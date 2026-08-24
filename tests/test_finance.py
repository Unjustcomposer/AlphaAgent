import json
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.finance import fetch_stock_data, calculate_technical_indicators

def test_finance_tools():
    print("--- Testing fetch_stock_data ---")
    data = fetch_stock_data.invoke({"ticker": "AAPL", "period": "1mo"})
    print(data)
    assert "Close" in data, "Failed to fetch OHLCV data"
    
    print("\n--- Testing calculate_technical_indicators ---")
    ta = calculate_technical_indicators.invoke({"ticker": "AAPL", "period": "6mo"})
    print(ta)
    assert "SMA 20:" in ta, "Failed to calculate indicators"
    print("\n✅ Finance Tools verification passed.")

if __name__ == "__main__":
    test_finance_tools()
