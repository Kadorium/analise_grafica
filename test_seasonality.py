import pandas as pd
import numpy as np
import strategies.seasonality_strategy as ss
from indicators.seasonality import day_of_week_returns, monthly_returns

# Create test data with a strong Monday pattern (3 years of data)
print("Creating test data with strong seasonal patterns...")
df = pd.DataFrame({
    'date': pd.date_range('2020-01-01', periods=365*3),
    'open': np.random.rand(365*3),
    'high': np.random.rand(365*3),
    'low': np.random.rand(365*3),
    'close': np.random.rand(365*3),
    'volume': np.random.rand(365*3)
})

# Make returns more consistent with less randomness
for i in range(1, len(df)):
    df.loc[i, 'close'] = df.loc[i-1, 'close'] * (1 + np.random.normal(0, 0.005))  # Base 0.5% daily volatility

# Add STRONG seasonal patterns:
# Monday returns are significantly positive (+1%), Friday returns are significantly negative (-1%)
for i in range(1, len(df)):
    if df.loc[i, 'date'].dayofweek == 0:  # Monday
        df.loc[i, 'close'] = df.loc[i-1, 'close'] * 1.01  # 1% increase
    elif df.loc[i, 'date'].dayofweek == 4:  # Friday
        df.loc[i, 'close'] = df.loc[i-1, 'close'] * 0.99  # 1% decrease

# January returns are significantly positive (+2%), October returns are significantly negative (-2%)
for i in range(1, len(df)):
    if df.loc[i, 'date'].month == 1:  # January
        df.loc[i, 'close'] = df.loc[i, 'close'] * 1.02  # Additional 2% boost
    elif df.loc[i, 'date'].month == 10:  # October
        df.loc[i, 'close'] = df.loc[i, 'close'] * 0.98  # Additional 2% reduction

# First run the seasonality analysis directly
print("\nChecking day of week returns analysis...")
dow_returns_df = day_of_week_returns(df, plot=False)
print(dow_returns_df[['day_of_week', 'mean']])

print("\nChecking monthly returns analysis...")
monthly_returns_df = monthly_returns(df, plot=False)
print(monthly_returns_df[['month', 'month_name', 'mean']])

# Now test the strategy with auto-optimization
print("\nRunning seasonality strategy with auto-optimization...")
# Lower thresholds to catch more patterns
result = ss.generate_signals(df, auto_optimize=True, significance_threshold=0.2, return_threshold=0.05)

# Count signals by day of week and month
print("\nBuy signals by day of week:")
buy_by_dow = result[result['signal'] == 'buy'].groupby('day_of_week').size()
print(buy_by_dow)

print("\nSell signals by day of week:")
sell_by_dow = result[result['signal'] == 'sell'].groupby('day_of_week').size() 
print(sell_by_dow)

print("\nBuy signals by month:")
buy_by_month = result[result['signal'] == 'buy'].groupby('month').size()
print(buy_by_month)

print("\nSell signals by month:")
sell_by_month = result[result['signal'] == 'sell'].groupby('month').size()
print(sell_by_month)

# Check if the strategy correctly identified the pattern
print("\nPattern Detection Results:")
if 0 in buy_by_dow.index:
    print("✓ Successfully detected Monday as a buy day")
else:
    print("✗ Failed to detect Monday as a buy day")
    
if 4 in sell_by_dow.index:
    print("✓ Successfully detected Friday as a sell day")
else:
    print("✗ Failed to detect Friday as a sell day")
    
if 1 in buy_by_month.index:
    print("✓ Successfully detected January as a buy month")
else:
    print("✗ Failed to detect January as a buy month")
    
if 10 in sell_by_month.index:
    print("✓ Successfully detected October as a sell month")
else:
    print("✗ Failed to detect October as a sell month")

# Calculate actual returns
print("\nVerifying the strategy performance...")
signals = result.copy()
position = 0
capital = 1000.0
signals['equity'] = capital
trade_count = 0
profitable_trades = 0

for i in range(1, len(signals)):
    if signals.iloc[i-1]['signal'] == 'buy' and position == 0:
        position = 1
        trade_count += 1
        entry_price = signals.iloc[i-1]['close']
    elif signals.iloc[i-1]['signal'] == 'sell' and position == 1:
        position = 0
        exit_price = signals.iloc[i-1]['close']
        return_pct = (exit_price / entry_price) - 1
        if return_pct > 0:
            profitable_trades += 1
        capital *= (1 + return_pct)
    signals.iloc[i, signals.columns.get_loc('equity')] = capital

print(f"Final capital: ${signals['equity'].iloc[-1]:.2f}")
print(f"Total return: {(signals['equity'].iloc[-1] / signals['equity'].iloc[0] - 1) * 100:.2f}%")
print(f"Total trades: {trade_count}")
if trade_count > 0:
    print(f"Profitable trades: {profitable_trades} ({profitable_trades/trade_count*100:.1f}%)") 