"""
Simple test script for RSI strategy
"""
import pandas as pd
import os
import traceback
from strategies import STRATEGY_REGISTRY, get_default_parameters

def main():
    print("Testing RSI strategy")
    
    # Load data
    if os.path.exists("data/teste_arranged.csv"):
        print("Loading data from data/teste_arranged.csv")
        data = pd.read_csv("data/teste_arranged.csv")
        if 'date' in data.columns:
            data['date'] = pd.to_datetime(data['date'])
    else:
        print("Data file not found!")
        return
    
    print(f"Data loaded, shape: {data.shape}")
    print(f"Columns: {data.columns.tolist()}")
    
    # Get RSI strategy
    if 'rsi' in STRATEGY_REGISTRY:
        rsi_func = STRATEGY_REGISTRY['rsi']
        print(f"RSI strategy found")
    else:
        print("RSI strategy not found in registry!")
        print(f"Available strategies: {list(STRATEGY_REGISTRY.keys())}")
        return
    
    # Get default parameters
    default_params = get_default_parameters('rsi')
    print(f"Default RSI parameters: {default_params}")
    
    # Run strategy
    try:
        signals_df = rsi_func(data.copy(), **default_params)
        print(f"Generated signals, shape: {signals_df.shape}")
        print(f"Columns after strategy: {signals_df.columns.tolist()}")
        
        # Check signals
        if 'signal' in signals_df.columns:
            print(f"Signal counts: {signals_df['signal'].value_counts().to_dict()}")
        else:
            print("No 'signal' column in output!")
    except Exception as e:
        print(f"Error running RSI strategy: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main() 