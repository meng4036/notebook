from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import app
from tagger import NODES

pytestmark = pytest.mark.skipif(
    not (os.environ.get("DASHSCOPE_API_KEY") or "").strip(),
    reason="DASHSCOPE_API_KEY not set",
)

RECOG = Path(__file__).resolve().parent / "recog"
client = TestClient(app)

# Gold knowledge (same-chapter OK; tests only require tree membership):
# 01 poly.perfect-square, 06 poly.common-factor, 12 rad.abs, 14 rad.rationalize,
# 18 cong.ssa, 20 cong.sas, 21 tri.equilateral, 23 pyg.converse
CASES: list[tuple[str, tuple[str, ...]]] = [
    ("recog-01-print-perfect-square.jpg", ("(x+y)", "x+y")),
    ("recog-06-hand-factor.jpg", ("因式分解", "xy")),
    ("recog-12-print-radical.jpg", ("x-2", "根")),
    ("recog-14-hand-rationalize.jpg", ("√3", "sqrt")),
    ("recog-18-print-SSA.jpg", ("全等",)),
    ("recog-20-hand-SAS.jpg", ("SAS", "夹角", "AB")),
    ("recog-21-hand-equilateral.jpg", ("a²", "a^2", "等边")),
    ("recog-23-print-pythagoras.jpg", ("木棒", "7")),
]


def _needles_ok(stem: str, needles: tuple[str, ...]) -> bool:
    return any(n in stem for n in needles)


@pytest.mark.parametrize("filename,needles", CASES)
def test_ingest_recog_photo(filename: str, needles: tuple[str, ...]):
    path = RECOG / filename
    if not path.is_file():
        pytest.skip(f"missing {path}")
    with path.open("rb") as f:
        r = client.post("/ingest", files={"image": (filename, f, "image/jpeg")})
    assert r.status_code == 200, (filename, r.status_code, r.text)
    body = r.json()
    kid = body["knowledge_id"]
    assert kid in NODES, (filename, kid)
    stem = body.get("stem") or ""
    assert _needles_ok(stem, needles), (filename, stem, needles)
