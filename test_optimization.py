import pandas as pd
import logging
from comparison.comparator import StrategyComparator
from strategies import get_default_parameters

# Set up logging to both console and file
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("test_optimization.log"),
                        logging.StreamHandler()
                    ])
logger = logging.getLogger('test_optimization')

# Load sample data
def load_test_data():
    try:
        data = pd.read_csv('data/sample/test_data.csv')
        return data
    except:
        try:
            data = pd.read_csv('data/teste_arranged.csv')
            return data
        except:
            # Create dummy data if no files exist
            dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
            data = pd.DataFrame({
                'date': dates,
                'open': range(100, 200),
                'high': range(105, 205),
                'low': range(95, 195),
                'close': range(102, 202),
                'volume': [1000000] * 100
            })
            return data

def test_optimization():
    # Load data
    logger.info("Loading test data...")
    data = load_test_data()
    logger.info(f"Loaded {len(data)} rows of data")
    
    # Create strategy configurations
    strategy_configs = [
        {
            'strategy_id': 'trend_following',
            'parameters': get_default_parameters('trend_following'),
            'param_ranges': {
                'fast_ma_type': ['sma', 'ema'],
                'fast_ma_period': [5, 10, 15],
                'slow_ma_type': ['sma', 'ema'],
                'slow_ma_period': [30, 50, 100]
            }
        }
    ]
    
    # Create comparator
    logger.info("Creating strategy comparator...")
    comparator = StrategyComparator(data)
    
    # Run optimization
    logger.info("Running optimization...")
    try:
        results = comparator.optimize_and_compare(
            strategy_configs=strategy_configs,
            metric='sharpe_ratio'
        )
        
        # Check results
        logger.info("Optimization completed!")
        strategy_results = results['results']
        logger.info(f"Number of strategies with results: {len(strategy_results)}")
        
        for strategy_id, result in strategy_results.items():
            logger.info(f"Strategy: {strategy_id}")
            logger.info(f"Parameters: {result['parameters']}")
            logger.info(f"Sharpe ratio: {result['metrics'].get('sharpe_ratio', 'N/A')}")
        
        return results
    except Exception as e:
        logger.error(f"Error during optimization: {str(e)}", exc_info=True)
        return None

if __name__ == "__main__":
    logger.info("Starting optimization test")
    results = test_optimization()
    logger.info("Test completed") 