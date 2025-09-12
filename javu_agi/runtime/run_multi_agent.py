from javu_agi.core_loop import run_core_loop


def main():
    print("🤖 MULTI-AGI COMM ACTIVE")
    agent_a, agent_b = "agent_A", "agent_B"
    msg = input("🧠 Input to Agent A: ")
    for _ in range(5):
        ra = run_core_loop(agent_a, msg)["response"]
        print(f"\nAgent A → {ra}")
        rb = run_core_loop(agent_b, ra)["response"]
        print(f"Agent B → {rb}")
        msg = rb


if __name__ == "__main__":
    main()
