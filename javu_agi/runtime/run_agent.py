from javu_agi.core_loop import run_core_loop


def main():
    user_id = input("User ID: ")
    print("🧠 AGI CLI Active. Type 'exit' to quit.\n")
    while True:
        prompt = input(">> ")
        if prompt.lower() in ("exit", "quit"):
            break
        out = run_core_loop(user_id, prompt)
        print(f"\n🤖 JAVU: {out['response']}\n")


if __name__ == "__main__":
    main()
