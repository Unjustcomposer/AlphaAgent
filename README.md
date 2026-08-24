# AlphaAgent-LangGraph ????

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![LangGraph](https://img.shields.io/badge/LangGraph-0.2.0%2B-brightgreen)
![Gemini](https://img.shields.io/badge/LLM-Gemini_Flash-orange)

AlphaAgent is a stateful multi-agent quantitative research pipeline orchestrating a team of specialized AI agents. Built with LangGraph, this project mirrors a professional quantitative team's workflow: gathering macro sentiment, pulling technical data, writing backtests, and presenting hypotheses—with a critical **Human-in-the-Loop (HITL)** checkpoint.

## Architecture

AlphaAgent uses a **Supervisor Pattern** driven by LangGraph's explicit StateGraph.

\\\mermaid
graph TD
    START((User Query)) --> Supervisor
    Supervisor -->|"route: quant"| QuantAnalyst["?? Quant Analyst"]
    Supervisor -->|"route: researcher"| MacroResearcher["?? Macro Researcher"]
    Supervisor -->|"route: backtest"| BacktestEngineer["?? Backtest Engineer"]
    Supervisor -->|"route: approve"| HITLGate["?? HITL Approval Gate"]
    QuantAnalyst --> Supervisor
    MacroResearcher --> Supervisor
    BacktestEngineer --> Supervisor
    HITLGate -->|"approved"| ReportGenerator["?? Report Generator"]
    HITLGate -->|"rejected / revise"| Supervisor
    ReportGenerator --> END((END))
\\\

## The Agents

1. **Supervisor**: A pure routing node that orchestrates the flow and manages state transitions using LangGraph conditional edges.
2. **Quant Analyst**: Uses \yfinance\ and \pandas-ta\ to pull historical OHLCV data and calculate strictly deterministic technical indicators, preventing LLM math hallucinations.
3. **Macro & Sentiment Researcher**: Uses \duckduckgo-search\ to identify current market regimes or news catalysts.
4. **Backtest Engineer**: Takes the gathered intelligence and dynamically generates executable \pandas\-based Python backtest code in an isolated subprocess.
5. **HITL Gate**: Uses LangGraph's \interrupt()\ primitive to pause execution, requiring the human portfolio manager to approve the generated strategy before finalization.

## Quick Start

### 1. Install Dependencies
\\\ash
pip install -r requirements.txt
\\\

### 2. Configure Environment
Copy the example environment file and add your Google Gemini API key:
\\\ash
cp .env.example .env
\\\
Edit \.env\ and set \GOOGLE_API_KEY=your_key_here\.

### 3. Run the Pipeline
\\\ash
python main.py
\\\
The agent will begin its research phase, write the backtest, and pause to request your approval in the terminal.

## Sample Output

See the \sample_output/\ directory for an example of a generated strategy report and the corresponding equity curve.

## Why This Architecture?

* **No LLM Math**: LLMs are terrible at calculating moving averages. The Quant Analyst uses real Python tools for deterministic data.
* **Safer Execution**: The Backtest Engineer executes code in a subprocess with timeouts, isolating the main state graph from crashes.
* **Modern LangGraph**: Uses the explicit manual StateGraph pattern (preferred over wrappers) and the latest \interrupt()\ primitive for stateful human-in-the-loop validation.
