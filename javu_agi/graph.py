from langgraph.graph import StateGraph, END
from typing import TypedDict
from javu_agi.planner import plan_task
from javu_agi.universal_agent import handle_input
from javu_agi.tool_executor import execute_tool
from javu_agi.memory.memory import save_to_memory


class AgentState(TypedDict):
    input: str
    messages: list[str]
    agent: str
    response: str


def planner_node(state: AgentState):
    user_input = state["input"]
    role = plan_task(user_input)
    print(f"🧠 Planner → {role}")
    state["agent"] = role
    state["response"] = f"[Planner → {role}]"
    state["messages"].append(f"[Planner] input: {user_input} → role: {role}")
    return state


def agent_node(state: AgentState):
    new_state = handle_input(state)
    new_state["messages"].append("[Universal Agent] responded.")
    return new_state


def tool_node(state: AgentState):
    user_input = state["input"]
    result = execute_tool("search", user_input)
    state["response"] = result
    state["messages"].append(f"[Tool] {result}")
    return state


def memory_node(state: AgentState):
    save_to_memory(state)
    state["messages"].append("[Memory Saved]")
    return state


def build_graph():
    builder = StateGraph(AgentState)

    builder.add_node("planner", planner_node)
    builder.add_node("agent", agent_node)
    builder.add_node("tool", tool_node)
    builder.add_node("memory", memory_node)

    builder.set_entry_point("planner")

    builder.add_edge("planner", "agent")
    builder.add_edge("agent", "tool")
    builder.add_edge("tool", "memory")
    builder.add_edge("memory", END)

    return builder.compile()
