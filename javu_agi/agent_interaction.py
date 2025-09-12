from javu_agi.llm import call_llm
from javu_agi.utils.logger import log


def talk_to_agent(agent_memory: str, message: str):
    prompt = f"Memory:\n{agent_memory}\n\nIncoming message: {message}\nHow should the agent respond?"
    response = call_llm(prompt, task_type="reason")
    log(f"[AGENT-TO-AGENT] {response}")
    return response
