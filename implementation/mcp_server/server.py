from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import httpx
from mcp.server.fastmcp import FastMCP


APP_NAME = 'continuity-mcp-adapter'
API_BASE_URL = os.getenv('CONTINUITY_API_BASE_URL', 'http://127.0.0.1:8000').rstrip('/')
TIMEOUT_SECONDS = float(os.getenv('CONTINUITY_MCP_HTTP_TIMEOUT', '20'))

mcp = FastMCP(APP_NAME)


class ContinuityAPIError(RuntimeError):
    pass


async def _api_request(method: str, path: str, *, params: Optional[Dict[str, Any]] = None, json_body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    url = f'{API_BASE_URL}{path}'
    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
        response = await client.request(method=method, url=url, params=params, json=json_body)

    if response.status_code >= 400:
        detail: Any
        try:
            detail = response.json()
        except Exception:
            detail = response.text
        raise ContinuityAPIError(f'{method} {path} failed ({response.status_code}): {detail}')

    data = response.json()
    if isinstance(data, dict):
        return data
    return {'data': data}


@mcp.tool()
async def continuity_health() -> Dict[str, Any]:
    """Check Continuity API connectivity and service health."""
    return await _api_request('GET', '/health')


@mcp.tool()
async def continuity_chat(user_id: str, message: str, idempotency_key: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """Main entry: execute continuity runtime via /chat."""
    payload: Dict[str, Any] = {
        'user_id': user_id,
        'message': message,
        'idempotency_key': idempotency_key,
    }
    if session_id is not None:
        payload['session_id'] = session_id
    return await _api_request('POST', '/chat', json_body=payload)


@mcp.tool()
async def continuity_confirm_decision(decision_id: int, user_id: str, confirm_token: str) -> Dict[str, Any]:
    """Confirm high-risk decision using issued confirm token."""
    payload = {
        'user_id': user_id,
        'confirm_token': confirm_token,
    }
    return await _api_request('POST', f'/decision/{decision_id}/confirm', json_body=payload)


@mcp.tool()
async def continuity_report_outcome(
    decision_id: int,
    user_id: str,
    actual_impact_vector: Dict[str, float],
    actual_cost: float,
    continuity_failure: bool = False,
    failure_type: Optional[str] = None,
    user_visible_cost: Optional[str] = None,
    preventable: Optional[bool] = None,
) -> Dict[str, Any]:
    """Write outcome feedback for a decision and close the loop."""
    payload: Dict[str, Any] = {
        'actual_impact_vector': actual_impact_vector,
        'actual_cost': actual_cost,
        'continuity_failure': continuity_failure,
        'failure_type': failure_type,
        'user_visible_cost': user_visible_cost,
        'preventable': preventable,
    }
    return await _api_request('POST', f'/decision/{decision_id}/outcome', params={'user_id': user_id}, json_body=payload)


@mcp.tool()
async def continuity_get_state(user_id: str) -> Dict[str, Any]:
    """Fetch current user resource state."""
    return await _api_request('GET', f'/user/{user_id}/state')


@mcp.tool()
async def continuity_list_objects(user_id: str, object_type: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    """List stored shell/success_path objects."""
    params: Dict[str, Any] = {'limit': limit}
    if object_type:
        params['type'] = object_type
    return await _api_request('GET', f'/user/{user_id}/objects', params=params)


@mcp.tool()
async def continuity_get_latest_shell(user_id: str) -> Dict[str, Any]:
    """Get latest shell object for a user."""
    return await _api_request('GET', f'/user/{user_id}/objects/shell/latest')


@mcp.tool()
async def continuity_put_shell(
    user_id: str,
    social_interface: Dict[str, Any],
    narratives: Dict[str, Any],
    confidence: str = 'high',
    validity: str = 'long',
    source: str = 'user',
) -> Dict[str, Any]:
    """Overwrite-style shell write."""
    payload = {
        'social_interface': social_interface,
        'narratives': narratives,
        'confidence': confidence,
        'validity': validity,
        'source': source,
    }
    return await _api_request('POST', f'/user/{user_id}/objects/shell', json_body=payload)


@mcp.tool()
async def continuity_put_success_path(
    user_id: str,
    name: str,
    intent: str,
    required_slots: List[str],
    slot_definitions: Dict[str, str],
    procedure: str,
    success_criteria: str,
    confidence: str = 'high',
    validity: str = 'long',
    tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Write reusable success path object."""
    payload = {
        'name': name,
        'intent': intent,
        'required_slots': required_slots,
        'slot_definitions': slot_definitions,
        'procedure': procedure,
        'success_criteria': success_criteria,
        'confidence': confidence,
        'validity': validity,
        'tags': tags or [],
    }
    return await _api_request('POST', f'/user/{user_id}/objects/success-path', json_body=payload)


def main() -> None:
    mcp.run()


if __name__ == '__main__':
    main()
