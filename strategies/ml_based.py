import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import logging

# Add indicators we need
from indicators.momentum import relative_strength_index, macd
from indicators.volatility import bollinger_bands
from indicators.moving_averages import simple_moving_average

# Create a logger for this module
logger = logging.getLogger("ml-strategy")

class MLBasedStrategy:
    """
    A machine learning based strategy that uses technical indicators to predict price direction and generate signals.
    
    This strategy:
    1. Uses technical indicators (RSI, SMA, MACD, Bollinger Bands) as features
    2. Trains a classifier to predict next-day price direction (up/down)
    3. Generates buy/sell signals based on the predictions
    
    By default, it uses a Random Forest classifier, but Logistic Regression is also available.
    """
    
    def __init__(self, model_type='random_forest', training_size=0.7, predict_n_days=1, 
                 threshold=0.55, rsi_period=14, sma_period=20, bbands_period=20):
        """
        Initialize the ML-based strategy.
        
        Args:
            model_type (str): Type of ML model to use ('random_forest' or 'logistic_regression')
            training_size (float): Proportion of data to use for training (0.0-1.0)
            predict_n_days (int): Number of days ahead to predict
            threshold (float): Probability threshold for generating signals (0.5-1.0)
            rsi_period (int): Period for RSI calculation
            sma_period (int): Period for SMA calculation
            bbands_period (int): Period for Bollinger Bands calculation
        """
        self.model_type = model_type
        self.training_size = training_size
        self.predict_n_days = predict_n_days
        self.threshold = threshold
        self.rsi_period = rsi_period
        self.sma_period = sma_period
        self.bbands_period = bbands_period
        
        # Initialize model as None (will be trained later)
        self.model = None
        self.scaler = StandardScaler()
        
        # Set name based on model type
        model_name = "Random Forest" if model_type == 'random_forest' else "Logistic Regression"
        self.name = f"ML Strategy ({model_name})"
    
    def prepare_data(self, data):
        """
        Add necessary indicators to the data and prepare it for the ML model.
        
        Args:
            data (pandas.DataFrame): DataFrame containing the price data.
            
        Returns:
            pandas.DataFrame: DataFrame with added indicators.
        """
        # Make a copy to avoid modifying the original data
        result = data.copy()
        
        # Add technical indicators
        result['rsi_14'] = relative_strength_index(result, period=self.rsi_period)
        result[f'sma_{self.sma_period}'] = simple_moving_average(result, window=self.sma_period)
        
        # Add MACD
        macd_result = macd(result)
        result['macd'] = macd_result['macd']
        result['macd_signal'] = macd_result['signal']
        result['macd_histogram'] = macd_result['histogram']
        
        # Add Bollinger Bands
        bb_result = bollinger_bands(result, window=self.bbands_period)
        result['bb_middle'] = bb_result['middle_band']
        result['bb_upper'] = bb_result['upper_band']
        result['bb_lower'] = bb_result['lower_band']
        
        # Calculate Bollinger %B
        result['bb_b'] = (result['close'] - result['bb_lower']) / (result['bb_upper'] - result['bb_lower'])
        
        # Create target variable: next day's return (for classification)
        result['next_day_return'] = result['close'].pct_change(periods=self.predict_n_days).shift(-self.predict_n_days)
        result['target'] = (result['next_day_return'] > 0).astype(int)  # 1 if positive return, 0 if negative
        
        # Drop rows with NaN values
        result = result.dropna()
        
        return result
    
    def create_features(self, data):
        """
        Create feature set from prepared data.
        
        Args:
            data (pandas.DataFrame): DataFrame with technical indicators.
            
        Returns:
            tuple: X (features) and y (targets) for the ML model.
        """
        # Select features
        feature_columns = [
            'rsi_14',          # RSI
            f'sma_{self.sma_period}',   # SMA
            'macd_histogram',  # MACD histogram
            'bb_b'             # Bollinger %B
        ]
        
        # Ensure all feature columns exist
        for col in feature_columns:
            if col not in data.columns:
                raise ValueError(f"Feature column '{col}' not found in data")
        
        # Extract features and target
        X = data[feature_columns].values
        y = data['target'].values
        
        return X, y
    
    def train_model(self, data):
        """
        Train the machine learning model using the prepared data.
        
        Args:
            data (pandas.DataFrame): DataFrame with technical indicators and targets.
            
        Returns:
            object: Trained ML model.
        """
        # Prepare data
        prepared_data = self.prepare_data(data)
        
        # Create features and target
        X, y = self.create_features(prepared_data)
        
        # Create train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=1-self.training_size, shuffle=False
        )
        
        # Scale features
        self.scaler.fit(X_train)
        X_train_scaled = self.scaler.transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Create model
        if self.model_type == 'random_forest':
            self.model = RandomForestClassifier(
                n_estimators=100, 
                random_state=42,
                class_weight='balanced'
            )
        else:  # logistic_regression
            self.model = LogisticRegression(
                random_state=42,
                class_weight='balanced'
            )
        
        # Train model
        logger.info(f"Training {self.model_type} model with {len(X_train)} samples")
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate model
        y_pred = self.model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        logger.info(f"Model accuracy: {accuracy:.4f}")
        
        # Log feature importances for Random Forest
        if self.model_type == 'random_forest':
            feature_columns = [
                'rsi_14',          # RSI
                f'sma_{self.sma_period}',   # SMA
                'macd_histogram',  # MACD histogram
                'bb_b'             # Bollinger %B
            ]
            importances = self.model.feature_importances_
            feature_importance = dict(zip(feature_columns, importances))
            logger.info(f"Feature importances: {feature_importance}")
        
        return self.model
    
    def generate_signals(self, data):
        """
        Generate buy/sell signals based on model predictions.
        
        Args:
            data (pandas.DataFrame): DataFrame containing price data and indicators.
            
        Returns:
            pandas.DataFrame: DataFrame with added signal columns.
        """
        # Make sure necessary indicators are added
        prepared_data = self.prepare_data(data)
        
        # If model is not trained, train it now
        if self.model is None:
            self.train_model(prepared_data)
        
        # Create a copy of the prepared data for predictions
        result = prepared_data.copy()
        
        # Extract features for prediction
        X, _ = self.create_features(prepared_data)
        X_scaled = self.scaler.transform(X)
        
        # Make predictions
        if hasattr(self.model, 'predict_proba'):
            probabilities = self.model.predict_proba(X_scaled)
            result['probability_up'] = probabilities[:, 1]  # Probability of price going up
        else:
            # If the model doesn't support probabilities, use predictions directly
            predictions = self.model.predict(X_scaled)
            result['probability_up'] = predictions
        
        # Generate signals based on prediction probability
        result['signal'] = 0  # Initialize signal column
        
        # Buy signal when probability of up movement exceeds threshold
        result.loc[result['probability_up'] > self.threshold, 'signal'] = 1
        
        # Sell signal when probability of down movement exceeds threshold
        result.loc[result['probability_up'] < (1 - self.threshold), 'signal'] = -1
        
        # Generate positions (1 = long, 0 = no position, -1 = short)
        result['position'] = 0
        
        # For a long-only strategy
        current_position = 0
        positions = []
        
        for signal in result['signal']:
            if signal == 1 and current_position <= 0:  # Buy if we don't have a long position
                current_position = 1
            elif signal == -1 and current_position >= 0:  # Sell if we have a long position
                current_position = 0
                
            positions.append(current_position)
            
        result['position'] = positions
        
        return result
    
    def backtest(self, data, initial_capital=10000.0, commission=0.001):
        """
        Run a backtest of the strategy.
        
        Args:
            data (pandas.DataFrame): DataFrame containing price data.
            initial_capital (float): Initial capital for the backtest. Default is 10000.0.
            commission (float): Commission rate per trade. Default is 0.001 (0.1%).
            
        Returns:
            pandas.DataFrame: DataFrame with backtest results.
        """
        # Generate signals and positions
        result = self.generate_signals(data)
        
        # Calculate returns
        result['market_return'] = result['close'].pct_change()
        result['strategy_return'] = result['market_return'] * result['position'].shift(1)
        
        # Account for commissions
        result['trade'] = result['position'].diff().abs()
        result['commission'] = result['trade'] * commission
        result['strategy_return'] = result['strategy_return'] - result['commission']
        
        # Calculate cumulative returns
        result['cumulative_market_return'] = (1 + result['market_return']).cumprod()
        result['cumulative_strategy_return'] = (1 + result['strategy_return']).cumprod()
        
        # Calculate equity and drawdown
        result['equity'] = initial_capital * result['cumulative_strategy_return']
        result['peak'] = result['equity'].cummax()
        result['drawdown'] = (result['peak'] - result['equity']) / result['peak']
        
        return result
    
    def get_performance_metrics(self, backtest_results):
        """
        Calculate performance metrics for the strategy.
        
        Args:
            backtest_results (pandas.DataFrame): DataFrame with backtest results.
            
        Returns:
            dict: Dictionary containing performance metrics.
        """
        # Basic metrics
        total_return = backtest_results['cumulative_strategy_return'].iloc[-1] - 1.0
        market_return = backtest_results['cumulative_market_return'].iloc[-1] - 1.0
        
        # Annualized metrics (assuming 252 trading days in a year)
        n_days = len(backtest_results)
        n_years = n_days / 252
        
        annual_return = (1 + total_return) ** (1 / n_years) - 1
        
        # Risk metrics
        daily_returns = backtest_results['strategy_return'].dropna()
        volatility = daily_returns.std() * np.sqrt(252)
        sharpe_ratio = annual_return / volatility if volatility > 0 else 0
        
        max_drawdown = backtest_results['drawdown'].max()
        
        # Trade metrics
        trades = backtest_results['trade'].value_counts()[1] if 1 in backtest_results['trade'].value_counts() else 0
        
        # Calculate win rate
        if trades > 0:
            winning_trades = (daily_returns[daily_returns > 0]).count()
            win_rate = winning_trades / trades
        else:
            win_rate = 0
        
        return {
            'strategy_name': self.name,
            'total_return': total_return * 100,  # Convert to percentage
            'market_return': market_return * 100,  # Convert to percentage
            'annual_return': annual_return * 100,  # Convert to percentage
            'volatility': volatility * 100,  # Convert to percentage
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown * 100,  # Convert to percentage
            'trades': trades,
            'win_rate': win_rate * 100,  # Convert to percentage
            'model_type': self.model_type,
            'threshold': self.threshold
        }
    
    def get_parameters(self):
        """
        Get the parameters for this strategy.
        
        Returns:
            dict: Dictionary containing the strategy parameters.
        """
        return {
            'strategy_type': 'ml_based',
            'model_type': self.model_type,
            'training_size': self.training_size,
            'predict_n_days': self.predict_n_days,
            'threshold': self.threshold,
            'rsi_period': self.rsi_period,
            'sma_period': self.sma_period,
            'bbands_period': self.bbands_period
        }
    
    @staticmethod
    def from_parameters(parameters):
        """
        Create a strategy instance from parameters.
        
        Args:
            parameters (dict): Dictionary containing strategy parameters.
            
        Returns:
            MLBasedStrategy: Strategy instance with the specified parameters.
        """
        # Get parameters with defaults
        model_type = parameters.get('model_type', 'random_forest')
        training_size = parameters.get('training_size', 0.7)
        predict_n_days = parameters.get('predict_n_days', 1)
        threshold = parameters.get('threshold', 0.55)
        rsi_period = parameters.get('rsi_period', 14)
        sma_period = parameters.get('sma_period', 20)
        bbands_period = parameters.get('bbands_period', 20)
        
        return MLBasedStrategy(
            model_type=model_type,
            training_size=training_size,
            predict_n_days=predict_n_days,
            threshold=threshold,
            rsi_period=rsi_period,
            sma_period=sma_period,
            bbands_period=bbands_period
        ) 