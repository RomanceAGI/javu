from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional


class ApproveBody(BaseModel):
    note: Optional[str] = ""


class RejectBody(BaseModel):
    note: Optional[str] = ""


def build_router(oversight_queue) -> APIRouter:
    """
    oversight_queue: instance dengan API submit/list_pending/approve/reject/get
    """
    r = APIRouter(prefix="/oversight", tags=["oversight"])

    @r.get("/pending")
    def pending():
        try:
            return {"items": oversight_queue.list_pending()}
        except Exception as e:
            raise HTTPException(500, str(e))

    @r.get("/item/{rid}")
    def get_item(rid: str):
        it = oversight_queue.get(rid)
        if not it:
            raise HTTPException(404, "not found")
        return it

    @r.post("/approve/{rid}")
    def approve(rid: str, body: ApproveBody):
        ok = oversight_queue.approve(rid, body.note or "")
        if not ok:
            raise HTTPException(404, "not found")
        return {"ok": True}

    @r.post("/reject/{rid}")
    def reject(rid: str, body: RejectBody):
        ok = oversight_queue.reject(rid, body.note or "")
        if not ok:
            raise HTTPException(404, "not found")
        return {"ok": True}

    return r
