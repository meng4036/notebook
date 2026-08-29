from __future__ import annotations

import re
from tagger import NODES

_INT = re.compile(r"(?<![\^])(?<![.\d])\d+(?![.\d])")


def _shift_int(n: int, k: int) -> int:
    if n == 0:
        return 1 + k
    sign = 1 if n > 0 else -1
    return sign * (abs(n) + k)



LETTER_MAPS = [
    {"x": "a", "y": "b"},
    {"x": "m", "y": "n"},
    {"x": "p", "y": "q"},
    {"a": "s", "b": "t"},
    {"m": "u", "n": "v"},
]

PARAPHRASES = [
    ("两个三角形", "一对三角形"),
    ("下列条件中", "下面各条件中"),
    ("是否正确", "对不对"),
    ("请判断", "判断"),
    ("△ABC", "△XYZ"),
    ("△DEF", "△MNP"),
    ("四边形对角线", "四边形 ABCD 对角线"),
    ("这个多边形", "该多边形"),
    ("已知四边形是平行四边形", "已知 ABCD 是平行四边形"),
    ("轴对称图形", "一个轴对称图形"),
    ("等腰三角形一腰", "等腰三角形的一腰"),
    ("发挥更稳定的人", "谁发挥更稳定"),
]


def mutate_stem(stem: str, k: int) -> str:
    i = 0

    def repl(m):
        nonlocal i
        i += 1
        n = int(m.group())
        return str(_shift_int(n, k + (i % 3)))

    numbered = _INT.sub(repl, stem)
    if numbered != stem:
        return numbered
    maps = LETTER_MAPS[(k - 1) % len(LETTER_MAPS)]
    out = stem
    for old, new in maps.items():
        out = re.sub(r"\b" + old + r"\b", new, out)
    if out != stem:
        return out
    if k - 1 < len(PARAPHRASES):
        a, b = PARAPHRASES[k - 1]
        if a in stem:
            return stem.replace(a, b, 1)
    return f"（变式{k}）" + stem


def _has(s: str, *keys: str) -> bool:
    t = s.lower()
    return any(k.lower() in t for k in keys)


def constraint_ok(original: str, variant: str, knowledge_id: str, error_constraint: str) -> bool:
    v = (variant or "").strip()
    o = (original or "").strip()
    if not v or v == o:
        return False
    c = error_constraint or ""
    kid = knowledge_id

    if kid == "poly.perfect-square":
        if _has(v, "平方差", "a²-b²", "a^2-b^2"):
            return False
        if ("±" in o or "正负" in c) and "±" in o and "±" not in v:
            return False
        return _has(v, "完全平方", "²", "^2")

    if kid == "poly.factor-def":
        return _has(v, "因式分解")

    if kid == "poly.common-factor":
        return _has(v, "因式分解", "提公因式")

    if kid == "poly.diff-of-squares":
        if _has(v, "展开成") and not _has(v, "因式分解"):
            return False
        return _has(v, "因式分解", "平方差", "能够被")

    if kid == "rad.abs":
        return _has(v, "√", "sqrt") and _has(v, "²", "^2", "绝对值", "|")

    if kid == "rad.domain":
        return _has(v, "√-") or _has(v, "被开方")

    if kid == "rad.rationalize":
        return _has(v, "√") and ("-" in v or "+" in v)

    if kid == "rad.like":
        return v.count("√") >= 2 or v.count("sqrt") >= 2

    if kid == "lin.mono":
        return _has(v, "一次函数") and (_has(v, "≤") or _has(v, "取值"))

    if kid == "lin.undetermined":
        return _has(v, "面积") and _has(v, "一次函数")

    if kid == "cong.ssa":
        if _has(v, "hl") or (_has(v, "直角三角形") and _has(v, "斜边")):
            return False
        return _has(v, "全等") and (_has(v, "对角", "ssa", "不能判定"))

    if kid == "cong.hl":
        return _has(v, "hl") and _has(v, "ssa", "对角", "两边")

    if kid == "cong.sas":
        return _has(v, "sas") and _has(v, "夹角", "∠", "全等")

    if kid == "tri.equilateral":
        if _has(v, "勾股", "直角"):
            return False
        return _has(v, "a²+b²+c²", "a^2+b^2+c^2", "等边", "形状")

    if kid == "tri.polygon":
        return _has(v, "外角") and _has(v, "多边形")

    if kid == "pyg.converse":
        return _has(v, "直角") and (_has(v, "木棒", "摆成", "最长"))

    if kid == "pyg.theorem":
        if _has(v, "逆定理", "是否直角", "木棒", "判断是不是直角"):
            return False
        return _has(v, "rt", "直角") and _has(v, "求")

    if kid == "para.judge":
        if _has(v, "矩形", "菱形"):
            return False
        return _has(v, "平行四边形")

    if kid == "rect.judge":
        return _has(v, "矩形") and _has(v, "菱形", "邻边")

    if kid == "sym.axis":
        if _has(v, "旋转"):
            return False
        return _has(v, "轴对称")

    if kid == "tri.isosceles":
        return _has(v, "等腰") and (_has(v, "分类") or _has(v, "顶角") or _has(v, "腰"))

    if kid == "stat.center":
        return _has(v, "众数") or _has(v, "中位数")

    if kid == "stat.variance":
        return _has(v, "稳定") or _has(v, "方差")

    return v != o


def generate(stem: str, knowledge_id: str, error_constraint: str, n: int = 3) -> list[dict]:
    if knowledge_id not in NODES:
        raise ValueError("knowledge_id not on tree")
    n = max(1, min(int(n or 3), 5))
    out: list[dict] = []
    seen = {stem.strip()}
    for k in range(1, 16):
        cand = mutate_stem(stem, k).strip()
        if cand in seen:
            continue
        if constraint_ok(stem, cand, knowledge_id, error_constraint):
            seen.add(cand)
            out.append({"stem": cand, "constraint_ok": True})
        if len(out) >= n:
            break
    return out
