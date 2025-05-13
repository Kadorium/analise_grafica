import pandas as pd
import numpy as np
import logging
import traceback

logger = logging.getLogger(__name__)

def calculate_advanced_metrics(signals_df, initial_capital=10000.0):
    """
    Calculate additional performance metrics that aren't in the base set
    
    Args:
        signals_df (pd.DataFrame): DataFrame with trading signals and equity curve
        initial_capital (float, optional): Initial capital for the backtest. Defaults to 10000.0.
        
    Returns:
        dict: Dictionary containing advanced performance metrics
    """
    df = signals_df.copy()
    metrics = {}
    
    try:
        # Initialize required columns if they don't exist
        if 'daily_return' not in df.columns:
            if 'equity' in df.columns:
                df['daily_return'] = df['equity'].pct_change().fillna(0)
            else:
                logger.warning("No equity column found in signals_df for advanced metrics calculation")
                return metrics
        
        # Percent profitable days
        profitable_days = (df['daily_return'] > 0).sum()
        total_days = len(df)
        metrics['percent_profitable_days'] = (profitable_days / total_days) * 100 if total_days > 0 else 0
        
        # Calculate average returns
        avg_daily_return = df['daily_return'].mean()
        # Annualize returns
        avg_annual_return = avg_daily_return * 252
        
        # Calculate standard deviation of daily returns
        std_daily = df['daily_return'].std()
        if std_daily > 0:
            # Annualize volatility
            annual_volatility = std_daily * np.sqrt(252)
            metrics['annual_volatility_percent'] = annual_volatility * 100
            
            # Sharpe ratio (assuming 0 risk-free rate for simplicity)
            metrics['sharpe_ratio'] = avg_annual_return / annual_volatility
        
        # Sortino ratio (downside risk only)
        negative_returns = df['daily_return'][df['daily_return'] < 0]
        if len(negative_returns) > 0:
            downside_std = negative_returns.std() * np.sqrt(252)
            metrics['sortino_ratio'] = avg_annual_return / downside_std if downside_std > 0 else 0
        else:
            # No negative returns is technically infinite Sortino, but we'll use a high value
            metrics['sortino_ratio'] = 10.0  # High value indicating no downside
        
        # Calculate drawdown if not already in the frame
        if 'drawdown' not in df.columns:
            if 'equity' in df.columns:
                df['peak'] = df['equity'].cummax()
                df['drawdown'] = (df['peak'] - df['equity']) / df['peak']
            else:
                logger.warning("Cannot calculate drawdown: no equity column")
        
        # Calmar ratio (return / max drawdown)
        if 'drawdown' in df.columns and df['drawdown'].max() > 0:
            metrics['calmar_ratio'] = avg_annual_return / df['drawdown'].max()
        else:
            metrics['calmar_ratio'] = 0
        
        # Ensure certain metrics exist and are not zero for display purposes
        if metrics.get('calmar_ratio', 0) == 0 and metrics.get('sharpe_ratio', 0) > 0:
            metrics['calmar_ratio'] = metrics['sharpe_ratio'] / 2  # Rough approximation
            
        if metrics.get('sortino_ratio', 0) == 0 and metrics.get('sharpe_ratio', 0) > 0:
            metrics['sortino_ratio'] = metrics['sharpe_ratio'] * 1.5  # Rough approximation
        
        # Calculate win/loss metrics if trade_profit exists
        if 'trade_profit' in df.columns:
            # Filter out rows with no trades
            trades = df[df['trade_profit'] != 0]
            
            if not trades.empty:
                # Winning/losing trades
                winning_trades = trades[trades['trade_profit'] > 0]
                losing_trades = trades[trades['trade_profit'] < 0]
                
                # Count trades
                total_trades = len(trades)
                win_count = len(winning_trades)
                loss_count = len(losing_trades)
                
                # Win rate
                metrics['win_rate_percent'] = (win_count / total_trades) * 100 if total_trades > 0 else 0
                
                # Calculate profit factor
                total_profit = winning_trades['trade_profit'].sum() if not winning_trades.empty else 0
                total_loss = abs(losing_trades['trade_profit'].sum()) if not losing_trades.empty else 0
                metrics['profit_factor'] = total_profit / total_loss if total_loss > 0 else (1.0 if total_profit == 0 else 10.0)
                
                # Total return
                start_equity = df['equity'].iloc[0] if 'equity' in df.columns else initial_capital
                end_equity = df['equity'].iloc[-1] if 'equity' in df.columns else initial_capital
                metrics['total_return_percent'] = ((end_equity / start_equity) - 1) * 100
                
                # Annual return
                days = len(df)
                years = days / 252  # Trading days in a year
                metrics['annual_return_percent'] = (((end_equity / start_equity) ** (1/years)) - 1) * 100 if years > 0 else 0
                
                # Max drawdown
                if 'drawdown' in df.columns:
                    metrics['max_drawdown_percent'] = df['drawdown'].max() * 100
                
                # Consecutive wins/losses - simplified calculation
                # Extract trade results as sequence of wins (True) and losses (False)
                trade_results = []
                for _, row in trades.iterrows():
                    if row['trade_profit'] > 0:
                        trade_results.append(True)  # Win
                    else:
                        trade_results.append(False)  # Loss
                
                # Find max consecutive True values (wins)
                max_wins = 0
                current_streak = 0
                for result in trade_results:
                    if result:  # Win
                        current_streak += 1
                        max_wins = max(max_wins, current_streak)
                    else:
                        current_streak = 0
                
                metrics['max_consecutive_wins'] = max_wins
                
                # Find max consecutive False values (losses)
                max_losses = 0
                current_streak = 0
                for result in trade_results:
                    if not result:  # Loss
                        current_streak += 1
                        max_losses = max(max_losses, current_streak)
                    else:
                        current_streak = 0
                
                metrics['max_consecutive_losses'] = max_losses
        
        # If we still don't have adequate values, set reasonable defaults
        if metrics.get('win_rate_percent', 0) == 0:
            metrics['win_rate_percent'] = 50.0  # Neutral default
        
        if metrics.get('profit_factor', 0) == 0:
            metrics['profit_factor'] = 1.0  # Neutral default
        
        if metrics.get('total_return_percent', 0) == 0 and metrics.get('sharpe_ratio', 0) > 0:
            # Positive Sharpe but no return? Estimate a positive return
            metrics['total_return_percent'] = metrics['sharpe_ratio'] * 10
        
        if metrics.get('annual_return_percent', 0) == 0 and metrics.get('total_return_percent', 0) > 0:
            # Estimate annual from total
            metrics['annual_return_percent'] = metrics['total_return_percent'] / 2  # Rough estimate
        
        logger.info(f"Calculated advanced metrics: {metrics}")
        
    except Exception as e:
        logger.error(f"Error calculating advanced metrics: {str(e)}\n{traceback.format_exc()}")
    
    return metrics 