import os
from dotenv import load_dotenv
from src.graph import build_graph
from langgraph.types import Command
from langchain_core.messages import HumanMessage

def main():
    print(" Initializing AlphaAgent-LangGraph...")
    
    # Load environment variables
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("GROQ_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
        print("ERROR: No API KEY found in .env file.")
        return

    graph = build_graph()
    
    print("\n--- Quantitative Research Pipeline ---")
    ticker = input("Enter a ticker symbol to research (e.g., AAPL): ").strip().upper()
    if not ticker:
        ticker = "AAPL"
        
    config = {"configurable": {"thread_id": "alpha-agent-run-1"}}
    
    # Initial state
    initial_state = {
        "messages": [HumanMessage(content=f"Please research {ticker} and develop a momentum strategy.")],
        "ticker": ticker
    }
    
    print(f"\n Starting research for {ticker}...\n")
    
    # Stream the graph execution
    for event in graph.stream(initial_state, config, stream_mode="values"):
        if "next_agent" in event:
            if event["next_agent"] != "FINISH":
                print(f"[Supervisor] Routing to -> {event['next_agent'].upper()}")
                
    # Check if we hit the interrupt
    state = graph.get_state(config)
    
    if state.next and "hitl_gate" in state.next:
        print("\n" + "="*50)
        print(" HUMAN-IN-THE-LOOP (HITL) GATE")
        print("="*50)
        print("\nThe backtest has completed. Here is the generated hypothesis:\n")
        print(state.values.get("hypothesis", "No hypothesis found."))
        
        print("\nEquity curve saved to: output/equity_curve.png")
        
        approval = input("\nDo you approve this strategy for final report generation? (yes/no): ").strip().lower()
        
        if approval in ['y', 'yes']:
            print("\nSUCCESS: Strategy Approved! Generating final report...")
            # Resume graph with state update via Command
            graph.invoke(Command(resume=True, update={"human_approved": True}), config)
        else:
            print("\nERROR: Strategy Rejected. Sending back to Supervisor for revision...")
            graph.invoke(Command(resume=True, update={"human_approved": False}), config)
            
        print("\nPipeline finished.")
        if approval in ['y', 'yes']:
             print(" Check output/strategy_report.md for the final results!")
    else:
        print("\nPipeline finished without hitting the HITL gate.")

if __name__ == "__main__":
    main()
