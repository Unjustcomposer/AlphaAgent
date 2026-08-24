import os
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from src.llm import get_llm
from src.tools.finance import fetch_stock_data, calculate_technical_indicators
from src.state import AgentState

def quant_node(state: AgentState):
    """
    Quantitative Analyst agent. Uses tools to fetch data and calculate indicators.
    Returns the summary back into the state.
    """
    model_name = os.getenv("LLM_MODEL", "gemini-2.5-flash")
    llm = get_llm()
    
    tools = [fetch_stock_data, calculate_technical_indicators]
    
    system_prompt = (
        "You are a strict Quantitative Analyst. Your job is to pull data and calculate technical indicators "
        "for the requested ticker. DO NOT hallucinate math. Always use your tools.\n"
        "After using the tools, provide a concise summary of the technical state of the asset."
    )
    
    # Create a sub-graph for the ReAct agent
    agent = create_react_agent(llm, tools, prompt=system_prompt)
    
    # We pass only the relevant context to the agent
    ticker = state.get("ticker", "AAPL")
    prompt = f"Please fetch the latest data and calculate technical indicators for {ticker}. Summarize the trend."
    
    # Invoke the agent
    result = agent.invoke({"messages": [HumanMessage(content=prompt)]})
    
    # The last message is the agent's final response
    final_message = result["messages"][-1]
    
    # Update the main state
    return {
        "messages": [final_message],
        "technical_analysis": final_message.content
    }
