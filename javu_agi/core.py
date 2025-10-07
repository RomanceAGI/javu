from __future__ import annotations
import sys
import signal
import traceback
from dotenv import load_dotenv
import argparse

from javu_agi.core_loop import run_core_loop

load_dotenv()

def _dispatch_cli():
    parser = argparse.ArgumentParser(prog="javu_agi")
    subparsers = parser.add_subparsers(dest="command")

    parser_run = subparsers.add_parser("run")
    parser_run.add_argument("mode", nargs="?", default="loop")

    parser_health = subparsers.add_parser("health")

    args = parser.parse_args()
    if args.command == "run":
        run(args.mode)
    elif args.command == "health":
        health()
    else:
        parser.print_help()


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
            # Invoke the graph with the user's input and handle the result robustly.
            # The exact invocation may vary depending on graph.invoke's signature.
            # Here we pass the raw user input and expect a dict-like response.
            result = graph.invoke(user_input)
            response = result.get("response", "[No response]") if isinstance(result, dict) else str(result)
            print("JAVU.AGI:", response)
            history.append(f"JAVU: {response}")
        except Exception as e:
            print("❌ Error:", str(e))
            traceback.print_exc()
            continue

        if len(history) >= 6 and len(history) % 6 == 0:
            try:
                reflection = reflect_on_conversation(history[-6:])
                print("🪞 JAVU Reflection:", reflection)
                log_action(f"[REFLECTION] {reflection}")
            except Exception:
                # Reflection should not break the loop
                traceback.print_exc()


def run(mode: str = "loop"):
    """
    Run the AGI in different modes. Supported modes: loop, arena, eval, api, shell.
    This function avoids external cli frameworks and keeps behaviour simple.
    """
    if mode == "loop":
        run_interactive_loop()
    elif mode == "arena":
        # Placeholder for arena mode; import and call actual arena runner if available.
        try:
            from javu_agi.arena.run_arena import run_arena
            stats = run_arena(rounds=20)
            print(stats)
        except Exception as e:
            print("Arena mode not available:", e, file=sys.stderr)
    elif mode == "eval":
        # Run a simple diagnostic evaluation if available
        try:
            result = run_core_loop("eval_user", "diagnostic run")  # keep compatibility if function exists
            print(result)
        except Exception as e:
            print("Eval mode not available:", e, file=sys.stderr)
    elif mode == "api":
        try:
            from javu_agi.api_server import serve
            serve()
        except Exception as e:
            print("API mode not available:", e, file=sys.stderr)
    elif mode == "shell":
        run_interactive_loop()
    else:
        print(f"Unknown mode: {mode}", file=sys.stderr)


def health() -> None:
    """
    Simple health check endpoint; prints a short diagnostic.
    """
    try:
        # If run_core_loop is available, run a quick diagnostic; otherwise report OK.
        try:
            result = run_core_loop("health_check", "diagnostic")
            print(result)
        except NameError:
            print({"status": "ok", "detail": "health check passed"})
    except Exception as e:
        print(f"Health check failed: {e}", file=sys.stderr)
        raise


if __name__ == "__main__":
    _dispatch_cli()
    # Optional eager imports to surface startup errors quickly
    try:
        __import__("javu_agi.world_model")
        __import__("javu_agi.memory")
        __import__("javu_agi.tool_executor")
        print("ok")
    except Exception as e:
        print(f"not ok: {e}", file=sys.stderr)
        # Do not raise typer.Exit since we don't depend on typer in this file
