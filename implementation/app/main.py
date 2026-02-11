from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query

from app.core.orchestrator import Orchestrator
from app.db.connection import close_pool, get_pool
from app.db.repositories import Repository
from app.schemas import (
    ChatRequest,
    ChatResponse,
    HighRiskConfirmRequest,
    HighRiskConfirmResponse,
    OutcomeUpdateRequest,
    ShellWriteRequest,
    SuccessPathWriteRequest,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await get_pool()
    yield
    await close_pool()


app = FastAPI(title='Continuity v1.1 API', version='1.1.0', lifespan=lifespan)
orc = Orchestrator()


async def get_conn():
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            yield conn


@app.get('/health')
async def health() -> dict:
    return {'ok': True, 'service': 'continuity-v1.1'}


@app.post('/chat', response_model=ChatResponse)
async def chat(req: ChatRequest, conn=Depends(get_conn)) -> ChatResponse:
    if not req.idempotency_key.strip():
        raise HTTPException(status_code=400, detail='idempotency_key is required')
    return await orc.handle_chat(conn, req)


@app.get('/user/{user_id}/state')
async def get_user_state(user_id: str, conn=Depends(get_conn)) -> dict:
    repo = Repository(conn)
    state = await repo.ensure_user_state(user_id)
    return state.model_dump()


@app.get('/user/{user_id}/objects')
async def get_objects(
    user_id: str,
    object_type: Optional[str] = Query(default=None, alias='type'),
    limit: int = Query(default=50, ge=1, le=200),
    conn=Depends(get_conn),
) -> dict:
    repo = Repository(conn)
    rows = await repo.list_memory_objects(user_id, object_type, limit)
    return {'items': rows, 'count': len(rows)}


@app.get('/user/{user_id}/objects/shell/latest')
async def get_latest_shell(user_id: str, conn=Depends(get_conn)) -> dict:
    repo = Repository(conn)
    row = await repo.get_latest_shell(user_id)
    if row is None:
        raise HTTPException(status_code=404, detail='shell not found')
    return row


@app.post('/user/{user_id}/objects/shell')
async def put_shell(user_id: str, req: ShellWriteRequest, conn=Depends(get_conn)) -> dict:
    repo = Repository(conn)
    await repo.ensure_user_state(user_id)
    row = await repo.put_shell_object(
        user_id=user_id,
        social_interface=req.social_interface,
        narratives=req.narratives,
        confidence=req.confidence,
        validity=req.validity,
        source=req.source,
    )
    return {'ok': True, 'item': row}


@app.post('/user/{user_id}/objects/success-path')
async def put_success_path(user_id: str, req: SuccessPathWriteRequest, conn=Depends(get_conn)) -> dict:
    repo = Repository(conn)
    await repo.ensure_user_state(user_id)
    missing_defs = [s for s in req.required_slots if s not in req.slot_definitions]
    if missing_defs:
        raise HTTPException(status_code=400, detail=f'missing slot_definitions for: {missing_defs}')

    row = await repo.put_success_path_object(
        user_id=user_id,
        name=req.name,
        intent=req.intent,
        required_slots=req.required_slots,
        slot_definitions=req.slot_definitions,
        procedure=req.procedure,
        success_criteria=req.success_criteria,
        confidence=req.confidence,
        validity=req.validity,
        tags=req.tags,
    )
    return {'ok': True, 'item': row}


@app.post('/decision/{decision_id}/outcome')
async def update_outcome(decision_id: int, user_id: str, req: OutcomeUpdateRequest, conn=Depends(get_conn)) -> dict:
    repo = Repository(conn)
    row = await repo.update_action_outcome(decision_id=decision_id, user_id=user_id, req=req)
    if row is None:
        raise HTTPException(status_code=404, detail='pending outcome not found for decision/user')
    return {'ok': True, 'item': row}


@app.post('/decision/{decision_id}/confirm', response_model=HighRiskConfirmResponse)
async def confirm_high_risk(decision_id: int, req: HighRiskConfirmRequest, conn=Depends(get_conn)) -> HighRiskConfirmResponse:
    repo = Repository(conn)
    confirmation = await repo.consume_high_risk_confirmation(decision_id=decision_id, user_id=req.user_id, token=req.confirm_token)
    if confirmation is None:
        raise HTTPException(status_code=400, detail='invalid_or_expired_confirm_token')

    updated_decision = await repo.mark_decision_confirmed(
        decision_id=decision_id,
        user_id=req.user_id,
        confirmation_id=confirmation['confirmation_id'],
    )
    if updated_decision is None:
        raise HTTPException(status_code=404, detail='decision_not_found_for_user')

    return HighRiskConfirmResponse(
        ok=True,
        decision_id=decision_id,
        user_id=req.user_id,
        confirmed=True,
        message='high risk decision confirmed',
    )
