from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ingest import MissingApiKeyError, IngestError, ingest_image
from tagger import TREE, NODES, tag
from variants import generate

ROOT = Path(__file__).resolve().parent
GOLD = json.loads((ROOT / "eval" / "gold_v0.2.json").read_text(encoding="utf-8"))

app = FastAPI(title="cuoti-ben P0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class TagIn(BaseModel):
    stem: str
    options: list[str] | None = None
    formula_tex: str | None = None


class VariantsIn(BaseModel):
    stem: str
    knowledge_id: str
    error_constraint: str
    n: int | None = Field(default=3)


@app.get("/tree")
def get_tree():
    return TREE


@app.get("/gold")
def get_gold():
    return [
        {
            "id": g["id"],
            "stem": g["stem"],
            "options": g.get("options"),
            "knowledge_id": g["knowledge_id"],
            "knowledge_label": NODES[g["knowledge_id"]]["label"],
            "item_type": g["item_type"],
            "error_constraint": g["error_constraint"],
        }
        for g in GOLD
    ]


@app.post("/tag")
def post_tag(body: TagIn):
    result = tag(body.stem, body.options)
    if result["knowledge_id"] not in NODES:
        raise HTTPException(400, "knowledge_id not on tree")
    return {
        "knowledge_id": result["knowledge_id"],
        "knowledge_label": result["knowledge_label"],
        "item_type": result["item_type"],
        "candidates": result["candidates"],
    }


@app.post("/variants")
def post_variants(body: VariantsIn):
    if body.knowledge_id not in NODES:
        raise HTTPException(400, "knowledge_id not on tree")
    variants = generate(body.stem, body.knowledge_id, body.error_constraint, body.n or 3)
    return {"variants": variants}


@app.post("/ingest")
async def post_ingest(image: UploadFile = File(...)):
    try:
        raw = await image.read()
        mime = image.content_type or "image/jpeg"
        result = ingest_image(raw, mime)
    except MissingApiKeyError as e:
        raise HTTPException(503, str(e)) from e
    except IngestError as e:
        raise HTTPException(400, str(e)) from e
    if result["knowledge_id"] not in NODES:
        raise HTTPException(400, "knowledge_id not on tree")
    return {
        "stem": result["stem"],
        "options": result["options"],
        "formula_tex": result["formula_tex"],
        "has_figure": result["has_figure"],
        "knowledge_id": result["knowledge_id"],
    }
