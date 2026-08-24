import yfinance as yf
import pandas as pd
from langchain_core.tools import tool

@tool
def fetch_stock_data(ticker: str, period: str = "1y", interval: str = "1d") -> str:
    """
    Fetches historical stock data (OHLCV) using yfinance.
    Returns the tail of the data as a string summarizing recent price action.
    """
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        if df.empty:
            return f"No data found for ticker {ticker}."
        tail_df = df.tail(10)
        return f"Recent 10 periods data for {ticker}:\n{tail_df.to_string()}"
    except Exception as e:
        return f"Error fetching data for {ticker}: {str(e)}"

@tool
def calculate_technical_indicators(ticker: str, period: str = "1y") -> str:
    """
    Calculates technical indicators (SMA, RSI, MACD) using pure pandas.
    Returns a summary of the current technical state of the asset.
    """
    try:
        df = yf.download(ticker, period=period, interval="1d", progress=False)
        if df.empty:
            return f"No data found for {ticker}."
            
        if isinstance(df.columns, pd.MultiIndex):
            try:
                df = df.xs(ticker, axis=1, level=1, drop_level=True)
            except KeyError:
                df.columns = df.columns.droplevel(1)
                
        # Pure Pandas Calculations
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['SMA_200'] = df['Close'].rolling(window=200).mean()
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI_14'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
        
        latest = df.iloc[-1]
        
        close = latest.get("Close", None)
        sma20 = latest.get("SMA_20", None)
        sma50 = latest.get("SMA_50", None)
        sma200 = latest.get("SMA_200", None)
        rsi = latest.get("RSI_14", None)
        macd = latest.get("MACD", None)
        macd_sig = latest.get("MACD_Signal", None)
        
        summary = [
            f"--- Technical Summary for {ticker} ---",
            f"Latest Close: {close:.2f}" if close else "Latest Close: N/A",
            f"SMA 20: {sma20:.2f}" if pd.notna(sma20) else "SMA 20: N/A",
            f"SMA 50: {sma50:.2f}" if pd.notna(sma50) else "SMA 50: N/A",
            f"SMA 200: {sma200:.2f}" if pd.notna(sma200) else "SMA 200: N/A",
            f"RSI (14): {rsi:.2f}" if pd.notna(rsi) else "RSI: N/A",
            f"MACD Value: {macd:.3f}" if pd.notna(macd) else "MACD: N/A",
            f"MACD Signal: {macd_sig:.3f}" if pd.notna(macd_sig) else "MACD Signal: N/A",
        ]
        
        if pd.notna(close) and pd.notna(sma200):
            if close > sma200:
                summary.append("Trend: Long-term UPTREND (Close > SMA 200)")
            else:
                summary.append("Trend: Long-term DOWNTREND (Close < SMA 200)")
                
        if pd.notna(rsi):
            if rsi > 70:
                summary.append("RSI State: OVERBOUGHT (>70)")
            elif rsi < 30:
                summary.append("RSI State: OVERSOLD (<30)")
            else:
                summary.append("RSI State: NEUTRAL")
                
        return "\n".join(summary)
    
    except Exception as e:
        return f"Error calculating technicals for {ticker}: {str(e)}"
