import os

POLICY_HARD = os.getenv("POLICY_HARD", "1") == "1"
CTX_LEARNER = os.getenv("CTX_LEARNER", "1") == "1"
SKILL_DAEMON_ENABLE = os.getenv("SKILL_DAEMON_ENABLE", "1") == "1"
SKILL_DAEMON_INTERVAL = int(os.getenv("SKILL_DAEMON_INTERVAL", "30"))
TOOL_TIMEOUT = int(os.getenv("TOOL_TIMEOUT", "8"))

PLANNER_LLM_URL = os.getenv("PLANNER_LLM_URL") or ""
PLANNER_LLM_KEY = os.getenv("PLANNER_LLM_KEY") or ""
