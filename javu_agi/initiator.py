from javu_agi.identity import update_user_identity, get_identity_prompt
from javu_agi.llm import call_llm


def get_initial_prompt(memory):
    user_known = memory["user"].get("name") is not None
    if not user_known:
        return "👋 Halo! Saya JAVU, AGI asisten pribadi kamu. Siapa nama kamu dan kamu fokus di bidang apa?"
    return get_identity_prompt(memory)


def process_initial_response(response, memory):
    system_prompt = """
Tugas kamu adalah mengekstrak nama orang dan industri dari kalimat berikut.

Jawaban harus format JSON:
{
  "name": "...",
  "industry": "..."
}

Jika tidak ketemu, isi null
"""
    prompt = f"Kalimat: {response}"
    result = call_llm(prompt=prompt, system_prompt=system_prompt, temperature=0.2)

    try:
        import json
        parsed = json.loads(result)
        name = parsed.get("name")
        industry = parsed.get("industry")
        update_user_identity(memory, name=name, industry=industry)
        return f"[✅ Identity captured] Nama: {name}, Industri: {industry}"
    except Exception:
        # If JSON parsing or updating identity fails, fall back to an error message
        return "[⚠️ Gagal memproses identitas awal]"
