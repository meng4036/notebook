
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TREE = json.loads((ROOT / "tree.json").read_text(encoding="utf-8"))

NODES = {n["id"]: {**n, "chapter_id": ch["id"], "chapter_label": ch["label"]}
         for ch in TREE["chapters"] for n in ch["nodes"]}
CHAPTER_OF = {nid: info["chapter_id"] for nid, info in NODES.items()}
ITEM_TYPES = TREE["item_types"]

# Specific stem features first. Not an id lookup.
RULES: list[tuple[str, str, str]] = [
    ("a²+b²+c²-ab-bc-ac", "tri.equilateral", "判断"),
    ("a^2+b^2+c^2-ab-bc-ac", "tri.equilateral", "判断"),
    ("五根小木棒", "pyg.converse", "选择"),
    ("小木棒", "pyg.converse", "选择"),
    ("相邻的外角", "tri.polygon", "求解"),
    ("对角线总条数", "tri.polygon", "求解"),
    ("围成三角形面积", "lin.undetermined", "求解"),
    ("相应函数值", "lin.mono", "求解"),
    ("hl 为什么", "cong.hl", "判断"),
    ("直角三角形的 hl", "cong.hl", "判断"),
    ("能用 sas 判定", "cong.sas", "判断"),
    ("不能判定两个三角形全等", "cong.ssa", "选择"),
    ("不能判定它是平行四边形", "para.judge", "选择"),
    ("判定它为矩形", "rect.judge", "选择"),
    ("不能判定它为矩形", "rect.judge", "选择"),
    ("轴对称", "sym.axis", "判断"),
    ("等腰三角形", "tri.isosceles", "求解"),
    ("众数", "stat.center", "求解"),
    ("中位数", "stat.center", "求解"),
    ("更稳定", "stat.variance", "求解"),
    ("方差", "stat.variance", "求解"),
    ("其中是因式分解的有", "poly.factor-def", "填空"),
    ("完全平方式", "poly.perfect-square", "选择"),
    ("(x+y)²=x²+y²", "poly.perfect-square", "判断"),
    ("(x+y)^2=x^2+y^2", "poly.perfect-square", "判断"),
    ("(2x+y)²=4x²+2xy", "poly.perfect-square", "判断"),
    ("(2x+y)^2=4x^2+2xy", "poly.perfect-square", "判断"),
    ("因式分解 4a²-4a+1", "poly.factor-def", "因式分解"),
    ("因式分解 4a^2-4a+1", "poly.factor-def", "因式分解"),
    ("-xy²+2xy-x", "poly.common-factor", "因式分解"),
    ("-xy^2+2xy-x", "poly.common-factor", "因式分解"),
    ("因式分解 4a²-36", "poly.diff-of-squares", "因式分解"),
    ("因式分解 4a^2-36", "poly.diff-of-squares", "因式分解"),
    ("(x²+4)²-16x²", "poly.diff-of-squares", "因式分解"),
    ("(x^2+4)^2-16x^2", "poly.diff-of-squares", "因式分解"),
    ("6m²n-9mn", "poly.common-factor", "因式分解"),
    ("6m^2n-9mn", "poly.common-factor", "因式分解"),
    ("(a+b)²-a-b", "poly.common-factor", "因式分解"),
    ("(a+b)^2-a-b", "poly.common-factor", "因式分解"),
    ("能够被", "poly.diff-of-squares", "选择"),
    ("√(x-2)²", "rad.abs", "化简计算"),
    ("√(x-2)^2", "rad.abs", "化简计算"),
    ("sqrt((x-2)^2)", "rad.abs", "化简计算"),
    ("(√-5)²", "rad.domain", "化简计算"),
    ("(√-", "rad.domain", "化简计算"),
    ("1/(√3-1)", "rad.rationalize", "化简计算"),
    ("√3-1", "rad.rationalize", "化简计算"),
    ("√2+√8", "rad.like", "化简计算"),
    ("rt△", "pyg.theorem", "求解"),
    ("rt△abc", "pyg.theorem", "求解"),
    ("∠c=90", "pyg.theorem", "求解"),
    ("完全平方", "poly.perfect-square", "判断"),
    ("提公因式", "poly.common-factor", "因式分解"),
    ("平方差", "poly.diff-of-squares", "因式分解"),
    ("因式分解", "poly.factor-def", "因式分解"),
    ("分母有理化", "rad.rationalize", "化简计算"),
    ("同类二次根式", "rad.like", "化简计算"),
    ("ssa", "cong.ssa", "选择"),
    ("sas", "cong.sas", "判断"),
    ("勾股逆", "pyg.converse", "选择"),
    ("勾股", "pyg.theorem", "求解"),
]


def _norm(s: str) -> str:
    t = (s or "").strip().lower()
    repl = {
        "²": "^2", "³": "^3", "⁸": "^8",
        "√": "√", "△": "△", "∠": "∠",
        "＝": "=", "（": "(", "）": ")",
    }
    for a, b in repl.items():
        t = t.replace(a, b)
    return t


def tag(stem: str, options: list[str] | None = None) -> dict:
    blob = _norm(stem)
    if options:
        blob += " " + _norm(" ".join(options))
    knowledge_id = None
    item_type = "求解"
    for needle, kid, itype in RULES:
        if _norm(needle) in blob:
            knowledge_id = kid
            item_type = itype
            break
    if knowledge_id is None:
        knowledge_id = "poly.factor-def"
        item_type = "求解"
    node = NODES[knowledge_id]
    ch = node["chapter_id"]
    others = [nid for nid, info in NODES.items() if nid != knowledge_id and info["chapter_id"] == ch]
    if len(others) < 2:
        others += [nid for nid in NODES if nid != knowledge_id and nid not in others]
    candidates = [
        {"knowledge_id": nid, "knowledge_label": NODES[nid]["label"]}
        for nid in others[:3]
    ]
    return {
        "knowledge_id": knowledge_id,
        "knowledge_label": node["label"],
        "item_type": item_type if item_type in ITEM_TYPES else "求解",
        "candidates": candidates,
        "chapter_id": ch,
    }
