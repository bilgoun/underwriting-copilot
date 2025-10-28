from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from ..config import get_settings

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
LOAN_ASSISTANT_PROMPT_PATH = PROJECT_ROOT / "business_loans_mn.json"

LOAN_ASSISTANT_PROMPT_HEADER = (
    "Та Монгол Улсад үйл ажиллагаа явуулдаг арилжааны банкны зээлийн туслах. Клиентуудтай найрсаг, ойлгомжтой, "
    "хариуцлагатай харилцаж, зээл авах нөхцөл болон бүрдүүлэх бичиг баримтын талаар тайлбар өг. Зээл олголтод шийдвэр гаргах "
    "боломжгүй тул эцсийн шийдвэрийг зээлийн мэргэжилтэн гаргана гэдгийг онцолж, харилцагчийг дараагийн алхамд нь чиглүүл. "
    "Зээлдэгчийн асуултад хариулахдаа албан ёсны мэдээлэл, хууль эрх зүйн шаардлагууд болон анхааруулгыг зөв, товч, найрсаг байдлаар дамжуул."
    "\n\nДоорх зээлийн бүтээгдэхүүний JSON мэдээллийг ашиглан асуултад хариул."
)


def _load_loan_assistant_reference(path: Path) -> str:
    try:
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        logger.error("Loan assistant prompt data not found at %s", path)
        return ""
    except json.JSONDecodeError:
        logger.exception("Loan assistant prompt data is not valid JSON: %s", path)
        return ""
    return json.dumps(data, ensure_ascii=False, indent=2)


def _build_loan_assistant_system_prompt() -> str:
    reference = _load_loan_assistant_reference(LOAN_ASSISTANT_PROMPT_PATH)
    if not reference:
        return LOAN_ASSISTANT_PROMPT_HEADER
    return (
        f"{LOAN_ASSISTANT_PROMPT_HEADER}\n\n"
        f"Зээлийн бүтээгдэхүүний мэдлэгийн сан (JSON):\n{reference}"
    )

SYSTEM_PROMPT = (
    "Та банкны ахлах зээлийн шинжээч. Доорх JSON өгөгдлөөр шийдвэр гаргалтад туслах "
    "богино, тодорхой, хариуцлагатай кредит мемо (Markdown) бич. "
    "\n\nОрлогын мэдээлэл: Банкны хуулга байвал түүнээс, үгүй бол бусад эх сурвалжаас авч дүгнэлт гарга."
    "\n\nБарьцаа хөрөнгө: Машины хувьд ML API-н үнэлгээ + веб хайлтын түүхий үр дүнг ашигла. "
    "Үл хөдлөх хөрөнгийн хувьд веб хайлтын түүхий өгөгдлөөс үнэ дүгнээд үндэслэх."
    "\n\nВеб хайлтын түүхий үр дүнг задлан шинжилж, боломжит зах зээлийн үнийг тайлбарла."
    "\n\nСанамж: Манай сарын хүүгийн хүрээ 3%-4%. DTI, нийт өрийн үйлчилгээ/орлогын (DSR) харьцаа, LTV зэрэг үндсэн үзүүлэлтүүдийг тооцоолж, эрсдэлд тулгуурлан Accept / Review / Decline шийдвэр болон санал болгосон сарын хүүг мемо дотроо тодорхой бич."
)

LOAN_ASSISTANT_SYSTEM_PROMPT = _build_loan_assistant_system_prompt()


tracer = trace.get_tracer("app.pipeline.llm")


def _gemini_request(system_prompt: str, contents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Send a set of contents to the Gemini API and return the response."""
    settings = get_settings()
    api_key = (
        os.getenv("GEMINI_API_KEY")
        or settings.model_extra.get("GEMINI_API_KEY")  # type: ignore[attr-defined]
        or settings.llm_api_key
    )
    if not api_key:
        raise ValueError(
            "Gemini API key not found. Set GEMINI_API_KEY or LLM_API_KEY in your environment or .env file."
        )

    model_name = "gemini-2.5-pro-preview-05-06"
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    )
    headers = {"Content-Type": "application/json"}
    data = {"contents": contents, "systemInstruction": {"parts": [{"text": system_prompt}]}}

    with tracer.start_as_current_span(
        "llm.request",
        attributes={
            "llm.provider": "gemini",
            "llm.model": model_name,
            "http.method": "POST",
            "http.url": url,
            "llm.prompt.messages": len(contents),
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


def call_gemini_llm(system_prompt: str, user_prompt: str) -> Dict[str, Any]:
    """Send a single user prompt to the Gemini API and return the response."""
    contents = [{"role": "user", "parts": [{"text": user_prompt}]}]
    return _gemini_request(system_prompt, contents)


def call_gemini_chat(system_prompt: str, messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """Send a conversational history to the Gemini API and return the response."""
    if not messages:
        raise ValueError("Conversation must include at least one message.")

    contents: List[Dict[str, Any]] = []
    for message in messages:
        role = message.get("role")
        content = message.get("content") or message.get("text")
        if not content:
            continue
        gemini_role = "user" if role == "user" else "model"
        contents.append({"role": gemini_role, "parts": [{"text": str(content)}]})

    if not contents:
        raise ValueError("Conversation did not contain any usable messages.")

    return _gemini_request(system_prompt, contents)


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


def generate_loan_chat_reply(messages: List[Dict[str, str]]) -> Tuple[str, Dict[str, Any]]:
    settings = get_settings()
    if not messages or messages[-1].get("role") != "user":
        raise ValueError("Conversation must end with a user message.")
    with tracer.start_as_current_span("llm.loan_chat") as span:
        span.set_attribute("llm.conversation.turns", len(messages))
        gemini_response = call_gemini_chat(LOAN_ASSISTANT_SYSTEM_PROMPT, messages)
        reply = _extract_memo_text(gemini_response)
        reply = reply.rstrip()
        portal_url = str(settings.loan_application_url)
        link_line = (
            f"Та энэхүү холбоосоор хандан онлайнаар зээлийн өргөдлөө бүрдүүлээрэй: {portal_url}"
        )
        full_reply = f"{reply}\n\n{link_line}" if reply else link_line
        span.set_attribute("llm.reply.length", len(full_reply))
        return full_reply, {"raw_response": gemini_response}
