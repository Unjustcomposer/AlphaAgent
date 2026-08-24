import subprocess
import os
import json
import tempfile
from langchain_core.tools import tool

@tool
def run_backtest(code: str) -> str:
    """
    Executes Python backtest code in an isolated subprocess.
    The code must calculate a backtest using pandas and print a JSON object to stdout.
    The JSON must contain keys: 'sharpe', 'return', 'max_drawdown'.
    The code can optionally save an equity curve plot to 'output/equity_curve.png'.
    
    Args:
        code: Complete Python script as a string. Must include imports (e.g., pandas, yfinance).
    """
    # Create output directory if it doesn't exist
    os.makedirs("output", exist_ok=True)
    
    # We write the code to a temporary file and run it
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        temp_file = f.name
        
    try:
        # Run the script with a 30-second timeout
        import sys
        result = subprocess.run(
            [sys.executable, temp_file], 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        
        if result.returncode != 0:
            return f"BACKTEST FAILED WITH ERROR:\n{result.stderr}\n\nSTDOUT:\n{result.stdout}"
        
        stdout = result.stdout
        
        # Try to parse the last line of stdout as JSON
        try:
            # Often LLMs print other things, so we search for a JSON block or try to parse the whole stdout
            # Let's just find the first { and last }
            start = stdout.find('{')
            end = stdout.rfind('}')
            if start != -1 and end != -1:
                json_str = stdout[start:end+1]
                metrics = json.loads(json_str)
                return f"BACKTEST SUCCESS! Metrics:\n{json.dumps(metrics, indent=2)}\n\n(Full stdout logged)"
            else:
                return f"BACKTEST SUCCESS, but could not parse metrics JSON from stdout.\nStdout:\n{stdout}"
        except json.JSONDecodeError:
            return f"BACKTEST SUCCESS, but JSON parsing failed.\nStdout:\n{stdout}"
            
    except subprocess.TimeoutExpired:
        return "BACKTEST TIMED OUT (30 seconds exceeded). Ensure there are no infinite loops or large data fetches."
    except Exception as e:
        return f"UNEXPECTED ERROR executing backtest: {str(e)}"
    finally:
        # Clean up temp file
        if os.path.exists(temp_file):
            os.remove(temp_file)
