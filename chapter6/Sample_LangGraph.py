from pathlib import Path
from typing import TypedDict, List

# Define the global state data structure
class AgentState(TypedDict):
    messages: List[str]      # Conversation history
    current_task: str        # Current task
    final_answer: str        # Final answer
    # ... any other state fields you want to track


# Define a "planner" node function
def planner_node(state: AgentState) -> AgentState:
    """Create a plan based on the current task and update state."""
    current_task = state["current_task"]
    # ... call an LLM to generate a plan ...
    plan = f"Plan generated for task '{current_task}'..."

    # Append new message to state
    state["messages"].append(plan)
    return state


# Define an "executor" node function
def executor_node(state: AgentState) -> AgentState:
    """Execute the latest plan and update state."""
    latest_plan = state["messages"][-1]
    # ... execute the plan and obtain results ...
    result = f"Result of executing plan '{latest_plan}'..."

    state["messages"].append(result)
    return state


def final_node(state: AgentState) -> AgentState:
    """Assemble the final answer and update state."""
    state["final_answer"] = state["messages"][-1]
    return state


def should_continue(state: AgentState) -> str:
    """Condition function: decide routing based on state."""
    # Example: if messages are fewer than 3, continue planning
    if len(state["messages"]) < 3:
        # Return value must match keys used to add conditional edges
        return "continue_to_planner"
    else:
        return "go_to_final"


from langgraph.graph import StateGraph, END

# Initialize a state graph and bind our state structure
workflow = StateGraph(AgentState)

# Add node functions to the graph
workflow.add_node("planner", planner_node)
workflow.add_node("executor", executor_node)
workflow.add_node("final", final_node)

# Set the graph entry point
workflow.set_entry_point("planner")

# Add a regular edge connecting planner -> executor
workflow.add_edge("planner", "executor")

# Add conditional edges to implement dynamic routing
workflow.add_conditional_edges(
    # start node
    "executor",
    # condition function
    should_continue,
    # routing map: map the condition function's return to a target node
    {
        "continue_to_planner": "planner",  # if returns "continue_to_planner", jump back to planner
        "go_to_final": "final"              # if returns "go_to_final", go to final node
    }
)

# After final node, end the flow
workflow.add_edge("final", END)

# Compile graph into an executable app
app = workflow.compile()

# 1. Print Mermaid diagram source (copy to Mermaid Live Editor or Markdown that supports Mermaid)
mermaid_code = app.get_graph().draw_mermaid()
print("\n===== Mermaid diagram source =====")
print(mermaid_code)

# 2. Save Mermaid source file
current_dir = Path(__file__).resolve().parent
mermaid_path = current_dir / "langgraph_workflow.mmd"
mermaid_path.write_text(mermaid_code, encoding="utf-8")
print(f"\nMermaid source saved to: {mermaid_path}")

# 3. Save PNG image
# Note: draw_mermaid_png() may access mermaid.ink; this step can fail if the network is unreliable.
png_path = current_dir / "langgraph_workflow.png"
try:
    png_data = app.get_graph().draw_mermaid_png()
    png_path.write_bytes(png_data)
    print(f"PNG image saved to: {png_path}")
except Exception as e:
    print(f"PNG generation failed: {e}")
    print("You can still open langgraph_workflow.mmd and paste the content into Mermaid Live Editor to view the graph.")

# Run the graph with example input
inputs = {
    "current_task": "Analyze recent AI industry news",
    "messages": [],
    "final_answer": ""
}

print("\n===== LangGraph execution trace =====")
for event in app.stream(inputs):
    print(event)
