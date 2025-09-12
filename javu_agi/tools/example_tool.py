def summarize(payload):
    text = payload.get("text", "")
    n = payload.get("max_sentences", 2)
    sents = [
        s.strip()
        for s in text.replace("?", ".").replace("!','.").split(".")
        if s.strip()
    ]
    return {"summary": ". ".join(sents[:n])}
