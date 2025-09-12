from fastapi import FastAPI, Request
from pydantic import BaseModel
from javu_agi.core_loop import run_user_loop
from runtime.user_manager import validate_user
from runtime.log_server import log_request

app = FastAPI()


class Input(BaseModel):
    user_id: str
    prompt: str


@app.post("/agi")
async def agi_multi_user(input: Input):
    try:
        if not validate_user(input.user_id):
            return {"error": "Unauthorized or invalid user_id."}

        log_request(input.user_id, input.prompt)
        response = run_user_loop(input.user_id, input.prompt)
        return {"response": response}
    except Exception as e:
        return {"error": f"Runtime failure: {str(e)}"}
