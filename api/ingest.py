from __future__ import annotations

import base64
import json
import os
import re
from pathlib import Path
from typing import Any

from openai import OpenAI

from tagger import NODES, tag

DEFAULT_BASE = "https://api.minimaxi.com/v1"
DEFAULT_MODEL = "MiniMax-M3"


class MissingApiKeyError(RuntimeError):
    pass


class IngestError(RuntimeError):
    pass


def _load_env_file() -> None:
    path = Path(__file__).resolve().parent / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        k, _, v = raw.partition("=")
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


_load_env_file()


def _api_key() -> str:
    return os.environ.get("MINIMAX_API_KEY", "").strip()


def _tree_lines() -> str:
    return "\n".join(
        f"- {nid}: {info['label']}" for nid, info in NODES.items()
    )


def _prompt() -> str:
    return (
        "你是初中数学错题录入助手。只从这张照片抽出题目本身，不要给答案，不要批改。\n"
        "手写卷上若有典型错解、演算过程，忽略它们，只保留题干。\n"
        "几何图形不要矢量化，有图就把 has_figure 设为 true。\n"
        "knowledge_id 必须从下面冻结树里选一个 id，禁止自造。\n\n"
        f"{_tree_lines()}\n\n"
        "只输出一段 JSON，不要 markdown 围栏，字段：\n"
        '{"stem":"题干字符串","options":null或字符串数组,"formula_tex":null或TeX,'
        '"has_figure":true或false,"knowledge_id":"树上的id"}'
    )


def _parse_json(text: str) -> dict[str, Any]:
    raw = (text or "").strip()
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.S)
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    start, end = raw.find("{"), raw.rfind("}")
    if start < 0 or end <= start:
        raise IngestError("vision did not return JSON")
    data = json.loads(raw[start : end + 1])
    if not isinstance(data, dict):
        raise IngestError("vision JSON is not an object")
    return data


def _call_vl(raw: bytes, mime: str) -> dict[str, Any]:
    key = _api_key()
    if not key:
        raise MissingApiKeyError("MINIMAX_API_KEY missing")
    model = os.environ.get("MINIMAX_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    base = os.environ.get("MINIMAX_BASE_URL", DEFAULT_BASE).strip() or DEFAULT_BASE
    b64 = base64.b64encode(raw).decode("ascii")
    media = mime if mime.startswith("image/") else "image/jpeg"
    client = OpenAI(api_key=key, base_url=base)
    resp = client.chat.completions.create(
        model=model,
        temperature=1,
        max_completion_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media};base64,{b64}",
                            "detail": "high",
                        },
                    },
                    {"type": "text", "text": _prompt()},
                ],
            }
        ],
        extra_body={"thinking": {"type": "disabled"}},
    )
    text = (resp.choices[0].message.content or "").strip()
    return _parse_json(text)


def ingest_image(raw: bytes, mime: str = "image/jpeg") -> dict[str, Any]:
    if not raw:
        raise IngestError("empty image")
    data = _call_vl(raw, mime)
    stem = str(data.get("stem") or "").strip()
    if not stem:
        raise IngestError("empty stem")
    options = data.get("options")
    if options is not None:
        if not isinstance(options, list):
            raise IngestError("options must be a list or null")
        options = [str(x) for x in options]
        if not options:
            options = None
    formula_tex = data.get("formula_tex")
    if formula_tex is not None:
        formula_tex = str(formula_tex).strip() or None
    has_figure = bool(data.get("has_figure"))
    kid = str(data.get("knowledge_id") or "").strip()
    if kid not in NODES:
        fallback = tag(stem, options)
        kid = fallback["knowledge_id"]
    if kid not in NODES:
        raise IngestError("knowledge_id not on tree")
    return {
        "stem": stem,
        "options": options,
        "formula_tex": formula_tex,
        "has_figure": has_figure,
        "knowledge_id": kid,
    }
