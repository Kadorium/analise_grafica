import pandas as pd
import numpy as np
import logging
import traceback

logger = logging.getLogger(__name__)

def calculate_advanced_metrics(signals_df, initial_capital=10000.0, base_metrics=None):
    """
    Calculate additional performance metrics using the signals DataFrame and base metrics.
    
    Args:
        signals_df (pd.DataFrame): DataFrame with trading signals and equity curve.
                                   Should contain 'date', 'equity', 'daily_return', 'trade_profit'.
        initial_capital (float, optional): Initial capital for the backtest. Defaults to 10000.0.
        base_metrics (dict, optional): Dictionary of pre-calculated base metrics from StrategyAdapter.
                                       Expected keys: 'annual_return' (raw ratio), 'max_drawdown' (raw ratio).
        
    Returns:
        tuple: (dict: Dictionary containing advanced metrics, list: List of debug log strings)
    """
    df = signals_df.copy() # df is the signals_df from StrategyAdapter.backtest
    advanced_metrics = {}
    debug_logs = [] # Initialize list to collect debug logs

    if base_metrics is None:
        base_metrics = {}

    try:
        # Ensure 'date' column is datetime
        if 'date' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['date']):
            df['date'] = pd.to_datetime(df['date'])

        # Ensure 'daily_return' is present and calculated if missing
        if 'daily_return' not in df.columns or df['daily_return'].isnull().all():
            if 'equity' in df.columns and not df.empty:
                df['daily_return'] = df['equity'].pct_change().fillna(0)
            else: # Fallback if equity is also missing or empty
                logger.warning("Cannot calculate daily_return for advanced metrics; equity data missing or empty.")
                df['daily_return'] = pd.Series([0.0] * len(df))
        
        # 1. Profitable Days (%)
        profitable_days_count = (df['daily_return'] > 0).sum()
        total_trading_days = len(df['daily_return'])
        # Return as a ratio; frontend will multiply by 100. Key changed to match frontend.
        advanced_metrics['percent_profitable_days'] = (profitable_days_count / total_trading_days) if total_trading_days > 0 else 0.0
        
        # 2. Annualized Volatility (%)
        annual_volatility = 0.0
        if not df['daily_return'].empty:
            std_daily_return = df['daily_return'].std()
            if std_daily_return is not None and std_daily_return > 0:
                annual_volatility = std_daily_return * np.sqrt(252) # Assuming 252 trading days
        advanced_metrics['annual_volatility_percent'] = annual_volatility * 100

        # Dependencies from base_metrics
        # Use raw annual_return (ratio), not percentage
        avg_annual_return_ratio = base_metrics.get('annual_return', 0.0) 
        # Use raw max_drawdown (ratio, should be positive or zero from StrategyAdapter), not percentage
        max_drawdown_ratio = base_metrics.get('max_drawdown', 0.0) 

        # 3. Sortino Ratio
        sortino_ratio = 0.0
        if not df['daily_return'].empty:
            negative_returns = df['daily_return'][df['daily_return'] < 0]
            if not negative_returns.empty:
                downside_std_daily = negative_returns.std()
                if downside_std_daily is not None and downside_std_daily > 0:
                    downside_std_annual = downside_std_daily * np.sqrt(252)
                    if downside_std_annual > 0:
                        sortino_ratio = avg_annual_return_ratio / downside_std_annual
            elif avg_annual_return_ratio > 0: # No negative returns and positive annual return
                sortino_ratio = 100.0  # High value indicating excellent risk/reward (no downside risk)
        advanced_metrics['sortino_ratio'] = sortino_ratio
        
        # 4. Calmar Ratio
        # max_drawdown_ratio from base_metrics is now expected to be positive or zero.
        calmar_ratio = 0.0
        if max_drawdown_ratio > 0:
            calmar_ratio = avg_annual_return_ratio / max_drawdown_ratio
        elif avg_annual_return_ratio > 0:  # max_drawdown_ratio is 0, and annual return is positive
            calmar_ratio = 1e9  # Represent infinite Calmar with a large number
        else: # max_drawdown_ratio is 0 and annual return is <= 0
            calmar_ratio = 0.0
        advanced_metrics['calmar_ratio'] = calmar_ratio
        
        # 5. Max Consecutive Wins & Losses
        max_consecutive_wins = 0
        max_consecutive_losses = 0
        if 'trade_profit' in df.columns:
            trade_profit_series = pd.to_numeric(df['trade_profit'], errors='coerce').fillna(0)
            actual_trades = trade_profit_series[trade_profit_series != 0]
            # --- Debug Logging for Consecutive Wins/Losses ---
            debug_logs.append("\n[DEBUG] calculate_advanced_metrics - Consecutive Wins/Losses")
            debug_logs.append(f"[DEBUG] trade_profit_series (first 5 for consecutive calc):\n{trade_profit_series.head()}")
            debug_logs.append(f"[DEBUG] actual_trades (non-zero profit) for consecutive calc (first 5):\n{actual_trades.head()}")
            debug_logs.append(f"[DEBUG] Number of actual_trades for streak calc: {len(actual_trades)}")
            # --- End Debug Logging ---
            if not actual_trades.empty:
                trade_results_bool = actual_trades > 0 # True for win, False for loss
                # --- Debug Logging for Consecutive Wins/Losses ---
                debug_logs.append(f"[DEBUG] trade_results_bool (first 5):\n{trade_results_bool.head()}")
                # --- End Debug Logging ---
                
                current_win_streak = 0
                current_loss_streak = 0
                for i, is_win in enumerate(trade_results_bool):
                    if is_win:
                        current_win_streak += 1
                        max_consecutive_losses = max(max_consecutive_losses, current_loss_streak)
                        current_loss_streak = 0
                    else: # Is Loss
                        current_loss_streak += 1
                        max_consecutive_wins = max(max_consecutive_wins, current_win_streak)
                        current_win_streak = 0
                    # --- Debug Logging for Consecutive Wins/Losses ---
                    if i < 5 or i > len(trade_results_bool) - 5: # Log first 5 and last 5 iterations
                        debug_logs.append(f"[DEBUG] Streak loop iter {i}: is_win={is_win}, cur_W={current_win_streak}, cur_L={current_loss_streak}, max_W={max_consecutive_wins}, max_L={max_consecutive_losses}")
                    # --- End Debug Logging ---
                # Final check for streaks ending at the last trade
                max_consecutive_wins = max(max_consecutive_wins, current_win_streak)
                max_consecutive_losses = max(max_consecutive_losses, current_loss_streak)
                # --- Debug Logging for Consecutive Wins/Losses ---
                debug_logs.append(f"[DEBUG] Final streaks: max_W={max_consecutive_wins}, max_L={max_consecutive_losses}")
                # --- End Debug Logging ---
        
        advanced_metrics['max_consecutive_wins'] = max_consecutive_wins
        advanced_metrics['max_consecutive_losses'] = max_consecutive_losses

        logger.info(f"Calculated advanced metrics (to be merged): {advanced_metrics}")
        debug_logs.append(f"[INFO] Calculated advanced metrics (to be merged): {advanced_metrics}") # Also add logger info to debug list
        
    except Exception as e:
        error_message = f"Error calculating advanced metrics: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_message)
        debug_logs.append(f"[ERROR] {error_message}") # Add error to debug list
        # Return empty or partially filled dict on error to avoid breaking the flow
        # Ensure all expected keys are present, even if with default error values (e.g., 0 or None)
        default_error_metrics = {
            'percent_profitable_days': 0.0,
            'annual_volatility_percent': 0.0,
            'sortino_ratio': 0.0,
            'calmar_ratio': 0.0,
            'max_consecutive_wins': 0,
            'max_consecutive_losses': 0
        }
        for key in default_error_metrics:
            if key not in advanced_metrics:
                advanced_metrics[key] = default_error_metrics[key]
    
    return advanced_metrics, debug_logs # Return metrics and debug logs

# Example usage
# advanced_metrics, debug_logs = calculate_advanced_metrics(signals_df)
# print("Advanced Metrics:", advanced_metrics)
# print("Debug Logs:", debug_logs) 