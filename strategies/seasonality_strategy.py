import pandas as pd
import numpy as np
from indicators.seasonality import day_of_week_returns, monthly_returns

def generate_signals(data, 
                    auto_optimize=True,
                    significance_threshold=0.6,
                    return_threshold=0.1,
                    day_of_week_filter=None, 
                    month_of_year_filter=None, 
                    day_of_month_filter=None, 
                    exit_after_days=3,
                    combined_seasonality=False):
    """
    Generate trading signals based on seasonality patterns. When auto_optimize is True,
    it will analyze historical data to determine the best days/months to trade.
    
    Args:
        data (pd.DataFrame): Price data with 'date', 'open', 'high', 'low', 'close', 'volume' columns
        auto_optimize (bool): If True, automatically determine best days/months to trade based on historical analysis
        significance_threshold (float): Minimum significance level (0-1) for considering a pattern valid
        return_threshold (float): Minimum average return percentage for considering a pattern valid
        day_of_week_filter (list, optional): List of days to enter positions (0-6, where 0 is Monday)
        month_of_year_filter (list, optional): List of months to enter positions (1-12)
        day_of_month_filter (list, optional): List of days of month to enter positions (1-31)
        exit_after_days (int, optional): Exit position after specified number of days (regardless of other factors)
        combined_seasonality (bool, optional): If True, requires all specified seasonality conditions to be met
                                             If False, any specified seasonality condition being met will generate a signal
    
    Returns:
        pd.DataFrame: DataFrame with 'signal' column ('buy', 'sell', 'hold')
    """
    signals = data.copy()
    
    # Create a dictionary to store the actual parameters used
    # This will be attached to the result dataframe
    actual_params = {
        'auto_optimize': auto_optimize,
        'significance_threshold': significance_threshold,
        'return_threshold': return_threshold,
        'day_of_week_filter': day_of_week_filter,
        'month_of_year_filter': month_of_year_filter,
        'day_of_month_filter': day_of_month_filter,
        'exit_after_days': exit_after_days,
        'combined_seasonality': combined_seasonality
    }
    
    # Ensure date is datetime type
    if not pd.api.types.is_datetime64_any_dtype(signals['date']):
        signals['date'] = pd.to_datetime(signals['date'])
    
    # Extract date components
    signals['day_of_week'] = signals['date'].dt.dayofweek  # 0 is Monday, 6 is Sunday
    signals['month'] = signals['date'].dt.month  # 1-12
    signals['day_of_month'] = signals['date'].dt.day  # 1-31
    
    # Initialize signal column
    signals['signal'] = 'hold'
    
    # If auto_optimize is True, analyze historical data to determine optimal parameters
    if auto_optimize:
        # Run historical analysis on day of week returns
        dow_returns_df = day_of_week_returns(data, plot=False)
        
        # Run historical analysis on monthly returns
        monthly_returns_df = monthly_returns(data, plot=False)
        
        # Define positive/negative thresholds for days of week (using absolute value for negative days)
        positive_dow = []
        negative_dow = []
        
        for _, row in dow_returns_df.iterrows():
            # Convert day name to index (0=Monday, 6=Sunday)
            day_name = row['day_of_week']
            day_mapping = {'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3, 'Friday': 4, 'Saturday': 5, 'Sunday': 6}
            day_index = day_mapping.get(day_name, 0)
            
            # Extract mean and standard error
            mean_return = row['mean']
            count = row['count']
            std_dev = row['std']
            std_error = std_dev / np.sqrt(count) if count > 0 else 0
            
            # Calculate a crude significance measure (mean / standard error if available)
            significance = abs(mean_return) / std_error if std_error > 0 else 0
            
            # Add days with good positive returns to positive list
            if mean_return > return_threshold and significance > significance_threshold:
                positive_dow.append(day_index)
            
            # Add days with bad negative returns to negative list
            elif mean_return < -return_threshold and significance > significance_threshold:
                negative_dow.append(day_index)
        
        # Define positive/negative thresholds for months
        positive_months = []
        negative_months = []
        
        for _, row in monthly_returns_df.iterrows():
            # Get month index (1-12)
            month_index = row['month']
            
            # Extract mean and standard error
            mean_return = row['mean']
            count = row['count']
            std_dev = row['std']
            std_error = std_dev / np.sqrt(count) if count > 0 else 0
            
            # Calculate a crude significance measure
            significance = abs(mean_return) / std_error if std_error > 0 else 0
            
            # Add months with good positive returns to positive list
            if mean_return > return_threshold and significance > significance_threshold:
                positive_months.append(month_index)
            
            # Add months with bad negative returns to negative list
            elif mean_return < -return_threshold and significance > significance_threshold:
                negative_months.append(month_index)
        
        # Override the provided filters with auto-optimized values
        actual_day_of_week_filter = positive_dow if positive_dow else day_of_week_filter
        actual_month_of_year_filter = positive_months if positive_months else month_of_year_filter
        
        # Override the actual parameters dictionary
        actual_params['day_of_week_filter'] = actual_day_of_week_filter
        actual_params['month_of_year_filter'] = actual_month_of_year_filter
        
        # Add information about the negative filters 
        actual_params['negative_day_of_week'] = negative_dow
        actual_params['negative_month_of_year'] = negative_months
        
        # Also add summary of analysis for better transparency
        day_name_mapping = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
        month_name_mapping = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June', 
                             7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December'}
        
        # Convert numerical days/months to names for better readability
        actual_params['positive_days'] = [day_name_mapping.get(day, str(day)) for day in positive_dow]
        actual_params['negative_days'] = [day_name_mapping.get(day, str(day)) for day in negative_dow]
        actual_params['positive_months'] = [month_name_mapping.get(month, str(month)) for month in positive_months]
        actual_params['negative_months'] = [month_name_mapping.get(month, str(month)) for month in negative_months]
        
        # Store the analyzed negative periods for potential short signals
        negative_day_of_week = negative_dow
        negative_month_of_year = negative_months
        
        # Print diagnostic information
        print(f"Auto-optimized Seasonality Strategy Parameters:")
        print(f"- Positive days of week: {actual_day_of_week_filter}")
        print(f"- Negative days of week: {negative_day_of_week}")
        print(f"- Positive months: {actual_month_of_year_filter}")
        print(f"- Negative months: {negative_month_of_year}")
        
        # Use the actual optimized values for signal generation
        day_of_week_filter = actual_day_of_week_filter
        month_of_year_filter = actual_month_of_year_filter
    
    # Handle case where no filters are provided (default to no signals)
    if day_of_week_filter is None and month_of_year_filter is None and day_of_month_filter is None:
        # Attach the actual parameters to the result DataFrame as an attribute
        signals.attrs['seasonality_params'] = actual_params
        return signals
    
    # Create condition masks for each seasonality factor
    dow_condition = True
    month_condition = True
    dom_condition = True
    
    # Create day of week filter condition
    if day_of_week_filter is not None:
        dow_condition = signals['day_of_week'].isin(day_of_week_filter)
    
    # Create month filter condition  
    if month_of_year_filter is not None:
        month_condition = signals['month'].isin(month_of_year_filter)
    
    # Create day of month filter condition
    if day_of_month_filter is not None:
        dom_condition = signals['day_of_month'].isin(day_of_month_filter)
    
    # Combine conditions based on strategy configuration
    if combined_seasonality:
        # All specified conditions must be met
        entry_condition = dow_condition & month_condition & dom_condition
    else:
        # Any specified condition can trigger a signal
        entry_condition = (
            (day_of_week_filter is not None and dow_condition) |
            (month_of_year_filter is not None and month_condition) |
            (day_of_month_filter is not None and dom_condition)
        )
    
    # Apply the condition
    signals.loc[entry_condition, 'signal'] = 'buy'
    
    # If auto_optimize is True, also add short signals based on negative seasonality
    if auto_optimize:
        # Create negative seasonality conditions
        neg_dow_condition = True
        neg_month_condition = True
        
        # Create negative day of week filter condition
        if negative_day_of_week:
            neg_dow_condition = signals['day_of_week'].isin(negative_day_of_week)
        else:
            neg_dow_condition = False
        
        # Create negative month filter condition  
        if negative_month_of_year:
            neg_month_condition = signals['month'].isin(negative_month_of_year)
        else:
            neg_month_condition = False
        
        # Combine negative conditions 
        negative_condition = neg_dow_condition | neg_month_condition
        
        # Only apply short signals where there isn't already a long signal
        short_condition = negative_condition & (signals['signal'] == 'hold')
        signals.loc[short_condition, 'signal'] = 'sell'
    
    # Handle exit after specified days
    if exit_after_days is not None and exit_after_days > 0:
        # For buy signals
        buy_indices = signals.index[signals['signal'] == 'buy'].tolist()
        for buy_index in buy_indices:
            if buy_index + exit_after_days < len(signals):
                # Only add 'sell' if we don't already have a signal there
                if signals.iloc[buy_index + exit_after_days]['signal'] == 'hold':
                    signals.at[signals.index[buy_index + exit_after_days], 'signal'] = 'sell'
        
        # For sell signals (short positions)
        short_indices = signals.index[signals['signal'] == 'sell'].tolist()
        for short_index in short_indices:
            if short_index + exit_after_days < len(signals):
                # Only add 'buy' (to close the short) if we don't already have a signal there
                if signals.iloc[short_index + exit_after_days]['signal'] == 'hold':
                    signals.at[signals.index[short_index + exit_after_days], 'signal'] = 'buy'
    else:
        # Default exit strategy: close the position when the pattern ends
        in_long_position = False
        in_short_position = False
        
        for i in range(1, len(signals)):
            if signals.iloc[i-1]['signal'] == 'buy':
                in_long_position = True
            elif signals.iloc[i-1]['signal'] == 'sell' and not in_long_position:
                in_short_position = True
            
            # Close long when the pattern ends (no longer in buy condition)
            if in_long_position and signals.iloc[i]['signal'] == 'hold':
                signals.at[signals.index[i], 'signal'] = 'sell'
                in_long_position = False
            
            # Close short when the pattern ends
            elif in_short_position and signals.iloc[i]['signal'] == 'hold':
                signals.at[signals.index[i], 'signal'] = 'buy'
                in_short_position = False
    
    # Add summary statistics to the result
    total_signals = len(signals[signals['signal'] != 'hold'])
    buy_signals = len(signals[signals['signal'] == 'buy'])
    sell_signals = len(signals[signals['signal'] == 'sell'])
    
    # Add some statistics to the parameters
    actual_params['total_signals'] = total_signals
    actual_params['buy_signals'] = buy_signals
    actual_params['sell_signals'] = sell_signals
    
    # Add high-level summary for easy display in UI
    if auto_optimize:
        summary = []
        if actual_params['positive_days']:
            summary.append(f"Buy on: {', '.join(actual_params['positive_days'])}")
        if actual_params['negative_days']:
            summary.append(f"Sell on: {', '.join(actual_params['negative_days'])}")
        if actual_params['positive_months']:
            summary.append(f"Buy in: {', '.join(actual_params['positive_months'])}")
        if actual_params['negative_months']:
            summary.append(f"Sell in: {', '.join(actual_params['negative_months'])}")
        
        actual_params['summary'] = summary
    
    # Attach the actual parameters to the result DataFrame as an attribute
    signals.attrs['seasonality_params'] = actual_params
    
    return signals 