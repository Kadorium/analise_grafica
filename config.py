import os
import json

# Default configuration
DEFAULT_CONFIG = {
    'data': {
        'start_date': '2020-01-01',
        'end_date': '2023-01-01',
        'symbols': ['SPY']
    },
    'backtest': {
        'initial_capital': 10000.0,
        'commission': 0.001
    },
    'indicators': {
        'moving_averages': {
            'sma_periods': [20, 50, 200],
            'ema_periods': [12, 26, 50]
        },
        'rsi': {
            'period': 14
        },
        'macd': {
            'fast_period': 12,
            'slow_period': 26,
            'signal_period': 9
        },
        'bollinger_bands': {
            'window': 20,
            'num_std': 2
        },
        'stochastic': {
            'k_period': 14,
            'd_period': 3,
            'slowing': 3
        },
        'volume': True,
        'atr': {
            'period': 14
        }
    },
    'strategies': {
        'trend_following': {
            'fast_ma_type': 'ema',
            'fast_ma_period': 20,
            'slow_ma_type': 'sma',
            'slow_ma_period': 50
        },
        'mean_reversion': {
            'rsi_period': 14,
            'oversold': 30,
            'overbought': 70,
            'exit_middle': 50
        },
        'breakout': {
            'lookback_period': 20,
            'volume_threshold': 1.5,
            'price_threshold': 0.02,
            'volatility_exit': True,
            'atr_multiplier': 2.0,
            'use_bbands': True
        }
    },
    'optimization': {
        'metric': 'sharpe_ratio',
        'max_workers': None
    },
    'plots': {
        'equity_curve': True,
        'drawdown': True,
        'trades': True
    },
    'output': {
        'save_results': True,
        'output_dir': 'results'
    }
}

class Config:
    """
    Configuration management class.
    """
    
    def __init__(self, config_path=None):
        """
        Initialize the configuration.
        
        Args:
            config_path (str, optional): Path to a JSON config file. Defaults to None.
        """
        self.config = DEFAULT_CONFIG.copy()
        
        if config_path and os.path.exists(config_path):
            self.load_config(config_path)
    
    def get(self, key, default=None):
        """
        Get a configuration value.
        
        Args:
            key (str): Configuration key. Can be a nested key using dot notation.
            default: Default value to return if the key is not found.
            
        Returns:
            The configuration value or the default value.
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
                
        return value
    
    def set(self, key, value):
        """
        Set a configuration value.
        
        Args:
            key (str): Configuration key. Can be a nested key using dot notation.
            value: The value to set.
        """
        keys = key.split('.')
        config = self.config
        
        for i, k in enumerate(keys[:-1]):
            if k not in config:
                config[k] = {}
            config = config[k]
            
        config[keys[-1]] = value
    
    def update(self, updates):
        """
        Update the configuration with multiple values.
        
        Args:
            updates (dict): Dictionary containing the updates.
        """
        def update_dict(d, u):
            for k, v in u.items():
                if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                    update_dict(d[k], v)
                else:
                    d[k] = v
                    
        update_dict(self.config, updates)
    
    def load_config(self, config_path):
        """
        Load configuration from a JSON file.
        
        Args:
            config_path (str): Path to the JSON config file.
        """
        try:
            with open(config_path, 'r') as f:
                loaded_config = json.load(f)
                self.update(loaded_config)
        except Exception as e:
            print(f"Error loading config from {config_path}: {str(e)}")
    
    def save_config(self, config_path):
        """
        Save the current configuration to a JSON file.
        
        Args:
            config_path (str): Path to save the JSON config file.
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config to {config_path}: {str(e)}")
    
    def get_all(self):
        """
        Get the entire configuration.
        
        Returns:
            dict: The complete configuration.
        """
        return self.config.copy()
    
    def reset(self):
        """
        Reset the configuration to the default values.
        """
        self.config = DEFAULT_CONFIG.copy()

# Initialize global configuration
config = Config()

# Function to get a configuration value
def get_config(key, default=None):
    """
    Get a configuration value.
    
    Args:
        key (str): Configuration key. Can be a nested key using dot notation.
        default: Default value to return if the key is not found.
        
    Returns:
        The configuration value or the default value.
    """
    return config.get(key, default)

# Function to set a configuration value
def set_config(key, value):
    """
    Set a configuration value.
    
    Args:
        key (str): Configuration key. Can be a nested key using dot notation.
        value: The value to set.
    """
    config.set(key, value)

# Function to update the configuration
def update_config(updates):
    """
    Update the configuration with multiple values.
    
    Args:
        updates (dict): Dictionary containing the updates.
    """
    config.update(updates)

# Function to load configuration from a file
def load_config(config_path):
    """
    Load configuration from a JSON file.
    
    Args:
        config_path (str): Path to the JSON config file.
    """
    config.load_config(config_path)

# Function to save configuration to a file
def save_config(config_path):
    """
    Save the current configuration to a JSON file.
    
    Args:
        config_path (str): Path to save the JSON config file.
    """
    config.save_config(config_path)

# Function to get the entire configuration
def get_all_config():
    """
    Get the entire configuration.
    
    Returns:
        dict: The complete configuration.
    """
    return config.get_all()

# Function to reset the configuration
def reset_config():
    """
    Reset the configuration to the default values.
    """
    config.reset() 