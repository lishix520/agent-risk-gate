from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx

from app.config import settings


@dataclass(frozen=True)
class LLMResponse:
    ok: bool
    text: str
    provider: str
    error: Optional[str] = None


class LLMClient:
    def __init__(self) -> None:
        self.provider = settings.llm_provider
        self.timeout = settings.llm_timeout_seconds
        self.anthropic_key = settings.anthropic_api_key
        self.openai_key = settings.openai_api_key

    def _pick_provider(self) -> str:
        if self.provider in {'anthropic', 'openai'}:
            return self.provider
        if self.anthropic_key:
            return 'anthropic'
        if self.openai_key:
            return 'openai'
        return 'none'

    async def json_completion(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        provider = self._pick_provider()
        if provider == 'anthropic':
            return await self._anthropic(system_prompt, user_prompt)
        if provider == 'openai':
            return await self._openai(system_prompt, user_prompt)
        return LLMResponse(ok=False, text='', provider='none', error='no_provider_or_key')

    async def _anthropic(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        headers = {
            'x-api-key': self.anthropic_key,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json',
        }
        payload: Dict[str, Any] = {
            'model': settings.anthropic_model,
            'max_tokens': settings.llm_max_tokens,
            'system': system_prompt,
            'messages': [{'role': 'user', 'content': user_prompt}],
            'temperature': 0,
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.post('https://api.anthropic.com/v1/messages', headers=headers, json=payload)
                r.raise_for_status()
                data = r.json()
            blocks = data.get('content') or []
            text = ''
            for b in blocks:
                if b.get('type') == 'text':
                    text += b.get('text', '')
            return LLMResponse(ok=bool(text.strip()), text=text, provider='anthropic')
        except Exception as e:  # noqa: BLE001
            return LLMResponse(ok=False, text='', provider='anthropic', error=str(e))

    async def _openai(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        headers = {
            'Authorization': f'Bearer {self.openai_key}',
            'content-type': 'application/json',
        }
        payload: Dict[str, Any] = {
            'model': settings.openai_model,
            'temperature': 0,
            'response_format': {'type': 'json_object'},
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            'max_tokens': settings.llm_max_tokens,
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.post('https://api.openai.com/v1/chat/completions', headers=headers, json=payload)
                r.raise_for_status()
                data = r.json()
            text = data['choices'][0]['message']['content']
            return LLMResponse(ok=bool(text.strip()), text=text, provider='openai')
        except Exception as e:  # noqa: BLE001
            return LLMResponse(ok=False, text='', provider='openai', error=str(e))


def extract_json_block(raw_text: str) -> Optional[Dict[str, Any]]:
    if not raw_text.strip():
        return None
    s = raw_text.strip()
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass

    start = s.find('{')
    end = s.rfind('}')
    if start >= 0 and end > start:
        snippet = s[start:end + 1]
        try:
            return json.loads(snippet)
        except json.JSONDecodeError:
            return None
    return None
