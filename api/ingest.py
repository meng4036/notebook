from __future__ import annotations

import base64
import json
import os
import re

from tagger import NODES, TREE, tag

DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL = "qwen-vl-max"


class MissingApiKeyError(RuntimeError):
    """Raised when DASHSCOPE_API_KEY is missing."""


def _knowledge_catalog() -> str:
    lines: list[str] = []
    for ch in TREE["chapters"]:
        for n in ch["nodes"]:
            lines.append(f"- {n['id']}: {n['label']} （{ch['label']}）")
    return "\n".join(lines)


def _strip_fences(text: str) -> str:
    t = (text or "").strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", t)
    if m:
        return m.group(1).strip()
    return t


def _parse_json(text: str) -> dict:
    t = _strip_fences(text)
    try:
        data = json.loads(t)
    except json.JSONDecodeError:
        start, end = t.find("{"), t.rfind("}")
        if start < 0 or end <= start:
            raise
        data = json.loads(t[start : end + 1])
    if not isinstance(data, dict):
        raise ValueError("ingest model JSON is not an object")
    return data


def _prompt() -> str:
    return (
        "你是初中数学错题识别器。只提取题目本身，不要解题、不要给答案、不要批改。\n"
        "若是手写作业，只抽出印刷或手写的【题目】；忽略学生的典型错误演算、草稿、对错标记。\n"
        "只输出一个 JSON 对象，不要 markdown 围栏，不要其它文字。字段：\n"
        '- "stem": 题干字符串\n'
        '- "options": 选项字符串列表，没有选项则为 null\n'
        '- "formula_tex": 题中主要公式的 TeX，没有则为 null\n'
        '- "has_figure": 是否有几何图/示意图，布尔\n'
        '- "knowledge_id": 必须从下列冻结知识点 id 中选一个\n\n'
        "知识点枚举：\n"
        f"{_knowledge_catalog()}\n"
    )


def ingest_image(image_bytes: bytes, mime: str = "image/jpeg") -> dict:
    api_key = (os.environ.get("DASHSCOPE_API_KEY") or "").strip()
    if not api_key:
        raise MissingApiKeyError("DASHSCOPE_API_KEY is not set")

    model = (os.environ.get("QWEN_VL_MODEL") or DEFAULT_MODEL).strip() or DEFAULT_MODEL
    if not mime or not mime.startswith("image/"):
        mime = "image/jpeg"

    from openai import OpenAI

    data_url = f"data:{mime};base64,{base64.b64encode(image_bytes).decode('ascii')}"
    client = OpenAI(api_key=api_key, base_url=DASHSCOPE_BASE_URL)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": data_url}},
                    {"type": "text", "text": _prompt()},
                ],
            }
        ],
        temperature=0,
    )
    raw = (resp.choices[0].message.content or "") if resp.choices else ""
    data = _parse_json(raw)

    stem = data.get("stem") if isinstance(data.get("stem"), str) else ""
    options = data.get("options")
    if not isinstance(options, list):
        options = None
    else:
        options = [str(x) for x in options]
    formula_tex = data.get("formula_tex")
    if formula_tex is not None and not isinstance(formula_tex, str):
        formula_tex = str(formula_tex)
    has_figure = bool(data.get("has_figure"))
    knowledge_id = data.get("knowledge_id")
    if not isinstance(knowledge_id, str) or knowledge_id not in NODES:
        knowledge_id = tag(stem, options)["knowledge_id"]

    return {
        "stem": stem,
        "options": options,
        "formula_tex": formula_tex,
        "has_figure": has_figure,
        "knowledge_id": knowledge_id,
    }
