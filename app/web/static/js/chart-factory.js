/**
 * Streaklet Chart Factory
 *
 * Reusable ApexCharts configurations and factory methods.
 * Consolidates duplicate chart code and provides consistent styling.
 */

// Default color palette
const CHART_COLORS = {
    primary: '#3b82f6',
    secondary: '#8b5cf6',
    success: '#52c41a',
    danger: '#ef4444',
    warning: '#f59e0b',
    info: '#06b6d4',
    gray: '#6b7280'
};

// Common chart configuration defaults
const CHART_DEFAULTS = {
    chart: {
        toolbar: {
            show: false
        },
        zoom: {
            enabled: false
        },
        animations: {
            enabled: true,
            easing: 'easeinout',
            speed: 800
        }
    },
    dataLabels: {
        enabled: false
    },
    grid: {
        borderColor: '#e5e7eb',
        strokeDashArray: 3
    },
    xaxis: {
        labels: {
            style: {
                fontSize: '12px'
            }
        }
    }
};

/**
 * Chart Factory class for creating consistent ApexCharts
 */
class ChartFactory {
    /**
     * Create a line chart
     * @param {string} containerId - DOM element ID
     * @param {Object} config - Chart configuration
     * @returns {ApexCharts} Chart instance
     */
    static createLineChart(containerId, config) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.warn(`Container #${containerId} not found`);
            return null;
        }

        const {
            data = [],
            label = '',
            color = CHART_COLORS.primary,
            height = 240,
            yAxisLabel = '',
            yAxisMin = 0,
            formatter = (val) => Math.round(val).toLocaleString(),
            transform = null,
            categories = null
        } = config;

        // Transform and prepare data
        const values = data.map(d => {
            const val = transform ? transform(d.value) : d.value;
            return Math.round(val * 100) / 100;
        });

        const xCategories = categories || data.map(d => {
            const date = new Date(d.date + 'T00:00:00');
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        });

        const options = {
            ...CHART_DEFAULTS,
            series: [{
                name: label,
                data: values
            }],
            chart: {
                ...CHART_DEFAULTS.chart,
                type: 'line',
                height
            },
            stroke: {
                curve: 'straight',
                width: 2
            },
            markers: {
                size: 3,
                strokeWidth: 1.5,
                hover: {
                    size: 5
                }
            },
            colors: [color],
            xaxis: {
                ...CHART_DEFAULTS.xaxis,
                categories: xCategories
            },
            yaxis: {
                min: yAxisMin,
                title: {
                    text: yAxisLabel,
                    style: {
                        fontSize: '12px',
                        fontWeight: 500
                    }
                },
                labels: {
                    formatter
                }
            },
            tooltip: {
                y: {
                    formatter
                }
            },
            grid: CHART_DEFAULTS.grid
        };

        return new ApexCharts(container, options);
    }

    /**
     * Create a multi-series line chart (with area support)
     * @param {string} containerId - DOM element ID
     * @param {Object} config - Chart configuration
     * @returns {ApexCharts} Chart instance
     */
    static createMultiSeriesChart(containerId, config) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.warn(`Container #${containerId} not found`);
            return null;
        }

        const {
            series = [],
            categories = [],
            height = 350,
            colors = [CHART_COLORS.primary, CHART_COLORS.danger, CHART_COLORS.secondary],
            yAxisConfig = [],
            enableToolbar = true,
            strokeWidth = 2,
            strokeCurve = 'smooth',
            fillType = 'solid'
        } = config;

        const options = {
            ...CHART_DEFAULTS,
            series,
            chart: {
                ...CHART_DEFAULTS.chart,
                height,
                type: 'line',
                stacked: false,
                toolbar: {
                    show: enableToolbar,
                    tools: enableToolbar ? {
                        download: true,
                        selection: true,
                        zoom: true,
                        zoomin: true,
                        zoomout: true,
                        pan: true,
                        reset: true
                    } : {}
                },
                zoom: {
                    enabled: enableToolbar
                }
            },
            stroke: {
                width: Array.isArray(strokeWidth) ? strokeWidth : Array(series.length).fill(strokeWidth),
                curve: strokeCurve
            },
            fill: {
                type: Array.isArray(fillType) ? fillType : Array(series.length).fill(fillType),
                gradient: {
                    shade: 'light',
                    type: 'vertical',
                    opacityFrom: 0.6,
                    opacityTo: 0.1
                }
            },
            colors,
            xaxis: {
                ...CHART_DEFAULTS.xaxis,
                categories,
                labels: {
                    ...CHART_DEFAULTS.xaxis.labels,
                    rotate: -45,
                    style: {
                        fontSize: '11px'
                    }
                }
            },
            yaxis: yAxisConfig.length > 0 ? yAxisConfig : {
                labels: {
                    formatter: (val) => Math.round(val).toLocaleString()
                }
            },
            legend: {
                position: 'top',
                horizontalAlign: 'center'
            },
            tooltip: {
                shared: true,
                intersect: false
            },
            grid: CHART_DEFAULTS.grid
        };

        return new ApexCharts(container, options);
    }

    /**
     * Create a bar chart (for comparisons)
     * @param {string} containerId - DOM element ID
     * @param {Object} config - Chart configuration
     * @returns {ApexCharts} Chart instance
     */
    static createBarChart(containerId, config) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.warn(`Container #${containerId} not found`);
            return null;
        }

        const {
            series = [],
            categories = [],
            height = 300,
            colors = [CHART_COLORS.primary, CHART_COLORS.secondary],
            horizontal = false,
            distributed = false,
            yAxisFormatter = (val) => Math.round(val).toLocaleString()
        } = config;

        const options = {
            ...CHART_DEFAULTS,
            series,
            chart: {
                ...CHART_DEFAULTS.chart,
                type: 'bar',
                height
            },
            plotOptions: {
                bar: {
                    horizontal,
                    distributed,
                    borderRadius: 4,
                    dataLabels: {
                        position: 'top'
                    }
                }
            },
            colors,
            xaxis: {
                ...CHART_DEFAULTS.xaxis,
                categories
            },
            yaxis: {
                labels: {
                    formatter: yAxisFormatter
                }
            },
            tooltip: {
                y: {
                    formatter: yAxisFormatter
                }
            },
            grid: CHART_DEFAULTS.grid
        };

        return new ApexCharts(container, options);
    }

    /**
     * Create a scatter chart (for correlations)
     * @param {string} containerId - DOM element ID
     * @param {Object} config - Chart configuration
     * @returns {ApexCharts} Chart instance
     */
    static createScatterChart(containerId, config) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.warn(`Container #${containerId} not found`);
            return null;
        }

        const {
            series = [],
            height = 300,
            colors = [CHART_COLORS.primary],
            xAxisTitle = '',
            yAxisTitle = '',
            xAxisFormatter = (val) => Math.round(val).toLocaleString(),
            yAxisFormatter = (val) => Math.round(val).toLocaleString()
        } = config;

        const options = {
            ...CHART_DEFAULTS,
            series,
            chart: {
                ...CHART_DEFAULTS.chart,
                type: 'scatter',
                height,
                zoom: {
                    enabled: true,
                    type: 'xy'
                }
            },
            colors,
            xaxis: {
                ...CHART_DEFAULTS.xaxis,
                title: {
                    text: xAxisTitle
                },
                labels: {
                    formatter: xAxisFormatter
                }
            },
            yaxis: {
                title: {
                    text: yAxisTitle
                },
                labels: {
                    formatter: yAxisFormatter
                }
            },
            tooltip: {
                custom: function({ seriesIndex, dataPointIndex, w }) {
                    const data = w.globals.initialSeries[seriesIndex].data[dataPointIndex];
                    return `<div class="apexcharts-tooltip-custom">
                        <div><strong>${xAxisTitle}:</strong> ${xAxisFormatter(data[0])}</div>
                        <div><strong>${yAxisTitle}:</strong> ${yAxisFormatter(data[1])}</div>
                    </div>`;
                }
            },
            grid: CHART_DEFAULTS.grid
        };

        return new ApexCharts(container, options);
    }

    /**
     * Create a histogram/distribution chart
     * @param {string} containerId - DOM element ID
     * @param {Object} config - Chart configuration
     * @returns {ApexCharts} Chart instance
     */
    static createHistogram(containerId, config) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.warn(`Container #${containerId} not found`);
            return null;
        }

        const {
            data = [],
            label = 'Frequency',
            categories = [],
            height = 300,
            color = CHART_COLORS.primary,
            yAxisFormatter = (val) => Math.round(val).toLocaleString()
        } = config;

        const options = {
            ...CHART_DEFAULTS,
            series: [{
                name: label,
                data
            }],
            chart: {
                ...CHART_DEFAULTS.chart,
                type: 'bar',
                height
            },
            plotOptions: {
                bar: {
                    borderRadius: 4,
                    distributed: true
                }
            },
            colors: [color],
            xaxis: {
                ...CHART_DEFAULTS.xaxis,
                categories
            },
            yaxis: {
                title: {
                    text: label
                },
                labels: {
                    formatter: yAxisFormatter
                }
            },
            tooltip: {
                y: {
                    formatter: yAxisFormatter
                }
            },
            legend: {
                show: false
            },
            grid: CHART_DEFAULTS.grid
        };

        return new ApexCharts(container, options);
    }

    /**
     * Destroy and recreate a chart
     * @param {Object} chartInstance - Existing chart instance
     * @param {Function} createFn - Function to create new chart
     * @returns {ApexCharts} New chart instance
     */
    static recreateChart(chartInstance, createFn) {
        if (chartInstance) {
            chartInstance.destroy();
        }
        return createFn();
    }

    /**
     * Get color by name
     * @param {string} name - Color name (primary, secondary, etc.)
     * @returns {string} Hex color code
     */
    static getColor(name) {
        return CHART_COLORS[name] || CHART_COLORS.primary;
    }
}

// Export for global use
window.ChartFactory = ChartFactory;
window.CHART_COLORS = CHART_COLORS;

// Console info
if (typeof console !== 'undefined' && console.info) {
    console.info('%c📊 Chart Factory Loaded', 'color: #3b82f6; font-weight: bold;');
    console.info('Available methods:', {
        'Line Charts': 'ChartFactory.createLineChart()',
        'Multi-Series': 'ChartFactory.createMultiSeriesChart()',
        'Bar Charts': 'ChartFactory.createBarChart()',
        'Scatter Charts': 'ChartFactory.createScatterChart()',
        'Histograms': 'ChartFactory.createHistogram()'
    });
}
