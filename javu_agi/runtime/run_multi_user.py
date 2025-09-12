from javu_agi.core_loop import run_core_loop


def main():
    print("🤖 Multi-User AGI CLI\nGunakan `exit` untuk keluar kapan saja.\n")
    while True:
        user_id = input("👤 User ID: ")
        if user_id.strip().lower() in ["exit", "quit"]:
            break
        while True:
            prompt = input(f"{user_id} >> ")
            if prompt.strip().lower() in ["exit", "quit"]:
                break
            out = run_core_loop(user_id, prompt)
            print(f"\n🧠 JAVU ({user_id}): {out['response']}\n")


if __name__ == "__main__":
    main()
