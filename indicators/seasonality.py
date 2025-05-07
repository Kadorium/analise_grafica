import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Union, Tuple
import calendar
from matplotlib.figure import Figure

def calculate_returns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate daily returns from close prices.
    
    Args:
        df: DataFrame with 'date' and 'close' columns
        
    Returns:
        DataFrame with added 'returns' column
    """
    # Make a copy to avoid modifying the original
    data = df.copy()
    
    # Ensure date is datetime type
    if not pd.api.types.is_datetime64_any_dtype(data['date']):
        data['date'] = pd.to_datetime(data['date'])
    
    # Sort by date
    data = data.sort_values('date')
    
    # Calculate daily returns
    data['returns'] = data['close'].pct_change() * 100
    
    return data

def day_of_week_returns(df: pd.DataFrame, plot: bool = False) -> Union[pd.DataFrame, Tuple[pd.DataFrame, Figure]]:
    """
    Calculate average return by day of the week.
    
    Args:
        df: DataFrame with 'date' and 'close' columns
        plot: Whether to generate a plot
        
    Returns:
        DataFrame with average returns by day of week or tuple of (DataFrame, Figure)
    """
    # Calculate returns
    data = calculate_returns(df)
    
    # Extract day of week
    data['day_of_week'] = data['date'].dt.day_name()
    
    # Group by day of week
    dow_returns = data.groupby('day_of_week')['returns'].agg(['mean', 'std', 'count']).reset_index()
    
    # Order days of week correctly
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    dow_returns['day_of_week'] = pd.Categorical(dow_returns['day_of_week'], categories=days_order, ordered=True)
    dow_returns = dow_returns.sort_values('day_of_week')
    
    if plot:
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(dow_returns['day_of_week'], dow_returns['mean'], yerr=dow_returns['std']/np.sqrt(dow_returns['count']),
                     alpha=0.7, capsize=5)
        
        # Add a horizontal line at y=0
        ax.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
        
        # Color positive and negative bars differently
        for i, bar in enumerate(bars):
            if dow_returns['mean'].iloc[i] < 0:
                bar.set_color('r')
            else:
                bar.set_color('g')
        
        ax.set_title('Average Return by Day of Week')
        ax.set_ylabel('Average Return (%)')
        ax.set_xlabel('Day of Week')
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        return dow_returns, fig
    
    return dow_returns

def monthly_returns(df: pd.DataFrame, plot: bool = False) -> Union[pd.DataFrame, Tuple[pd.DataFrame, Figure]]:
    """
    Calculate average return by month of the year.
    
    Args:
        df: DataFrame with 'date' and 'close' columns
        plot: Whether to generate a plot
        
    Returns:
        DataFrame with average returns by month or tuple of (DataFrame, Figure)
    """
    # Calculate returns
    data = calculate_returns(df)
    
    # Extract month
    data['month'] = data['date'].dt.month
    data['month_name'] = data['date'].dt.month_name()
    
    # Group by month
    monthly_returns = data.groupby(['month', 'month_name'])['returns'].agg(['mean', 'std', 'count']).reset_index()
    
    # Sort by month
    monthly_returns = monthly_returns.sort_values('month')
    
    if plot:
        fig, ax = plt.subplots(figsize=(12, 6))
        bars = ax.bar(monthly_returns['month_name'], monthly_returns['mean'], 
                     yerr=monthly_returns['std']/np.sqrt(monthly_returns['count']),
                     alpha=0.7, capsize=5)
        
        # Add a horizontal line at y=0
        ax.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
        
        # Color positive and negative bars differently
        for i, bar in enumerate(bars):
            if monthly_returns['mean'].iloc[i] < 0:
                bar.set_color('r')
            else:
                bar.set_color('g')
        
        ax.set_title('Average Return by Month')
        ax.set_ylabel('Average Return (%)')
        ax.set_xlabel('Month')
        ax.grid(axis='y', alpha=0.3)
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        return monthly_returns, fig
    
    return monthly_returns

def day_of_week_volatility(df: pd.DataFrame, plot: bool = False) -> Union[pd.DataFrame, Tuple[pd.DataFrame, Figure]]:
    """
    Calculate average volatility by day of the week.
    
    Args:
        df: DataFrame with 'date' and 'close' columns
        plot: Whether to generate a plot
        
    Returns:
        DataFrame with average volatility by day of week or tuple of (DataFrame, Figure)
    """
    # Calculate returns
    data = calculate_returns(df)
    
    # Calculate daily volatility (absolute value of returns)
    data['volatility'] = data['returns'].abs()
    
    # Extract day of week
    data['day_of_week'] = data['date'].dt.day_name()
    
    # Group by day of week
    dow_volatility = data.groupby('day_of_week')['volatility'].agg(['mean', 'std', 'count']).reset_index()
    
    # Order days of week correctly
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    dow_volatility['day_of_week'] = pd.Categorical(dow_volatility['day_of_week'], categories=days_order, ordered=True)
    dow_volatility = dow_volatility.sort_values('day_of_week')
    
    if plot:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar(dow_volatility['day_of_week'], dow_volatility['mean'], 
               yerr=dow_volatility['std']/np.sqrt(dow_volatility['count']),
               alpha=0.7, capsize=5, color='purple')
        
        ax.set_title('Average Volatility by Day of Week')
        ax.set_ylabel('Average Volatility (Absolute Returns %)')
        ax.set_xlabel('Day of Week')
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        return dow_volatility, fig
    
    return dow_volatility

def calendar_heatmap(df: pd.DataFrame) -> Figure:
    """
    Generate a heatmap of returns by calendar day.
    
    Args:
        df: DataFrame with 'date' and 'close' columns
        
    Returns:
        Matplotlib Figure object
    """
    # Calculate returns
    data = calculate_returns(df)
    
    # Extract components
    data['year'] = data['date'].dt.year
    data['month'] = data['date'].dt.month
    data['day'] = data['date'].dt.day
    
    # Find min and max years
    min_year = data['year'].min()
    max_year = data['year'].max()
    
    # If we have more than 2 years of data, create a pivot table by month/day
    # ignoring the year to see seasonal patterns
    if max_year - min_year > 2:
        # Group by month and day
        calendar_data = data.groupby(['month', 'day'])['returns'].mean().reset_index()
        
        # Create pivot table: month vs day
        pivot_data = calendar_data.pivot(index='month', columns='day', values='returns')
        
        title = 'Average Daily Returns by Calendar Day'
    else:
        # For shorter timeframes, include the year to see specific dates
        calendar_data = data.pivot_table(
            index='month', 
            columns='day', 
            values='returns', 
            aggfunc='mean'
        )
        
        pivot_data = calendar_data
        title = f'Daily Returns Heatmap ({min_year}-{max_year})'
    
    # Create the heatmap
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Create a colormap that's red for negative, white for zero, green for positive
    cmap = sns.diverging_palette(10, 120, as_cmap=True)
    
    # Calculate the abs maximum for symmetric color scaling
    vmax = max(abs(pivot_data.min().min()), abs(pivot_data.max().max()))
    
    # Generate the heatmap
    sns.heatmap(pivot_data, 
                cmap=cmap, 
                center=0, 
                annot=False, 
                fmt=".2f", 
                linewidths=.5, 
                ax=ax,
                vmin=-vmax,
                vmax=vmax,
                cbar_kws={'label': 'Return (%)'}
               )
    
    # Set the month names
    month_names = [calendar.month_name[i] for i in range(1, 13)]
    ax.set_yticklabels(month_names, rotation=0)
    
    ax.set_title(title)
    ax.set_xlabel('Day of Month')
    ax.set_ylabel('Month')
    
    plt.tight_layout()
    return fig

def seasonality_summary(df: pd.DataFrame) -> Tuple[Figure, dict]:
    """
    Generate a comprehensive seasonality analysis with multiple plots.
    
    Args:
        df: DataFrame with 'date' and 'close' columns
        
    Returns:
        Tuple containing (Figure, results_dict)
    """
    # Ensure date is datetime
    data = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(data['date']):
        data['date'] = pd.to_datetime(data['date'])
    
    # Create a combined figure with multiple subplots
    fig = plt.figure(figsize=(15, 15))
    
    # Get individual results
    dow_ret, _ = day_of_week_returns(data, plot=True)
    month_ret, _ = monthly_returns(data, plot=True)
    dow_vol, _ = day_of_week_volatility(data, plot=True)
    
    # Day of week returns
    ax1 = plt.subplot(2, 2, 1)
    bars = ax1.bar(dow_ret['day_of_week'], dow_ret['mean'], alpha=0.7)
    # Color by positive/negative
    for i, bar in enumerate(bars):
        if dow_ret['mean'].iloc[i] < 0:
            bar.set_color('r')
        else:
            bar.set_color('g')
    ax1.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
    ax1.set_title('Average Return by Day of Week')
    ax1.set_ylabel('Average Return (%)')
    
    # Monthly returns
    ax2 = plt.subplot(2, 2, 2)
    bars = ax2.bar(month_ret['month_name'], month_ret['mean'], alpha=0.7)
    # Color by positive/negative
    for i, bar in enumerate(bars):
        if month_ret['mean'].iloc[i] < 0:
            bar.set_color('r')
        else:
            bar.set_color('g')
    ax2.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
    ax2.set_title('Average Return by Month')
    ax2.set_ylabel('Average Return (%)')
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
    
    # Day of week volatility
    ax3 = plt.subplot(2, 2, 3)
    ax3.bar(dow_vol['day_of_week'], dow_vol['mean'], alpha=0.7, color='purple')
    ax3.set_title('Average Volatility by Day of Week')
    ax3.set_ylabel('Average Volatility (%)')
    
    # Calendar heatmap in a smaller subplot
    ax4 = plt.subplot(2, 2, 4)
    
    # Calculate returns
    data = calculate_returns(data)
    
    # Extract components
    data['year'] = data['date'].dt.year
    data['month'] = data['date'].dt.month
    data['day'] = data['date'].dt.day
    
    # Group by month and day
    calendar_data = data.groupby(['month', 'day'])['returns'].mean().reset_index()
    
    # Create pivot table: month vs day
    pivot_data = calendar_data.pivot(index='month', columns='day', values='returns')
    
    # Create a colormap that's red for negative, white for zero, green for positive
    cmap = sns.diverging_palette(10, 120, as_cmap=True)
    
    # Calculate the abs maximum for symmetric color scaling
    vmax = max(abs(pivot_data.min().min()), abs(pivot_data.max().max()))
    
    # Generate the heatmap
    sns.heatmap(pivot_data, 
                cmap=cmap, 
                center=0, 
                annot=False, 
                fmt=".2f", 
                linewidths=.5, 
                ax=ax4,
                vmin=-vmax,
                vmax=vmax,
                cbar_kws={'label': 'Return (%)'}
               )
    
    # Set the month names
    month_names = [calendar.month_name[i] for i in range(1, 13)]
    ax4.set_yticklabels(month_names, rotation=0)
    
    ax4.set_title('Returns by Calendar Day')
    ax4.set_xlabel('Day of Month')
    ax4.set_ylabel('Month')
    
    plt.tight_layout()
    
    # Compile results dictionary
    results = {
        'day_of_week_returns': dow_ret.to_dict('records'),
        'monthly_returns': month_ret.to_dict('records'),
        'day_of_week_volatility': dow_vol.to_dict('records'),
    }
    
    return fig, results 