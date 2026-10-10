r"""BMI calculator built as a LangGraph workflow.

Flow:
    START -> validate --(valid)--> calculate_bmi -> classify -> END
                     \--(invalid)--> handle_error -> END
"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph


# 1. STATE: the shared data every node can read and update.
class BMIState(TypedDict, total=False):
    weight_kg: float
    height_m: float
    bmi: float
    category: str
    error: str


# 2. NODES: plain functions. Each takes the state and returns ONLY the keys it changes.
def validate(state: BMIState) -> dict:
    if state["weight_kg"] <= 0 or state["height_m"] <= 0:
        return {"error": "Weight and height must be positive numbers."}
    return {}


def calculate_bmi(state: BMIState) -> dict:
    bmi = state["weight_kg"] / (state["height_m"] ** 2)
    return {"bmi": round(bmi, 2)}


def classify(state: BMIState) -> dict:
    bmi = state["bmi"]
    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25:
        category = "Normal weight"
    elif bmi < 30:
        category = "Overweight"
    else:
        category = "Obese"
    return {"category": category}


def handle_error(state: BMIState) -> dict:
    return {"category": "Unknown"}


# 3. ROUTER: decides which node runs next. Used by the conditional edge.
def route_after_validate(state: BMIState) -> str:
    return "invalid" if state.get("error") else "valid"


# 4. BUILD THE GRAPH: register nodes, then connect them with edges.
builder = StateGraph(BMIState)

builder.add_node("validate", validate)
builder.add_node("calculate_bmi", calculate_bmi)
builder.add_node("classify", classify)
builder.add_node("handle_error", handle_error)

builder.add_edge(START, "validate")
builder.add_conditional_edges(
    "validate",
    route_after_validate,
    {"valid": "calculate_bmi", "invalid": "handle_error"},
)
builder.add_edge("calculate_bmi", "classify")
builder.add_edge("classify", END)
builder.add_edge("handle_error", END)

graph = builder.compile()


# 5. RUN IT
if __name__ == "__main__":
    print(graph.invoke({"weight_kg": 70, "height_m": 1.75}))
    print(graph.invoke({"weight_kg": 95, "height_m": 1.70}))
    print(graph.invoke({"weight_kg": -5, "height_m": 1.70}))

    # Watch each node's update as it happens
    for step in graph.stream({"weight_kg": 50, "height_m": 1.80}):
        print("step:", step)

    # Print the graph structure as a Mermaid diagram
    print(graph.get_graph().draw_mermaid())
