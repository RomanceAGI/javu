from javu_agi.llm import call_llm


def generate_invention(topic):
    prompt = f"Berikan ide penemuan baru yang revolusioner di bidang {topic}"
    return call_llm(prompt)
