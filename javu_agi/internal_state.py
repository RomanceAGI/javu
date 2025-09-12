class InternalState:
    def __init__(self):
        self.state = {
            "energy": 100,
            "focus": 100,
            "emotion": "neutral",
            "confidence": 80,
            "last_error": None,
            "last_success": None,
        }

    def reflect(self, event: str, success: bool):
        if success:
            self.state["confidence"] += 5
            self.state["last_success"] = event
        else:
            self.state["confidence"] -= 10
            self.state["last_error"] = event
            self.state["focus"] -= 5
            self.state["emotion"] = "frustrated"

        self.state["confidence"] = max(0, min(100, self.state["confidence"]))
        self.state["focus"] = max(0, min(100, self.state["focus"]))

    def summarize(self) -> str:
        return f"""
⚙️ Internal State:
• Confidence: {self.state['confidence']}
• Focus: {self.state['focus']}
• Emotion: {self.state['emotion']}
• Last Success: {self.state['last_success']}
• Last Error: {self.state['last_error']}
""".strip()
