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

client = TestClient(app)
RECOG = Path(__file__).resolve().parent / "recog"

CASES = [
    ("recog-01-print-perfect-square.jpg", ("(x+y)", "x+y", "x²+y²", "x^2+y^2")),
    ("recog-06-hand-factor.jpg", ("因式分解", "xy", "-xy")),
    ("recog-12-print-radical.jpg", ("x-2", "根", "√")),
    ("recog-14-hand-rationalize.jpg", ("√3", "sqrt", "有理化")),
    ("recog-18-print-SSA.jpg", ("全等", "SSA", "SAS")),
    ("recog-20-hand-SAS.jpg", ("SAS", "夹角", "AB")),
    ("recog-21-hand-equilateral.jpg", ("a²", "a^2", "等边", "-ab-bc-ac")),
    ("recog-23-print-pythagoras.jpg", ("木棒", "7", "直角")),
]


def test_ingest_503_without_key(monkeypatch):
    monkeypatch.setattr("ingest._api_key", lambda: "")
    r = client.post("/ingest", files={"image": ("x.jpg", b"fake", "image/jpeg")})
    assert r.status_code == 503


def test_ingest_clamps_off_tree(monkeypatch):
    monkeypatch.setattr("ingest._api_key", lambda: "test-key")

    def fake_vl(raw, mime):
        return {
            "stem": "判断 (x+y)²=x²+y² 是否正确。",
            "options": None,
            "formula_tex": "(x+y)^2=x^2+y^2",
            "has_figure": False,
            "knowledge_id": "not.a.node",
        }

    monkeypatch.setattr("ingest._call_vl", fake_vl)
    r = client.post("/ingest", files={"image": ("x.jpg", b"fake", "image/jpeg")})
    assert r.status_code == 200
    body = r.json()
    assert body["knowledge_id"] in NODES
    assert body["knowledge_id"] == "poly.perfect-square"
    assert "(x+y)" in body["stem"]
    assert body["has_figure"] is False


@pytest.mark.skipif(not os.environ.get("MINIMAX_API_KEY"), reason="no MINIMAX_API_KEY")
@pytest.mark.parametrize("filename,needles", CASES)
def test_ingest_live_recog(filename, needles):
    path = RECOG / filename
    if not path.exists():
        pytest.skip(f"missing {filename}")
    r = client.post(
        "/ingest",
        files={"image": (filename, path.read_bytes(), "image/jpeg")},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["knowledge_id"] in NODES
    stem = body["stem"]
    assert any(n in stem for n in needles), (filename, stem, needles)
