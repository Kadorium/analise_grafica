// frontend/js/utils/formatters.js

export function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toISOString().split('T')[0];
}

export function formatNumber(num, decimals = 2) {
    return Number(num).toFixed(decimals);
}

export function formatMetricName(metric) {
    // Convert snake_case to Title Case with spaces
    return metric
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

export function formatMetricValue(metric, value) {
    if (typeof value === 'number') {
        // Format percentages with 2 decimal places
        if (metric.includes('return') || metric.includes('drawdown') || metric.includes('volatility') || metric.includes('rate')) {
            return value.toFixed(2) + '%';
        } 
        // Format ratios with 2 decimal places
        else if (metric.includes('ratio')) {
            return value.toFixed(2);
        }
        // Format other numbers with 2 decimal places
        return value.toFixed(2);
    }
    return value;
}

export function formatParamName(name) {
    return name
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}
