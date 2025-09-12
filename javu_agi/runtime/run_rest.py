from fastapi import FastAPI, Request
from pydantic import BaseModel
from javu_agi.core_loop import run_user_loop

app = FastAPI()


class Input(BaseModel):
    user_id: str
    prompt: str


@app.post("/agi")
async def agi_run(input: Input):
    try:
        response = run_user_loop(input.user_id, input.prompt)
        return {"response": response}
    except Exception as e:
        return {"error": str(e)}
