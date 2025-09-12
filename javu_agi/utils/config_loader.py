import os
from dotenv import load_dotenv

_config_cache = None


def load_config():
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    try:
        load_dotenv()
        _config_cache = {
            "LLM_MODEL": os.getenv("LLM_MODEL", "gpt-4"),
            "MAX_MEMORY_TOKENS": int(os.getenv("MAX_MEMORY_TOKENS", 2048)),
            "DEBUG_MODE": os.getenv("DEBUG_MODE", "false").lower() == "true",
        }
    except Exception as e:
        _config_cache = {
            "LLM_MODEL": "gpt-4",
            "MAX_MEMORY_TOKENS": 2048,
            "DEBUG_MODE": False,
        }
    return _config_cache
