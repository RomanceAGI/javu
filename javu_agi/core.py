from __future__ import annotations
import sys
import signal
import traceback
from dotenv import load_dotenv
import typer

load_dotenv()
app = typer.Typer(no_args_is_help=True, add_completion=False)


def _sigterm(*_):
    print("🛑 Stop signal received, shutting down...", file=sys.stderr)
    sys.exit(0)


signal.signal(signal.SIGINT, _sigterm)
signal.signal(signal.SIGTERM, _sigterm)


def run_interactive_loop():
    from javu_agi.graph import build_graph
    from javu_agi.initiator import get_initial_prompt, process_initial_response
    from javu_agi.identity import get_default_identity
    from javu_agi.goal_planner import generate_plan_from_goal
    from javu_agi.privacy import log_action
    from javu_agi.self_reflection import reflect_on_conversation
    from javu_agi.tool_executor import react_tool_chain, execute_tool

    print("✅ JAVU.AGI aktif — Digital Being operational.")
    graph = build_graph()
    memory = get_default_identity()

    initial_prompt = get_initial_prompt(memory)
    print(f"JAVU: {initial_prompt}")
    try:
        user_response = input("YOU: ")
    except EOFError:
        return
    print(process_initial_response(user_response, memory))

    history = []

    while True:
        try:
            user_input = input("YOU: ")
        except EOFError:
            break
        if user_input.lower() in ["exit", "quit"]:
            break

        log_action(f"[INPUT] {user_input}")
        history.append(f"User: {user_input}")

        if user_input.lower().startswith("goal:"):
            goal_text = user_input[5:].strip()
            plan = generate_plan_from_goal(goal_text)
            print("📌 Plan dari Goal:")
            print(plan)
            log_action(f"[GOAL] {goal_text} → {plan}")
            continue

        tool_chain = react_tool_chain(user_input)
        for tool in tool_chain:
            tool_result = execute_tool(tool, user_input)
            print(f"🔧 Tool {tool} → {tool_result}")
            log_action(f"[TOOL] {tool} → {tool_result}")

        try:
            result = graph.invoke(
                {"input": user_input, "messages": [], "agent": "", "response": ""}
            )
            response = result.get("response", "[No response]")
            print("JAVU.AGI:", response)
            history.append(f"JAVU: {response}")
        except Exception as e:
            print("❌ Error:", str(e))
            traceback.print_exc()
            continue

        if len(history) >= 6 and len(history) % 6 == 0:
            reflection = reflect_on_conversation(history[-6:])
            print("🪞 JAVU Reflection:", reflection)
            log_action(f"[REFLECTION] {reflection}")


@app.command("run")
def run(mode: str = typer.Argument("loop")):
    if mode == "loop":
        from .main_agi_loop import AGILoop

        AGILoop().run_forever()
    elif mode == "arena":
        from .run_arena import run_arena

        stats = run_arena(rounds=20)
        print(stats)
    elif mode == "eval":
        from .core_loop import run_core_loop

        result = run_core_loop("eval_user", "diagnostic run")
        print(result)
    elif mode == "api":
        from .api import serve

        serve()
    elif mode == "shell":
        run_interactive_loop()
    else:
        typer.echo(f"Unknown mode: {mode}")
        raise typer.Exit(2)


@app.command("health")
def health() -> None:
    try:
        __import__("javu_agi.world_model")
        __import__("javu_agi.memory")
        __import__("javu_agi.tool_executor")
        print("ok")
    except Exception as e:
        print(f"not ok: {e}", file=sys.stderr)
        raise typer.Exit(1)


cli = app

if __name__ == "__main__":
    app()
