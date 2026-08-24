import os
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from src.llm import get_llm
from src.state import AgentState

# Define the structured output for routing
class Route(BaseModel):
    next_agent: str

def supervisor_node(state: AgentState):
    """
    The supervisor reads the state and decides who acts next.
    Allowed targets: 'quant', 'researcher', 'backtest', 'approve', 'FINISH'
    """
    messages = state.get("messages", [])
    
    # We use the configured LLM or default to gemini-2.5-flash
    model_name = os.getenv("LLM_MODEL", "gemini-2.5-flash")
    llm = get_llm()
    
    system_prompt = (
        "You are the Supervisor of a Quantitative Research Team. "
        "Your job is to orchestrate the workflow by routing to the correct agent.\n\n"
        "WORKFLOW RULES:\n"
        "1. First, send to 'researcher' to get macro/sentiment news for the ticker.\n"
        "2. Then, send to 'quant' to get technical indicators.\n"
        "3. Once both are done, send to 'backtest' to generate and run the trading strategy.\n"
        "4. After the backtest is complete, send to 'approve' to get human validation.\n"
        "5. Only send 'FINISH' if the report has been generated after approval.\n\n"
        "Current Ticker: {ticker}\n"
        "Has Technical Analysis? {has_ta}\n"
        "Has Macro Research? {has_macro}\n"
        "Has Backtest Results? {has_backtest}\n"
        "Is Human Approved? {is_approved}\n\n"
        "Based on the conversation history and state, decide the next_agent.\n"
        "Must be one of: 'quant', 'researcher', 'backtest', 'approve', 'FINISH'."
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("placeholder", "{messages}"),
        ("human", "Evaluate the state and determine the next_agent."),
    ])
    
    # Bind the structured output schema
    router = prompt | llm.with_structured_output(Route)
    
    # Format the variables
    has_ta = "Yes" if state.get("technical_analysis") else "No"
    has_macro = "Yes" if state.get("macro_research") else "No"
    has_backtest = "Yes" if state.get("backtest_results") else "No"
    is_approved = "Yes" if state.get("human_approved") else "No"
    
    import time, re
    for attempt in range(5):
        try:
            response = router.invoke({
                "messages": messages,
                "ticker": state.get("ticker", "UNKNOWN"),
                "has_ta": has_ta,
                "has_macro": has_macro,
                "has_backtest": has_backtest,
                "is_approved": is_approved
            })
            return {"next_agent": response.next_agent}
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "rate" in error_str.lower():
                match = re.search(r'retry\s*(?:in|after|delay)[\s:]*(\d+)', error_str, re.IGNORECASE)
                wait = int(match.group(1)) + 5 if match else 65
                print(f"\n[Supervisor] Rate limited. Waiting {wait}s (attempt {attempt+1}/5)...")
                time.sleep(wait)
            else:
                raise
    
    # Final attempt - let it raise if it fails
    response = router.invoke({
        "messages": messages,
        "ticker": state.get("ticker", "UNKNOWN"),
        "has_ta": has_ta,
        "has_macro": has_macro,
        "has_backtest": has_backtest,
        "is_approved": is_approved
    })
    return {"next_agent": response.next_agent}
