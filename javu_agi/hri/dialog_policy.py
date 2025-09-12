def safe_counter(user_text: str) -> str | None:
    t = (user_text or "").lower()
    MAL = ("bom", "peretasan", "kekerasan", "curi", "phishing")
    if any(k in t for k in MAL):
        return (
            "Saya tidak bisa membantu hal berbahaya. "
            "Apa tujuan aman & bermanfaat yang ingin dicapai?"
        )
    if len(t) < 5 or t.count("?") > 3:
        return (
            "Biar tepat, maksudmu apa? konteks, batasan, dan hasil apa yang diinginkan?"
        )
    return None
