import os
import json
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from src.llm import get_llm
from src.tools.backtest import run_backtest
from src.state import AgentState

def backtest_node(state: AgentState):
    """
    Backtest Engineer agent.
    Takes the technical and macro analysis, forms a hypothesis, generates pandas code, and runs it.
    """
    model_name = os.getenv("LLM_MODEL", "gemini-2.5-flash")
    # Use a higher capacity model if possible for coding, but flash works fine
    llm = get_llm()
    
    tools = [run_backtest]
    
    system_prompt = """You are a Quantitative Backtest Engineer.
Your job is to write a Python script that backtests a trading strategy using pandas.
You have access to the `run_backtest` tool, which executes your code safely.

RULES FOR THE PYTHON CODE:
1. Fetch data using `yfinance`. Use the ticker provided.
2. Use `pandas` (and optionally `pandas-ta`) to calculate signals.
3. The strategy should be based on the technical and macro analysis provided.
4. Calculate simple metrics: 'sharpe', 'return', 'max_drawdown'. 
   (Assume risk-free rate = 0, 252 trading days).
5. Plot the cumulative returns and save it exactly to 'output/equity_curve.png' using matplotlib.
6. The script MUST end by printing EXACTLY ONE JSON object to stdout containing the metrics. 
   Example: print(json.dumps({"sharpe": 1.2, "return": 0.15, "max_drawdown": -0.05}))
7. Do not use complex frameworks like vectorbt or backtrader. Stick to simple pandas vectorized backtesting (e.g. calculating strategy returns as signal.shift(1) * daily_returns).

Once you run the tool and get a SUCCESS response, summarize the hypothesis and the results.
"""

    agent = create_react_agent(llm, tools, prompt=system_prompt)
    
    ticker = state.get("ticker", "AAPL")
    ta = state.get("technical_analysis", "None")
    macro = state.get("macro_research", "None")
    
    prompt = f"""
Ticker: {ticker}
Technical Analysis:
{ta}

Macro Research:
{macro}

Please formulate a trading hypothesis based on this data, write the Python backtest script, and run it using the tool. 
Make sure the script saves the plot to 'output/equity_curve.png' and prints the JSON metrics.
"""
    
    result = agent.invoke({"messages": [HumanMessage(content=prompt)]})
    final_message = result["messages"][-1]
    
    # Handle content being a list (Gemini returns content blocks) or a string
    content = final_message.content
    if isinstance(content, list):
        content = "\n".join(str(c) for c in content)
    
    return {
        "messages": [final_message],
        "hypothesis": "Strategy based on TA and Macro.\n" + content,
        "backtest_results": {"status": "completed", "details": content},
        "equity_curve_path": "output/equity_curve.png"
    }
