// frontend/js/utils/strategies-config.js

// Define all available strategies with their parameters, labels, and descriptions
export const strategies = [
    {
        name: 'trend_following',
        label: 'Trend Following',
        description: 'Buys when fast MA crosses above slow MA (golden cross) and sells when fast MA crosses below slow MA (death cross).',
        params: [
            { id: 'fast_ma_type', label: 'Fast MA Type', type: 'select', default: 'ema', options: [
                { value: 'sma', label: 'Simple Moving Average' },
                { value: 'ema', label: 'Exponential Moving Average' }
            ]},
            { id: 'fast_ma_period', label: 'Fast MA Period', type: 'number', default: 20, min: 1, max: 100 },
            { id: 'slow_ma_type', label: 'Slow MA Type', type: 'select', default: 'sma', options: [
                { value: 'sma', label: 'Simple Moving Average' },
                { value: 'ema', label: 'Exponential Moving Average' }
            ]},
            { id: 'slow_ma_period', label: 'Slow MA Period', type: 'number', default: 50, min: 1, max: 500 }
        ]
    },
    {
        name: 'mean_reversion',
        label: 'Mean Reversion',
        description: 'Buys when RSI is below oversold level and sells when RSI is above overbought level. Also exits positions when RSI crosses the middle level.',
        params: [
            { id: 'rsi_period', label: 'RSI Period', type: 'number', default: 14, min: 1, max: 100 },
            { id: 'oversold', label: 'Oversold Level', type: 'number', default: 30, min: 0, max: 100 },
            { id: 'overbought', label: 'Overbought Level', type: 'number', default: 70, min: 0, max: 100 },
            { id: 'exit_middle', label: 'Exit Middle Level', type: 'number', default: 50, min: 0, max: 100 }
        ]
    },
    {
        name: 'breakout',
        label: 'Breakout',
        description: 'Buys when price breaks out above recent highs with increased volume. Uses volatility-based exit strategies.',
        params: [
            { id: 'lookback_period', label: 'Lookback Period', type: 'number', default: 20, min: 1, max: 100 },
            { id: 'volume_threshold', label: 'Volume Threshold', type: 'number', default: 1.5, min: 1, max: 5, step: 0.1 },
            { id: 'price_threshold', label: 'Price Threshold (%)', type: 'number', default: 2, min: 0.1, max: 10, step: 0.1 },
            { id: 'volatility_exit', label: 'Use Volatility-Based Exit', type: 'checkbox', default: true },
            { id: 'atr_multiplier', label: 'ATR Multiplier', type: 'number', default: 2.0, min: 0.5, max: 5, step: 0.1 },
            { id: 'use_bbands', label: 'Use Bollinger Bands', type: 'checkbox', default: true }
        ]
    },
    {
        name: 'sma_crossover',
        label: 'SMA Crossover',
        description: 'Buys when short SMA crosses above long SMA and sells when it crosses below.',
        params: [
            { id: 'short_period', label: 'Short Period', type: 'number', default: 50, min: 1, max: 200 },
            { id: 'long_period', label: 'Long Period', type: 'number', default: 200, min: 1, max: 500 }
        ]
    },
    {
        name: 'ema_crossover',
        label: 'EMA Crossover',
        description: 'Buys when short EMA crosses above long EMA and sells when it crosses below.',
        params: [
            { id: 'short_period', label: 'Short Period', type: 'number', default: 20, min: 1, max: 100 },
            { id: 'long_period', label: 'Long Period', type: 'number', default: 50, min: 1, max: 200 }
        ]
    },
    {
        name: 'supertrend',
        label: 'SuperTrend',
        description: 'Trend following indicator that uses ATR for volatility-based entries and exits.',
        params: [
            { id: 'period', label: 'Period', type: 'number', default: 10, min: 1, max: 50 },
            { id: 'multiplier', label: 'Multiplier', type: 'number', default: 2.0, min: 0.5, max: 10, step: 0.1 }
        ]
    },
    {
        name: 'adx',
        label: 'ADX',
        description: 'Average Directional Index strategy for identifying trend strength and potential reversals.',
        params: [
            { id: 'period', label: 'Period', type: 'number', default: 14, min: 1, max: 50 },
            { id: 'threshold', label: 'Threshold', type: 'number', default: 25, min: 1, max: 50 }
        ]
    },
    {
        name: 'bollinger_breakout',
        label: 'Bollinger Bands Breakout',
        description: 'Signals when price breaks out of the Bollinger Bands.',
        params: [
            { id: 'period', label: 'Period', type: 'number', default: 20, min: 1, max: 100 },
            { id: 'std_dev', label: 'Standard Deviations', type: 'number', default: 2.0, min: 0.1, max: 5, step: 0.1 }
        ]
    },
    {
        name: 'atr_breakout',
        label: 'ATR Breakout',
        description: 'Uses Average True Range to identify significant price movements.',
        params: [
            { id: 'period', label: 'Period', type: 'number', default: 14, min: 1, max: 50 },
            { id: 'multiplier', label: 'Multiplier', type: 'number', default: 1.5, min: 0.1, max: 5, step: 0.1 }
        ]
    },
    {
        name: 'donchian_breakout',
        label: 'Donchian Channel Breakout',
        description: 'Buys/sells when price breaks above/below the Donchian channel.',
        params: [
            { id: 'period', label: 'Period', type: 'number', default: 20, min: 1, max: 100 }
        ]
    },
    {
        name: 'keltner_reversal',
        label: 'Keltner Channel Reversal',
        description: 'Looks for reversals at Keltner channel boundaries.',
        params: [
            { id: 'period', label: 'Period', type: 'number', default: 20, min: 1, max: 100 },
            { id: 'multiplier', label: 'Multiplier', type: 'number', default: 2.0, min: 0.1, max: 5, step: 0.1 }
        ]
    },
    {
        name: 'rsi',
        label: 'RSI',
        description: 'Relative Strength Index strategy for identifying overbought and oversold conditions.',
        params: [
            { id: 'period', label: 'Period', type: 'number', default: 14, min: 1, max: 50 },
            { id: 'buy_level', label: 'Buy Level', type: 'number', default: 30, min: 0, max: 100 },
            { id: 'sell_level', label: 'Sell Level', type: 'number', default: 70, min: 0, max: 100 }
        ]
    },
    {
        name: 'macd_crossover',
        label: 'MACD Crossover',
        description: 'Momentum indicator that shows the relationship between two moving averages.',
        params: [
            { id: 'fast_period', label: 'Fast Period', type: 'number', default: 12, min: 1, max: 50 },
            { id: 'slow_period', label: 'Slow Period', type: 'number', default: 26, min: 1, max: 100 },
            { id: 'signal_period', label: 'Signal Period', type: 'number', default: 9, min: 1, max: 50 }
        ]
    },
    {
        name: 'stochastic',
        label: 'Stochastic Oscillator',
        description: 'Compares current price to its range over a period of time.',
        params: [
            { id: 'k_period', label: 'K Period', type: 'number', default: 14, min: 1, max: 50 },
            { id: 'd_period', label: 'D Period', type: 'number', default: 3, min: 1, max: 20 }
        ]
    },
    {
        name: 'cci',
        label: 'CCI',
        description: 'Commodity Channel Index identifies cyclical trends in price movement.',
        params: [
            { id: 'period', label: 'Period', type: 'number', default: 20, min: 1, max: 100 },
            { id: 'overbought', label: 'Overbought Level', type: 'number', default: 100, min: 0, max: 300 },
            { id: 'oversold', label: 'Oversold Level', type: 'number', default: -100, min: -300, max: 0 }
        ]
    },
    {
        name: 'williams_r',
        label: 'Williams %R',
        description: 'Momentum indicator that measures overbought/oversold levels.',
        params: [
            { id: 'period', label: 'Period', type: 'number', default: 14, min: 1, max: 50 },
            { id: 'buy_level', label: 'Buy Level', type: 'number', default: -80, min: -100, max: 0 },
            { id: 'sell_level', label: 'Sell Level', type: 'number', default: -20, min: -100, max: 0 }
        ]
    },
    {
        name: 'obv_trend',
        label: 'OBV Trend',
        description: 'Uses On-Balance Volume flow to predict changes in price.',
        params: [
            { id: 'period', label: 'Period', type: 'number', default: 20, min: 1, max: 100 }
        ]
    },
    {
        name: 'vpt_signal',
        label: 'Volume Price Trend',
        description: 'Relates volume to price changes to confirm price movements.',
        params: [
            { id: 'period', label: 'Period', type: 'number', default: 20, min: 1, max: 100 }
        ]
    },
    {
        name: 'volume_ratio',
        label: 'Volume Ratio',
        description: 'Identifies unusual volume that may signal price reversals.',
        params: [
            { id: 'period', label: 'Period', type: 'number', default: 20, min: 1, max: 100 },
            { id: 'threshold', label: 'Threshold', type: 'number', default: 2.0, min: 0.1, max: 5, step: 0.1 }
        ]
    },
    {
        name: 'cmf',
        label: 'Chaikin Money Flow',
        description: 'Measures the Money Flow Volume over a period of time.',
        params: [
            { id: 'period', label: 'Period', type: 'number', default: 20, min: 1, max: 100 }
        ]
    },
    {
        name: 'accum_dist',
        label: 'Accumulation/Distribution',
        description: 'Volume indicator that assesses money flowing into or out of a security.',
        params: [
            { id: 'period', label: 'Period', type: 'number', default: 20, min: 1, max: 100 }
        ]
    },
    {
        name: 'candlestick',
        label: 'Candlestick Patterns',
        description: 'Identifies common candlestick patterns for potential reversals or continuations.',
        params: [
            { id: 'confirmation_period', label: 'Confirmation Period', type: 'number', default: 1, min: 1, max: 10 }
        ]
    },
    {
        name: 'adaptive_trend',
        label: 'Adaptive Trend',
        description: 'Dynamically adjusts to market conditions using multiple indicators.',
        params: [
            { id: 'fast_period', label: 'Fast Period', type: 'number', default: 10, min: 1, max: 50 },
            { id: 'slow_period', label: 'Slow Period', type: 'number', default: 30, min: 1, max: 100 },
            { id: 'signal_period', label: 'Signal Period', type: 'number', default: 9, min: 1, max: 50 }
        ]
    },
    {
        name: 'hybrid_momentum_volatility',
        label: 'Hybrid Momentum/Volatility',
        description: 'Combines momentum and volatility indicators for a hybrid approach.',
        params: [
            { id: 'rsi_period', label: 'RSI Period', type: 'number', default: 14, min: 1, max: 50 },
            { id: 'bb_period', label: 'Bollinger Period', type: 'number', default: 20, min: 1, max: 100 },
            { id: 'std_dev', label: 'Standard Deviations', type: 'number', default: 2.0, min: 0.1, max: 5, step: 0.1 }
        ]
    },
    {
        name: 'pattern_recognition',
        label: 'Pattern Recognition',
        description: 'Identifies chart patterns for potential trading signals.',
        params: [
            { id: 'lookback', label: 'Lookback Period', type: 'number', default: 5, min: 1, max: 20 }
        ]
    }
];

// Helper function to get a strategy configuration by name
export function getStrategyConfig(strategyName) {
    return strategies.find(strategy => strategy.name === strategyName) || null;
}

// Helper function to get strategy descriptions
export function getStrategyDescription(strategyName) {
    const strategy = getStrategyConfig(strategyName);
    return strategy ? strategy.description : '';
}

// Helper function to get strategy default parameters
export function getStrategyDefaultParams(strategyName) {
    const strategy = getStrategyConfig(strategyName);
    if (!strategy) return {};
    
    const defaultParams = {};
    strategy.params.forEach(param => {
        defaultParams[param.id] = param.default;
    });
    
    return defaultParams;
} 