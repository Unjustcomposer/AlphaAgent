import os
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage

from src.state import AgentState
from src.agents.supervisor import supervisor_node
from src.agents.quant import quant_node
from src.agents.researcher import researcher_node
from src.agents.backtest import backtest_node

def hitl_gate_node(state: AgentState):
    """
    A simple node that just passes through, but we will interrupt BEFORE this node.
    It reads the human's approval from the state (injected via Command during resume).
    """
    # The actual interruption happens because we compile with interrupt_before=["hitl_gate"]
    # When resumed, the state should have 'human_approved' updated
    return {}

def report_node(state: AgentState):
    """
    Generates the final markdown report.
    """
    ticker = state.get("ticker", "UNKNOWN")
    ta = state.get("technical_analysis", "No TA")
    macro = state.get("macro_research", "No Macro")
    hypo = state.get("hypothesis", "No Hypothesis")
    
    report = f"""# Quantitative Strategy Report: {ticker}

## 1. Macro & Sentiment Regime
{macro}

## 2. Technical Analysis
{ta}

## 3. Backtest & Hypothesis
{hypo}

## 4. Execution details
Equity curve saved to: {state.get('equity_curve_path', 'N/A')}
Human Approved: {state.get('human_approved', False)}
"""
    
    os.makedirs("output", exist_ok=True)
    with open("output/strategy_report.md", "w", encoding="utf-8") as f:
        f.write(report)
        
    return {"final_report": report}

# Define edge routing logic
def supervisor_router(state: AgentState):
    next_agent = state.get("next_agent")
    if next_agent == "quant":
        return "quant"
    elif next_agent == "researcher":
        return "researcher"
    elif next_agent == "backtest":
        return "backtest"
    elif next_agent == "approve":
        return "hitl_gate"
    elif next_agent == "FINISH":
        return END
    else:
        # Default fallback
        return END

def hitl_router(state: AgentState):
    if state.get("human_approved", False):
        return "report"
    else:
        # If rejected, clear backtest results and go back to supervisor
        return "supervisor"

# Build Graph
def build_graph():
    builder = StateGraph(AgentState)
    
    # Add Nodes
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("quant", quant_node)
    builder.add_node("researcher", researcher_node)
    builder.add_node("backtest", backtest_node)
    builder.add_node("hitl_gate", hitl_gate_node)
    builder.add_node("report", report_node)
    
    # Add Edges
    builder.add_edge(START, "supervisor")
    
    builder.add_conditional_edges(
        "supervisor", 
        supervisor_router, 
        {
            "quant": "quant",
            "researcher": "researcher",
            "backtest": "backtest",
            "hitl_gate": "hitl_gate",
            END: END
        }
    )
    
    # Workers report back to supervisor
    builder.add_edge("quant", "supervisor")
    builder.add_edge("researcher", "supervisor")
    builder.add_edge("backtest", "supervisor")
    
    # HITL logic
    builder.add_conditional_edges(
        "hitl_gate",
        hitl_router,
        {
            "report": "report",
            "supervisor": "supervisor"
        }
    )
    
    builder.add_edge("report", END)
    
    # Compile with MemorySaver and interrupt_before
    memory = MemorySaver()
    graph = builder.compile(checkpointer=memory, interrupt_before=["hitl_gate"])
    
    return graph
