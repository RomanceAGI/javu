from __future__ import annotations
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from javu_agi.eval.rct_runner import run_rct

API_TOKEN = "dev"


class Payload(BaseModel):
    queries: list[str]
    per_arm: int = 20
    seed: int = 7


app = FastAPI(title="eval-report")


def _auth(tok: str | None):
    if tok != f"Bearer {API_TOKEN}":
        raise HTTPException(401, "unauthorized")


@app.post("/rct")
def rct(x: Payload, authorization: str | None = Header(None)):
    _auth(authorization)
    return run_rct(x.queries, seed=x.seed, per_arm=x.per_arm)
