"""
Web dashboard for performance monitoring
"""

import asyncio
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from .metrics import MetricsCollector


class DashboardServer:
    """Web dashboard server for monitoring"""

    def __init__(
        self,
        metrics_collector: MetricsCollector,
        host: str = "0.0.0.0",
        port: int = 8080,
    ):
        self.metrics_collector = metrics_collector
        self.host = host
        self.port = port

        # Create FastAPI app
        self.app = FastAPI(title="Self-Optimizing System Dashboard")

        # WebSocket connections for real-time updates
        self.websocket_connections = []

        # Setup routes
        self._setup_routes()

        # Create static directory for dashboard assets
        self.static_dir = Path(__file__).parent / "static"
        self.static_dir.mkdir(exist_ok=True)

        # Mount static files
        self.app.mount(
            "/static", StaticFiles(directory=str(self.static_dir)), name="static"
        )

        # Create default dashboard HTML
        self._create_dashboard_html()

    def _setup_routes(self):
        """Setup API routes"""

        @self.app.get("/")
        async def dashboard():
            """Serve dashboard HTML"""
            html_content = self._get_dashboard_html()
            return HTMLResponse(content=html_content)

        @self.app.get("/api/metrics/current")
        async def get_current_metrics():
            """Get current metrics"""
            metrics = self.metrics_collector.current_metrics
            return JSONResponse(content=metrics.to_dict())

        @self.app.get("/api/metrics/historical")
        async def get_historical_metrics(hours: int = 24):
            """Get historical metrics"""
            metrics = self.metrics_collector.get_historical_metrics(hours)
            return JSONResponse(content=[m.to_dict() for m in metrics])

        @self.app.get("/api/metrics/summary")
        async def get_metrics_summary(hours: int = 1):
            """Get metrics summary"""
            summary = self.metrics_collector.get_summary(hours)
            return JSONResponse(content=summary)

        @self.app.get("/api/health")
        async def health_check():
            """Health check endpoint"""
            return JSONResponse(
                content={
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "uptime": (
                        datetime.now() - self.metrics_collector.start_time
                    ).total_seconds(),
                }
            )

        @self.app.websocket("/ws/metrics")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket for real-time metrics updates"""
            await websocket.accept()
            self.websocket_connections.append(websocket)

            try:
                while True:
                    # Send metrics updates every 5 seconds
                    metrics = self.metrics_collector.current_metrics
                    await websocket.send_json(metrics.to_dict())
                    await asyncio.sleep(5)
            except WebSocketDisconnect:
                self.websocket_connections.remove(websocket)

    def _create_dashboard_html(self):
        """Create dashboard HTML file"""
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Self-Optimizing System Dashboard</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/luxon"></script>
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }

                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 20px;
                }

                .dashboard {
                    max-width: 1400px;
                    margin: 0 auto;
                }

                .header {
                    background: rgba(255, 255, 255, 0.95);
                    border-radius: 15px;
                    padding: 30px;
                    margin-bottom: 20px;
                    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
                }

                .header h1 {
                    color: #333;
                    font-size: 2.5rem;
                    margin-bottom: 10px;
                }

                .header p {
                    color: #666;
                    font-size: 1.1rem;
                }

                .stats-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin-bottom: 20px;
                }

                .stat-card {
                    background: rgba(255, 255, 255, 0.95);
                    border-radius: 15px;
                    padding: 25px;
                    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
                    transition: transform 0.3s ease;
                }

                .stat-card:hover {
                    transform: translateY(-5px);
                }

                .stat-card.good {
                    border-left: 5px solid #4CAF50;
                }

                .stat-card.warning {
                    border-left: 5px solid #FF9800;
                }

                .stat-card.critical {
                    border-left: 5px solid #F44336;
                }

                .stat-card.info {
                    border-left: 5px solid #2196F3;
                }

                .stat-title {
                    font-size: 0.9rem;
                    color: #666;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                    margin-bottom: 10px;
                }

                .stat-value {
                    font-size: 2rem;
                    font-weight: bold;
                    color: #333;
                    margin-bottom: 5px;
                }

                .stat-change {
                    font-size: 0.9rem;
                    color: #666;
                }

                .stat-change.positive {
                    color: #4CAF50;
                }

                .stat-change.negative {
                    color: #F44336;
                }

                .charts-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
                    gap: 20px;
                    margin-bottom: 20px;
                }

                .chart-container {
                    background: rgba(255, 255, 255, 0.95);
                    border-radius: 15px;
                    padding: 25px;
                    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
                }

                .chart-title {
                    font-size: 1.2rem;
                    color: #333;
                    margin-bottom: 20px;
                    font-weight: 600;
                }

                .chart-wrapper {
                    position: relative;
                    height: 300px;
                }

                .time-selector {
                    display: flex;
                    gap: 10px;
                    margin-bottom: 20px;
                }

                .time-btn {
                    padding: 8px 16px;
                    background: #fff;
                    border: 2px solid #667eea;
                    border-radius: 8px;
                    color: #667eea;
                    cursor: pointer;
                    transition: all 0.3s ease;
                }

                .time-btn:hover {
                    background: #667eea;
                    color: white;
                }

                .time-btn.active {
                    background: #667eea;
                    color: white;
                }

                .status-indicator {
                    display: inline-block;
                    width: 10px;
                    height: 10px;
                    border-radius: 50%;
                    margin-right: 8px;
                }

                .status-online {
                    background: #4CAF50;
                }

                .status-offline {
                    background: #F44336;
                }

                @media (max-width: 768px) {
                    .charts-grid {
                        grid-template-columns: 1fr;
                    }

                    .stat-card, .chart-container {
                        padding: 15px;
                    }
                }
            </style>
        </head>
        <body>
            <div class="dashboard">
                <div class="header">
                    <h1>🚀 Self-Optimizing System Dashboard</h1>
                    <p>Real-time performance monitoring and analytics</p>
                    <div class="time-selector" id="timeSelector">
                        <button class="time-btn active" data-hours="1">1 Hour</button>
                        <button class="time-btn" data-hours="6">6 Hours</button>
                        <button class="time-btn" data-hours="24">24 Hours</button>
                        <button class="time-btn" data-hours="168">7 Days</button>
                    </div>
                </div>

                <div class="stats-grid" id="statsGrid">
                    <!-- Stats will be populated by JavaScript -->
                </div>

                <div class="charts-grid">
                    <div class="chart-container">
                        <div class="chart-title">Query Performance</div>
                        <div class="chart-wrapper">
                            <canvas id="queryChart"></canvas>
                        </div>
                    </div>

                    <div class="chart-container">
                        <div class="chart-title">Optimization Success Rate</div>
                        <div class="chart-wrapper">
                            <canvas id="optimizationChart"></canvas>
                        </div>
                    </div>

                    <div class="chart-container">
                        <div class="chart-title">System Health</div>
                        <div class="chart-wrapper">
                            <canvas id="healthChart"></canvas>
                        </div>
                    </div>

                    <div class="chart-container">
                        <div class="chart-title">Cost Analysis</div>
                        <div class="chart-wrapper">
                            <canvas id="costChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>

            <script>
                // Global variables
                let currentMetrics = {};
                let historicalMetrics = [];
                let selectedTimeRange = 1; // hours
                let charts = {};

                // Initialize dashboard
                document.addEventListener('DOMContentLoaded', function() {
                    setupTimeSelector();
                    loadMetrics();
                    setupWebSocket();
                    setInterval(loadMetrics, 30000); // Refresh every 30 seconds
                });

                // Setup time range selector
                function setupTimeSelector() {
                    const buttons = document.querySelectorAll('.time-btn');
                    buttons.forEach(btn => {
                        btn.addEventListener('click', function() {
                            buttons.forEach(b => b.classList.remove('active'));
                            this.classList.add('active');
                            selectedTimeRange = parseInt(this.dataset.hours);
                            loadHistoricalMetrics();
                        });
                    });
                }

                // Load current metrics
                async function loadMetrics() {
                    try {
                        const response = await fetch('/api/metrics/current');
                        currentMetrics = await response.json();
                        updateStatsGrid();
                    } catch (error) {
                        console.error('Error loading metrics:', error);
                    }
                }

                // Load historical metrics
                async function loadHistoricalMetrics() {
                    try {
                        const response = await fetch(`/api/metrics/historical?hours=${selectedTimeRange}`);
                        historicalMetrics = await response.json();
                        updateCharts();
                    } catch (error) {
                        console.error('Error loading historical metrics:', error);
                    }
                }

                // Setup WebSocket for real-time updates
                function setupWebSocket() {
                    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                    const wsUrl = `${protocol}//${window.location.host}/ws/metrics`;
                    const ws = new WebSocket(wsUrl);

                    ws.onmessage = function(event) {
                        currentMetrics = JSON.parse(event.data);
                        updateStatsGrid();
                    };

                    ws.onerror = function(error) {
                        console.error('WebSocket error:', error);
                    };
                }

                // Update stats grid with current metrics
                function updateStatsGrid() {
                    const statsGrid = document.getElementById('statsGrid');
                    if (!statsGrid || !currentMetrics.execution) return;

                    const stats = [
                        {
                            title: 'Total Queries',
                            value: currentMetrics.execution.total_queries.toLocaleString(),
                            change: '+12%',
                            type: 'info',
                            icon: '📊'
                        },
                        {
                            title: 'Success Rate',
                            value: (currentMetrics.execution.success_rate * 100).toFixed(1) + '%',
                            change: currentMetrics.execution.success_rate > 0.9 ? '+2%' : '-5%',
                            type: currentMetrics.execution.success_rate > 0.9 ? 'good' : 'warning',
                            icon: '✅'
                        },
                        {
                            title: 'Avg Response Time',
                            value: currentMetrics.execution.avg_response_time.toFixed(2) + 's',
                            change: currentMetrics.execution.avg_response_time < 2 ? '-10%' : '+15%',
                            type: currentMetrics.execution.avg_response_time < 2 ? 'good' : 'warning',
                            icon: '⚡'
                        },
                        {
                            title: 'Total Optimizations',
                            value: currentMetrics.optimization.total_optimizations.toLocaleString(),
                            change: '+8%',
                            type: 'info',
                            icon: '🔄'
                        },
                        {
                            title: 'Optimization Success',
                            value: (currentMetrics.optimization.success_rate * 100).toFixed(1) + '%',
                            change: currentMetrics.optimization.success_rate > 0.8 ? '+3%' : '-7%',
                            type: currentMetrics.optimization.success_rate > 0.8 ? 'good' : 'warning',
                            icon: '🎯'
                        },
                        {
                            title: 'Total Failures',
                            value: currentMetrics.failures.total_failures.toLocaleString(),
                            change: '-5%',
                            type: currentMetrics.failures.total_failures < 10 ? 'good' : 'critical',
                            icon: '⚠️'
                        },
                        {
                            title: 'Total Tokens',
                            value: (currentMetrics.cost.total_tokens / 1000).toFixed(1) + 'K',
                            change: '+20%',
                            type: 'info',
                            icon: '💰'
                        },
                        {
                            title: 'Estimated Cost',
                            value: '$' + currentMetrics.cost.estimated_cost.toFixed(2),
                            change: '+18%',
                            type: 'info',
                            icon: '💵'
                        },
                        {
                            title: 'System Uptime',
                            value: formatUptime(currentMetrics.system_health.uptime_seconds),
                            change: '100%',
                            type: 'good',
                            icon: '🖥️'
                        },
                        {
                            title: 'Memory Usage',
                            value: currentMetrics.system_health.memory_usage_mb.toFixed(1) + ' MB',
                            change: currentMetrics.system_health.memory_usage_mb < 500 ? 'Stable' : 'High',
                            type: currentMetrics.system_health.memory_usage_mb < 500 ? 'good' : 'warning',
                            icon: '🧠'
                        },
                        {
                            title: 'CPU Usage',
                            value: currentMetrics.system_health.cpu_percent.toFixed(1) + '%',
                            change: currentMetrics.system_health.cpu_percent < 50 ? 'Low' : 'High',
                            type: currentMetrics.system_health.cpu_percent < 50 ? 'good' : 'warning',
                            icon: '⚙️'
                        },
                        {
                            title: 'Validation Pass Rate',
                            value: (currentMetrics.validation.pass_rate * 100).toFixed(1) + '%',
                            change: currentMetrics.validation.pass_rate > 0.95 ? '+1%' : '-3%',
                            type: currentMetrics.validation.pass_rate > 0.95 ? 'good' : 'warning',
                            icon: '🔍'
                        }
                    ];

                    statsGrid.innerHTML = stats.map(stat => `
                        <div class="stat-card ${stat.type}">
                            <div class="stat-title">${stat.icon} ${stat.title}</div>
                            <div class="stat-value">${stat.value}</div>
                            <div class="stat-change ${stat.change.startsWith('+') || stat.change === 'Stable' || stat.change === 'Low' || stat.change === '100%' ? 'positive' : 'negative'}">
                                ${stat.change}
                            </div>
                        </div>
                    `).join('');
                }

                // Format uptime
                function formatUptime(seconds) {
                    const days = Math.floor(seconds / 86400);
                    const hours = Math.floor((seconds % 86400) / 3600);
                    const minutes = Math.floor((seconds % 3600) / 60);

                    if (days > 0) return `${days}d ${hours}h`;
                    if (hours > 0) return `${hours}h ${minutes}m`;
                    return `${minutes}m`;
                }

                // Update charts with historical data
                function updateCharts() {
                    if (historicalMetrics.length === 0) return;

                    // Query Performance Chart
                    updateQueryChart();

                    // Optimization Chart
                    updateOptimizationChart();

                    // Health Chart
                    updateHealthChart();

                    // Cost Chart
                    updateCostChart();
                }

                function updateQueryChart() {
                    const ctx = document.getElementById('queryChart').getContext('2d');

                    const labels = historicalMetrics.map(m =>
                        new Date(m.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})
                    );

                    const successData = historicalMetrics.map(m => m.execution.successful_queries);
                    const failedData = historicalMetrics.map(m => m.execution.failed_queries);
                    const responseTimeData = historicalMetrics.map(m => m.execution.avg_response_time);

                    if (charts.queryChart) {
                        charts.queryChart.destroy();
                    }

                    charts.queryChart = new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: labels,
                            datasets: [
                                {
                                    label: 'Successful Queries',
                                    data: successData,
                                    borderColor: '#4CAF50',
                                    backgroundColor: 'rgba(76, 175, 80, 0.1)',
                                    fill: true,
                                    tension: 0.4
                                },
                                {
                                    label: 'Failed Queries',
                                    data: failedData,
                                    borderColor: '#F44336',
                                    backgroundColor: 'rgba(244, 67, 54, 0.1)',
                                    fill: true,
                                    tension: 0.4
                                },
                                {
                                    label: 'Avg Response Time (s)',
                                    data: responseTimeData,
                                    borderColor: '#2196F3',
                                    backgroundColor: 'rgba(33, 150, 243, 0.1)',
                                    fill: true,
                                    tension: 0.4,
                                    yAxisID: 'y1'
                                }
                            ]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: {
                                y: {
                                    type: 'linear',
                                    display: true,
                                    position: 'left',
                                    title: {
                                        display: true,
                                        text: 'Query Count'
                                    }
                                },
                                y1: {
                                    type: 'linear',
                                    display: true,
                                    position: 'right',
                                    title: {
                                        display: true,
                                        text: 'Response Time (s)'
                                    },
                                    grid: {
                                        drawOnChartArea: false
                                    }
                                }
                            }
                        }
                    });
                }

                function updateOptimizationChart() {
                    const ctx = document.getElementById('optimizationChart').getContext('2d');

                    const labels = historicalMetrics.map(m =>
                        new Date(m.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})
                    );

                    const successRateData = historicalMetrics.map(m => m.optimization.success_rate * 100);
                    const optimizationTimeData = historicalMetrics.map(m => m.optimization.avg_optimization_time);

                    if (charts.optimizationChart) {
                        charts.optimizationChart.destroy();
                    }

                    charts.optimizationChart = new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: labels,
                            datasets: [
                                {
                                    label: 'Success Rate (%)',
                                    data: successRateData,
                                    backgroundColor: 'rgba(76, 175, 80, 0.7)',
                                    borderColor: '#4CAF50',
                                    borderWidth: 1,
                                    yAxisID: 'y'
                                },
                                {
                                    label: 'Avg Time (s)',
                                    data: optimizationTimeData,
                                    backgroundColor: 'rgba(33, 150, 243, 0.7)',
                                    borderColor: '#2196F3',
                                    borderWidth: 1,
                                    type: 'line',
                                    yAxisID: 'y1'
                                }
                            ]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    max: 100,
                                    title: {
                                        display: true,
                                        text: 'Success Rate (%)'
                                    }
                                },
                                y1: {
                                    type: 'linear',
                                    display: true,
                                    position: 'right',
                                    title: {
                                        display: true,
                                        text: 'Time (s)'
                                    },
                                    grid: {
                                        drawOnChartArea: false
                                    }
                                }
                            }
                        }
                    });
                }

                function updateHealthChart() {
                    const ctx = document.getElementById('healthChart').getContext('2d');

                    const labels = historicalMetrics.map(m =>
                        new Date(m.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})
                    );

                    const memoryData = historicalMetrics.map(m => m.system_health.memory_usage_mb);
                    const cpuData = historicalMetrics.map(m => m.system_health.cpu_percent);

                    if (charts.healthChart) {
                        charts.healthChart.destroy();
                    }

                    charts.healthChart = new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: labels,
                            datasets: [
                                {
                                    label: 'Memory Usage (MB)',
                                    data: memoryData,
                                    borderColor: '#FF9800',
                                    backgroundColor: 'rgba(255, 152, 0, 0.1)',
                                    fill: true,
                                    tension: 0.4
                                },
                                {
                                    label: 'CPU Usage (%)',
                                    data: cpuData,
                                    borderColor: '#9C27B0',
                                    backgroundColor: 'rgba(156, 39, 176, 0.1)',
                                    fill: true,
                                    tension: 0.4,
                                    yAxisID: 'y1'
                                }
                            ]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: {
                                y: {
                                    title: {
                                        display: true,
                                        text: 'Memory (MB)'
                                    }
                                },
                                y1: {
                                    type: 'linear',
                                    display: true,
                                    position: 'right',
                                    max: 100,
                                    title: {
                                        display: true,
                                        text: 'CPU (%)'
                                    },
                                    grid: {
                                        drawOnChartArea: false
                                    }
                                }
                            }
                        }
                    });
                }

                function updateCostChart() {
                    const ctx = document.getElementById('costChart').getContext('2d');

                    // Get unique models from cost data
                    const models = new Set();
                    historicalMetrics.forEach(m => {
                        Object.keys(m.cost.cost_by_model).forEach(model => models.add(model));
                    });

                    const labels = historicalMetrics.map(m =>
                        new Date(m.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})
                    );

                    const datasets = Array.from(models).map((model, index) => {
                        const colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40'];
                        return {
                            label: model,
                            data: historicalMetrics.map(m => m.cost.cost_by_model[model] || 0),
                            backgroundColor: colors[index % colors.length],
                            borderColor: colors[index % colors.length],
                            fill: false,
                            tension: 0.4
                        };
                    });

                    if (charts.costChart) {
                        charts.costChart.destroy();
                    }

                    charts.costChart = new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: labels,
                            datasets: datasets
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    title: {
                                        display: true,
                                        text: 'Cost ($)'
                                    }
                                }
                            }
                        }
                    });
                }

                // Initial load
                loadHistoricalMetrics();
            </script>
        </body>
        </html>
        """

        html_file = self.static_dir / "dashboard.html"
        html_file.write_text(html)

    def _get_dashboard_html(self) -> str:
        """Get dashboard HTML content"""
        html_file = self.static_dir / "dashboard.html"
        return html_file.read_text()

    def start(self):
        """Start the dashboard server"""
        uvicorn.run(self.app, host=self.host, port=self.port)

    async def start_async(self):
        """Start the dashboard server asynchronously"""
        config = uvicorn.Config(self.app, host=self.host, port=self.port)
        server = uvicorn.Server(config)
        await server.serve()
