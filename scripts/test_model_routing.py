import os
from javu_agi.llm import call_llm
from javu_agi.llm_router import get_route
from javu_agi.config import LLM_POLICY
from javu_agi.utils.logger import log_user

# Optional image test (jika kamu sudah tambahkan media_router & tool_image_gen)
IMAGE_TEST = True
try:
    from javu_agi.media_router import generate_image
except Exception:
    IMAGE_TEST = False

def try_call(task_type: str, prompt: str, modalities: set | None = None, max_tokens: int = 512):
    route = get_route(task_type=task_type, modalities=modalities, need_ctx=max_tokens)
    print(f"\n=== TASK: {task_type} | modalities={modalities} | need_ctx={max_tokens}")
    print(f"→ Router picked model: {route}")
    out = call_llm(prompt, task_type=task_type, modalities=modalities, max_tokens=max_tokens)
    print("→ Output (first 240 chars):", (out or "")[:240].replace("\n", " "))
    log_user("router_test", f"[{task_type}] model={route} out={out[:120]}")
    return route

def main():
    print("=== ROUTER POLICY ===")
    for k,v in LLM_POLICY["route_by_task"].items():
        print(f"- {k:10s} -> {v}")
    print("Fallback order:", LLM_POLICY["fallback_order"])

    used = []

    # 1) Deep reasoning → target gpt-5
    used.append(try_call("reason",
        "Jelaskan singkat perbedaan fundamental antara relativitas umum dan mekanika kuantum, 3 poin."))

    # 2) Planning → target gpt-5
    used.append(try_call("plan",
        "Buat rencana 7 langkah untuk eksperimen penemuan material superkonduktor suhu kamar."))

    # 3) Codegen/tooling → target gpt-4o (atau 5-mini jika kamu set)
    used.append(try_call("code",
        "Tulis HTML satu file yang menampilkan tulisan 'Hello AGI' besar di tengah layar dengan CSS sederhana."))

    # 4) Web/IO ringan → target gpt-5-mini
    used.append(try_call("web",
        "Ringkas dalam 2 kalimat: mengapa eksplorasi ruang penting bagi peradaban manusia."))

    # 5) Action/short → target gpt-5-mini
    used.append(try_call("action",
        "Buat checklist 5 item untuk memulai eksperimen sains di rumah."))

    # 6) Fast (opsional) → target gpt-5-nano (jika route_by_task punya 'fast')
    if "fast" in LLM_POLICY["route_by_task"]:
        used.append(try_call("fast",
            "Balas singkat: 'ok' saja.", max_tokens=16))
    else:
        print("\n[INFO] Task type 'fast' belum di-mapping. Lewati tes nano.")

    # 7) Vision modalities flag (kalau ada tugas yang butuh vision, sekadar mengetes capability flag)
    used.append(try_call("analyze",
        "Bayangkan kamu melihat diagram sirkuit sederhana. Sebutkan 3 risiko umum pada desain sirkuit pemula.",
        modalities={"vision"}))

    # 8) Image generation (opsional, kalau IMAGE_TEST True)
    if IMAGE_TEST:
        try:
            os.makedirs("artifacts", exist_ok=True)
            img = generate_image("ikon robot futuristik minimalis, latar putih, vektor, high contrast", size="512x512")
            out_path = "artifacts/router_test_image.png"
            with open(out_path, "wb") as f:
                f.write(img)
            print(f"\n[IMAGE] OK → saved to {out_path}")
        except Exception as e:
            print(f"\n[IMAGE] FAILED:", e)
    else:
        print("\n[IMAGE] Skip (media_router tidak tersedia).")

    # Summary
    print("\n=== SUMMARY MODEL USED (router picks) ===")
    for m in used:
        if m: print("-", m)

if __name__ == "__main__":
    main()
