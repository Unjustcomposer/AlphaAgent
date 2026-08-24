from typing import Annotated, TypedDict, Any
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage

class AgentState(TypedDict):
    """
    The state of the AlphaAgent-LangGraph pipeline.
    """
    # LangGraph's add_messages reducer takes care of appending new messages
    messages: Annotated[list[AnyMessage], add_messages]
    
    # State routing and tracking
    next_agent: str
    
    # Data payloads
    ticker: str
    market_data: dict
    technical_analysis: str
    macro_research: str
    hypothesis: str
    
    # Execution payloads
    backtest_code: str
    backtest_results: dict
    equity_curve_path: str
    
    # Gate payloads
    human_approved: bool
    final_report: str
