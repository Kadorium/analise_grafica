import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Import our modules
from data.data_loader import DataLoader
from indicators.moving_averages import add_sma, add_ema
from indicators.momentum import add_rsi, add_macd
from indicators.volatility import add_bollinger_bands
from strategies import create_strategy
from backtesting.backtester import Backtester
from optimization.optimizer import optimize_strategy
import config as cfg

def generate_test_data(days=365, initial_price=100.0, volatility=0.02):
    """Generate synthetic OHLCV data for testing."""
    dates = [(datetime.now() - timedelta(days=days-i)).strftime('%Y-%m-%d') for i in range(days)]
    
    # Initialize price and arrays
    price = initial_price
    opens, highs, lows, closes = [], [], [], []
    volumes = []
    
    for i in range(days):
        # Random price change
        daily_volatility = np.random.normal(0, volatility)
        price *= (1 + daily_volatility)
        
        # Generate OHLC
        daily_open = price * (1 + np.random.normal(0, volatility/2))
        daily_high = max(daily_open, price) * (1 + abs(np.random.normal(0, volatility/2)))
        daily_low = min(daily_open, price) * (1 - abs(np.random.normal(0, volatility/2)))
        
        opens.append(daily_open)
        highs.append(daily_high)
        lows.append(daily_low)
        closes.append(price)
        
        # Generate volume
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
    
    return df

def test_data_loader():
    """Test DataLoader functionality."""
    print("\n[TEST] Testing DataLoader...")
    
    # Generate test data
    test_data = generate_test_data()
    
    # Create a DataLoader instance
    data_loader = DataLoader()
    
    # Set the data
    data_loader.data = test_data.copy()
    
    # Clean the data
    cleaned_data = data_loader.clean_data()
    
    print(f"  ✅ Original data shape: {test_data.shape}")
    print(f"  ✅ Cleaned data shape: {cleaned_data.shape}")
    print(f"  ✅ Date column is datetime: {pd.api.types.is_datetime64_any_dtype(cleaned_data['date'])}")
    
    return cleaned_data

def test_indicators(data):
    """Test technical indicators."""
    print("\n[TEST] Testing Indicators...")
    
    # Add indicators
    data = add_sma(data, window=20)
    data = add_ema(data, window=14)
    data = add_rsi(data, window=14)
    data = add_macd(data)
    data = add_bollinger_bands(data)
    
    indicator_columns = [col for col in data.columns 
                         if col not in ['date', 'open', 'high', 'low', 'close', 'volume']]
    
    print(f"  ✅ Added {len(indicator_columns)} indicator columns")
    print(f"  ✅ Indicator columns: {', '.join(indicator_columns)}")
    
    return data

def test_strategies(data):
    """Test strategy creation and signal generation."""
    print("\n[TEST] Testing Strategies...")
    
    strategies_to_test = ['trend_following', 'mean_reversion', 'breakout']
    results = {}
    
    for strategy_type in strategies_to_test:
        strategy = create_strategy(strategy_type)
        signals = strategy.generate_signals(data.copy())
        
        buy_signals = signals[signals['signal'] > 0].shape[0]
        sell_signals = signals[signals['signal'] < 0].shape[0]
        
        results[strategy_type] = {
            'buy_signals': buy_signals,
            'sell_signals': sell_signals
        }
        
        print(f"  ✅ {strategy_type.capitalize()} strategy: {buy_signals} buy signals, {sell_signals} sell signals")
    
    return results

def test_backtesting(data, strategy_type='trend_following'):
    """Test backtesting engine."""
    print("\n[TEST] Testing Backtester...")
    
    # Create strategy
    strategy = create_strategy(strategy_type)
    
    # Create backtester
    backtester = Backtester(
        data=data,
        strategy=strategy,
        initial_capital=10000.0,
        commission=0.001
    )
    
    # Run backtest
    results = backtester.run()
    
    print(f"  ✅ Backtest completed for {strategy_type}")
    print(f"  ✅ Final portfolio value: ${results['final_portfolio_value']:.2f}")
    print(f"  ✅ Total return: {results['total_return']:.2%}")
    print(f"  ✅ Sharpe ratio: {results['sharpe_ratio']:.2f}")
    print(f"  ✅ Maximum drawdown: {results['max_drawdown']:.2%}")
    print(f"  ✅ Total trades: {results['total_trades']}")
    
    return results

def test_optimization(data, strategy_type='trend_following'):
    """Test optimization module."""
    print("\n[TEST] Testing Optimizer...")
    
    # Define parameter ranges
    if strategy_type == 'trend_following':
        param_ranges = {
            'fast_ma_period': range(5, 21, 5),
            'slow_ma_period': range(20, 61, 10)
        }
    elif strategy_type == 'mean_reversion':
        param_ranges = {
            'rsi_period': range(10, 21, 5),
            'oversold': range(20, 41, 10),
            'overbought': range(60, 81, 10)
        }
    else:  # breakout
        param_ranges = {
            'lookback_period': range(10, 31, 10),
            'volume_threshold': [1.2, 1.5, 2.0],
            'price_threshold': [0.01, 0.02, 0.03]
        }
    
    # Run optimization
    best_params, results = optimize_strategy(
        data=data,
        strategy_type=strategy_type,
        param_ranges=param_ranges,
        metric='sharpe_ratio'
    )
    
    print(f"  ✅ Optimization completed for {strategy_type}")
    print(f"  ✅ Best parameters: {json.dumps(best_params, indent=2)}")
    print(f"  ✅ Best sharpe ratio: {results['sharpe_ratio']:.2f}")
    print(f"  ✅ Best total return: {results['total_return']:.2%}")
    
    return best_params, results

def test_config():
    """Test configuration management."""
    print("\n[TEST] Testing Configuration...")
    
    # Get default config
    default_config = cfg.get_all_config()
    
    # Modify config
    cfg.set_config('backtest.initial_capital', 20000.0)
    cfg.set_config('strategies.trend_following.fast_ma_period', 10)
    
    # Get updated config
    updated_config = cfg.get_all_config()
    
    print(f"  ✅ Default initial capital: ${default_config['backtest']['initial_capital']}")
    print(f"  ✅ Updated initial capital: ${updated_config['backtest']['initial_capital']}")
    print(f"  ✅ Updated trend following fast MA period: {updated_config['strategies']['trend_following']['fast_ma_period']}")
    
    # Reset config
    cfg.reset_config()
    
    # Verify reset
    reset_config = cfg.get_all_config()
    print(f"  ✅ Reset initial capital: ${reset_config['backtest']['initial_capital']}")
    
    return default_config, updated_config, reset_config

def run_all_tests():
    """Run all system tests."""
    print("\n🔍 RUNNING SYSTEM TESTS\n" + "="*50)
    
    try:
        # Test data loading
        data = test_data_loader()
        
        # Test indicators
        data_with_indicators = test_indicators(data)
        
        # Test strategies
        strategy_results = test_strategies(data_with_indicators)
        
        # Test backtesting
        backtest_results = test_backtesting(data_with_indicators)
        
        # Test optimization (simplified for testing)
        test_data_small = data_with_indicators.tail(100)  # Use smaller dataset for optimization
        optimization_results = test_optimization(test_data_small)
        
        # Test configuration
        config_results = test_config()
        
        print("\n" + "="*50)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        print("\n" + "="*50)
        print("❌ TESTS FAILED")
        print("="*50)

if __name__ == "__main__":
    run_all_tests() 