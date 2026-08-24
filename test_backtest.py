from src.tools.backtest import run_backtest
import os

def test_backtest_tool():
    # A sample script that the Backtest Engineer would generate
    script = """
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Generate dummy data instead of yfinance for faster testing
dates = pd.date_range('2023-01-01', periods=100)
returns = np.random.normal(0.001, 0.02, 100)
cumulative = (1 + returns).cumprod()

plt.figure()
plt.plot(dates, cumulative)
plt.savefig('output/equity_curve.png')

print(json.dumps({
    "sharpe": 1.5,
    "return": 0.10,
    "max_drawdown": -0.05
}))
"""
    
    print("--- Testing run_backtest tool ---")
    result = run_backtest.invoke({"code": script})
    print(result)
    
    assert "BACKTEST SUCCESS" in result, "Backtest tool failed"
    assert os.path.exists("output/equity_curve.png"), "Equity curve PNG was not saved"
    
    print("\n✅ Backtest Engineer tool verification passed.")

if __name__ == "__main__":
    test_backtest_tool()
