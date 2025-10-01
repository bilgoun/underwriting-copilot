from __future__ import annotations

import json
import os
from typing import Any, Dict, Tuple

import requests
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from ..config import get_settings

SYSTEM_PROMPT = (
    "Та банкны ахлах зээлийн шинжээч. Доорх JSON өгөгдлөөр шийдвэр гаргалтад туслах "
    "богино, тодорхой, хариуцлагатай кредит мемо (Markdown) бич. "
    "\n\nОрлогын мэдээлэл: Банкны хуулга байвал түүнээс, үгүй бол бусад эх сурвалжаас авч дүгнэлт гарга."
    "\n\nБарьцаа хөрөнгө: Машины хувьд ML API-н үнэлгээ + веб хайлтын түүхий үр дүнг ашигла. "
    "Үл хөдлөх хөрөнгийн хувьд веб хайлтын түүхий өгөгдлөөс үнэ дүгнээд үндэслэх."
    "\n\nВеб хайлтын түүхий үр дүнг задлан шинжилж, боломжит зах зээлийн үнийг тайлбарла."
    "\n\nСанамж: Манай сарын хүүгийн хүрээ 3%-4%. DTI, нийт өрийн үйлчилгээ/орлогын (DSR) харьцаа, LTV зэрэг үндсэн үзүүлэлтүүдийг тооцоолж, эрсдэлд тулгуурлан Accept / Review / Decline шийдвэр болон санал болгосон сарын хүүг мемо дотроо тодорхой бич."
)

tracer = trace.get_tracer("app.pipeline.llm")


def call_gemini_llm(system_prompt: str, user_prompt: str) -> Dict[str, Any]:
    """Send a prompt to the Gemini API and return the response."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "Gemini API key not found. Please set the GEMINI_API_KEY environment variable."
        )

    model_name = "gemini-2.5-pro-preview-05-06"
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    )
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": user_prompt}]}],
        "systemInstruction": {"parts": [{"text": system_prompt}]},
    }

    with tracer.start_as_current_span(
        "llm.request",
        attributes={
            "llm.provider": "gemini",
            "llm.model": model_name,
            "http.method": "POST",
            "http.url": url,
        },
    ) as span:
        response = requests.post(url, headers=headers, json=data, timeout=90)
        span.set_attribute("http.status_code", response.status_code)
        if response.status_code == 200:
            payload = response.json()
            span.set_attribute("llm.candidates", len(payload.get("candidates", []) or []))
            return payload
        error_message = response.text[:200]
        span.record_exception(RuntimeError(error_message))
        span.set_status(Status(StatusCode.ERROR, error_message))
        raise RuntimeError(
            f"Gemini API request failed with status code {response.status_code}: {response.text}"
        )


def _extract_memo_text(gemini_response: Dict[str, Any]) -> str:
    candidates = gemini_response.get("candidates") or []
    for candidate in candidates:
        content = candidate.get("content") or {}
        parts = content.get("parts") or []
        for part in parts:
            text = part.get("text")
            if text:
                return text
    raise RuntimeError("Gemini response did not contain any text content")


def generate_memo(features: Dict[str, Dict]) -> Tuple[str, Dict[str, Any]]:
    _ = get_settings()  # ensure settings loaded / future config use
    user_prompt = json.dumps(features, ensure_ascii=False)
    with tracer.start_as_current_span("llm.generate_memo") as span:
        span.set_attribute("llm.input.size_bytes", len(user_prompt.encode("utf-8")))
        gemini_response = call_gemini_llm(SYSTEM_PROMPT, user_prompt)
        memo = _extract_memo_text(gemini_response)
        meta = {"raw_response": gemini_response}
        span.set_attribute("llm.memo.length", len(memo))
        return memo, meta
