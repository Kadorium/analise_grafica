import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def generate_sample_data(days=365, initial_price=100.0, volatility=0.02, save=True):
    """
    Generate synthetic OHLCV data for testing and demos.
    
    Args:
        days (int): Number of days of data to generate
        initial_price (float): Starting price
        volatility (float): Daily volatility factor
        save (bool): Whether to save the data to a CSV file
        
    Returns:
        pd.DataFrame: DataFrame with OHLCV data
    """
    dates = [(datetime.now() - timedelta(days=days-i)).strftime('%Y-%m-%d') for i in range(days)]
    
    # Initialize price and arrays
    price = initial_price
    opens, highs, lows, closes = [], [], [], []
    volumes = []
    
    # Add slight trend bias
    trend = np.random.choice([-0.0001, 0.0001])
    
    for i in range(days):
        # Random price change with slight trend bias
        daily_volatility = np.random.normal(trend, volatility)
        price *= (1 + daily_volatility)
        
        # Generate OHLC
        daily_open = price * (1 + np.random.normal(0, volatility/2))
        daily_high = max(daily_open, price) * (1 + abs(np.random.normal(0, volatility/2)))
        daily_low = min(daily_open, price) * (1 - abs(np.random.normal(0, volatility/2)))
        
        opens.append(daily_open)
        highs.append(daily_high)
        lows.append(daily_low)
        closes.append(price)
        
        # Generate volume - higher volume on bigger price moves
        volume = np.random.randint(1000, 10000) * (1 + abs(daily_volatility) * 5)
        volumes.append(int(volume))
    
    # Create DataFrame
    df = pd.DataFrame({
        'date': dates,
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
        'volume': volumes
    })
    
    # Save to CSV if requested
    if save:
        os.makedirs('data/sample', exist_ok=True)
        df.to_csv('data/sample/sample_stock_data.csv', index=False)
        print(f"Sample data saved to 'data/sample/sample_stock_data.csv'")
    
    return df

def load_sample_data():
    """
    Load sample data from CSV or generate if it doesn't exist.
    
    Returns:
        pd.DataFrame: DataFrame with OHLCV data
    """
    sample_path = 'data/sample/sample_stock_data.csv'
    
    if os.path.exists(sample_path):
        return pd.read_csv(sample_path)
    else:
        return generate_sample_data(save=True)

if __name__ == "__main__":
    # Generate a sample dataset when run directly
    data = generate_sample_data(days=500, initial_price=150.0, volatility=0.015)
    print(f"Generated sample data with {len(data)} rows")
    print(data.head()) 