from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import app
from tagger import CHAPTER_OF, NODES

GOLD = json.loads((ROOT / "eval" / "gold_v0.2.json").read_text(encoding="utf-8"))
client = TestClient(app)


def test_tag_on_tree_and_same_chapter():
    misses = []
    print("\n# tag summary")
    print("id gold pred gold_ch pred_ch chapter_ok")
    for g in GOLD:
        r = client.post("/tag", json={"stem": g["stem"], "options": g.get("options")})
        assert r.status_code == 200, g["id"]
        body = r.json()
        pred = body["knowledge_id"]
        assert pred in NODES, (g["id"], pred)
        gold_ch = CHAPTER_OF[g["knowledge_id"]]
        pred_ch = CHAPTER_OF[pred]
        ok = gold_ch == pred_ch
        print(g["id"], g["knowledge_id"], pred, gold_ch, pred_ch, ok)
        if not ok:
            misses.append((g["id"], g["knowledge_id"], pred))
    assert not misses, misses


def test_variants_pass_constraints():
    print("\n# variants summary")
    for g in GOLD:
        r = client.post(
            "/variants",
            json={
                "stem": g["stem"],
                "knowledge_id": g["knowledge_id"],
                "error_constraint": g["error_constraint"],
                "n": 3,
            },
        )
        assert r.status_code == 200, g["id"]
        variants = r.json()["variants"]
        print(g["id"], len(variants))
        assert 2 <= len(variants) <= 3, (g["id"], len(variants), variants)
        for v in variants:
            assert v["constraint_ok"] is True
            assert v["stem"].strip() != g["stem"].strip()
        if g["id"] == "24":
            for v in variants:
                s = v["stem"]
                assert "逆定理" not in s
                assert "木棒" not in s
                assert "是否直角" not in s
        if g["id"] == "08":
            for v in variants:
                assert "因式分解" in v["stem"]
                assert "展开" not in v["stem"]
        if g["id"] == "18":
            for v in variants:
                assert "HL" not in v["stem"] and "hl" not in v["stem"].lower()
                assert "直角三角形" not in v["stem"]
