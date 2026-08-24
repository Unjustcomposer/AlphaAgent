import os
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from src.llm import get_llm
from src.tools.search import search_financial_news
from src.state import AgentState

def researcher_node(state: AgentState):
    """
    Macro & Sentiment Researcher agent. Searches for recent news.
    """
    model_name = os.getenv("LLM_MODEL", "gemini-2.5-flash")
    llm = get_llm()
    
    tools = [search_financial_news]
    
    system_prompt = (
        "You are a Macro & Sentiment Researcher for a quantitative hedge fund. "
        "Use your search tools to find recent news, sentiment, or macroeconomic catalysts "
        "affecting the given ticker. Summarize the findings into a clear 'regime' (e.g., Risk-On, Risk-Off, Catalyst Pending)."
    )
    
    agent = create_react_agent(llm, tools, prompt=system_prompt)
    
    ticker = state.get("ticker", "AAPL")
    prompt = f"Search for recent financial news and macro events affecting {ticker}. Summarize the sentiment and current market regime."
    
    result = agent.invoke({"messages": [HumanMessage(content=prompt)]})
    final_message = result["messages"][-1]
    
    return {
        "messages": [final_message],
        "macro_research": final_message.content
    }
