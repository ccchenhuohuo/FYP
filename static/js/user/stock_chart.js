/**
 * 股票历史数据可视化脚本
 * 用于获取和展示股票的历史价格走势图，以及蒙特卡洛模拟预测
 */

// 全局变量
let stockChart = null; // 图表实例
let currentData = null; // 当前加载的数据
let monteCarloData = null; // 蒙特卡洛模拟数据
let viewMode = 'history'; // 视图模式：'history'(历史数据)或'simulation'(模拟数据)
let completeHistoricalData = null; // 存储完整的历史数据

/**
 * 页面加载完成后初始化
 */
document.addEventListener('DOMContentLoaded', function() {
    // 获取DOM元素
    const stockSelector = document.getElementById('stockSelector');
    const timeRange = document.getElementById('timeRange');
    const customDateRange = document.getElementById('customDateRange');
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');
    const applyDateRangeBtn = document.getElementById('applyDateRange');
    const simulateButton = document.getElementById('simulateButton');
    const historyModeBtn = document.getElementById('historyModeBtn');
    const simulationModeBtn = document.getElementById('simulationModeBtn');
    
    // 添加事件监听器
    stockSelector.addEventListener('change', updateChart);
    timeRange.addEventListener('change', function() {
        if (this.value === 'custom') {
            customDateRange.style.display = 'flex';
            // 如果已经有完整的历史数据，则设置日期选择器的默认值
            if (completeHistoricalData && completeHistoricalData.length > 0) {
                const firstDate = new Date(completeHistoricalData[0].date);
                const lastDate = new Date(completeHistoricalData[completeHistoricalData.length - 1].date);
                
                startDateInput.value = formatDateForInput(firstDate);
                endDateInput.value = formatDateForInput(lastDate);
            }
        } else {
            customDateRange.style.display = 'none';
            updateChart();
        }
    });
    
    applyDateRangeBtn.addEventListener('click', function() {
        updateChartWithCustomDateRange();
    });
    
    simulateButton.addEventListener('click', runMonteCarloSimulation);
    
    // 添加视图模式切换事件监听
    if (historyModeBtn) {
        historyModeBtn.addEventListener('click', function() {
            setViewMode('history');
        });
    }
    
    if (simulationModeBtn) {
        simulationModeBtn.addEventListener('click', function() {
            setViewMode('simulation');
        });
    }
    
    // 初始加载图表
    loadStockData('AAPL', 'all');
    
    // 设置日期选择器的默认范围
    // 默认开始日期为当前日期的一年前
    const defaultEndDate = new Date();
    const defaultStartDate = new Date();
    defaultStartDate.setFullYear(defaultStartDate.getFullYear() - 1);
    
    startDateInput.value = formatDateForInput(defaultStartDate);
    endDateInput.value = formatDateForInput(defaultEndDate);
    
    // 添加实时数据监听器
    addRealTimeDataListeners();
    
    // 加载初始股票的实时数据
    const initialSymbol = document.getElementById('stockSelector').value;
    fetchRealTimeData(initialSymbol);
});

/**
 * 设置视图模式并更新图表
 * @param {string} mode - 视图模式 ('history' 或 'simulation')
 */
function setViewMode(mode) {
    viewMode = mode;
    
    // 更新按钮状态
    const historyBtn = document.getElementById('historyModeBtn');
    const simulationBtn = document.getElementById('simulationModeBtn');
    
    if (historyBtn && simulationBtn) {
        if (mode === 'history') {
            historyBtn.classList.add('active');
            simulationBtn.classList.remove('active');
        } else {
            historyBtn.classList.remove('active');
            simulationBtn.classList.add('active');
        }
    }
    
    // 如果已经有蒙特卡洛数据，则更新图表
    if (monteCarloData) {
        updateChartWithSimulation();
    }
}

/**
 * 加载股票数据
 * @param {string} ticker - 股票代码
 * @param {string} range - 时间范围
 * @param {Object} [dateRange] - 自定义日期范围 {startDate, endDate}
 */
function loadStockData(ticker, range, dateRange) {
    // 显示加载信息
    document.getElementById('loadingMessage').style.display = 'block';
    document.getElementById('errorMessage').style.display = 'none';
    
    // 构建API URL
    let url = `/user/api/market_data?ticker=${ticker}&range=${range}`;
    
    // 如果是自定义日期范围
    if (range === 'custom' && dateRange) {
        url += `&start_date=${dateRange.startDate}&end_date=${dateRange.endDate}`;
    }
    
    // 发送AJAX请求
    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error('网络响应失败');
            }
            return response.json();
        })
        .then(data => {
            // 保存完整的历史数据
            if (range === 'all' || !completeHistoricalData) {
                completeHistoricalData = [...data];
            }
            
            // 根据选定的时间范围在前端对数据进行筛选
            let filteredData = data;
            
            // 如果不是全部数据，并且完整历史数据已存在，则进行前端筛选
            if (range !== 'all' && completeHistoricalData && completeHistoricalData.length > 0) {
                const today = new Date();
                let startDate;
                
                // 根据时间范围计算开始日期
                switch(range) {
                    case '1m':
                        startDate = new Date(today);
                        startDate.setMonth(startDate.getMonth() - 1);
                        break;
                    case '3m':
                        startDate = new Date(today);
                        startDate.setMonth(startDate.getMonth() - 3);
                        break;
                    case '6m':
                        startDate = new Date(today);
                        startDate.setMonth(startDate.getMonth() - 6);
                        break;
                    case '1y':
                        startDate = new Date(today);
                        startDate.setFullYear(startDate.getFullYear() - 1);
                        break;
                    case 'custom':
                        if (dateRange) {
                            startDate = new Date(dateRange.startDate);
                            const endDateObj = new Date(dateRange.endDate);
                            // 对于自定义日期范围，我们需要额外筛选结束日期
                            filteredData = completeHistoricalData.filter(item => {
                                const itemDate = new Date(item.date);
                                return itemDate >= startDate && itemDate <= endDateObj;
                            });
                            break;
                        }
                        // 如果没有提供有效的日期范围，则默认回退到显示全部数据
                        filteredData = completeHistoricalData;
                        break;
                    default:
                        // 默认使用所有数据
                        filteredData = completeHistoricalData;
                }
                
                // 对于非自定义日期范围，只筛选开始日期
                if (range !== 'custom') {
                    filteredData = completeHistoricalData.filter(item => {
                        return new Date(item.date) >= startDate;
                    });
                }
            }
            
            // 保存当前筛选后的数据
            currentData = filteredData;
            
            // 更新图表
            renderChart(filteredData);
            
            // 隐藏加载信息
            document.getElementById('loadingMessage').style.display = 'none';
        })
        .catch(error => {
            // 显示错误信息
            document.getElementById('loadingMessage').style.display = 'none';
            document.getElementById('errorMessage').style.display = 'block';
            document.getElementById('errorMessage').textContent = `获取数据失败: ${error.message}`;
            console.error('获取数据失败:', error);
        });
}

/**
 * 根据用户选择更新图表
 */
function updateChart() {
    const ticker = document.getElementById('stockSelector').value;
    const range = document.getElementById('timeRange').value;
    
    // 如果选择的是自定义日期范围，但没有点击应用按钮，则不更新图表
    if (range === 'custom') {
        document.getElementById('customDateRange').style.display = 'flex';
        return;
    }
    
    // 重置模拟数据
    resetSimulationData();
    
    // 加载股票数据
    loadStockData(ticker, range);
}

/**
 * 根据自定义日期范围更新图表
 */
function updateChartWithCustomDateRange() {
    const ticker = document.getElementById('stockSelector').value;
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    
    // 验证日期输入
    if (!startDate || !endDate) {
        alert('请选择开始和结束日期');
        return;
    }
    
    // 验证开始日期不晚于结束日期
    if (new Date(startDate) > new Date(endDate)) {
        alert('开始日期不能晚于结束日期');
        return;
    }
    
    // 重置模拟数据
    resetSimulationData();
    
    // 加载自定义日期范围的数据
    loadStockData(ticker, 'custom', {
        startDate: startDate,
        endDate: endDate
    });
}

/**
 * 重置模拟数据
 */
function resetSimulationData() {
    monteCarloData = null;
    document.getElementById('viewModeToggle').style.display = 'none';
    document.getElementById('simulationStats').style.display = 'none';
}

/**
 * 渲染股票价格走势图
 * @param {Object[]} data - 股票数据数组
 */
function renderChart(data) {
    // 准备数据
    const dates = data.map(item => formatDate(new Date(item.date)));
    const prices = data.map(item => item.close);
    const volumes = data.map(item => item.volume);
    
    // 获取Canvas元素
    const ctx = document.getElementById('stockChart').getContext('2d');
    
    // 销毁旧图表（如果存在）
    if (stockChart) {
        stockChart.destroy();
    }
    
    // 创建新图表
    stockChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [
                {
                    label: '历史价格',
                    data: prices,
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1,
                    yAxisID: 'y',
                },
                {
                    label: '交易量',
                    data: volumes,
                    borderColor: 'rgb(153, 102, 255)',
                    backgroundColor: 'rgba(153, 102, 255, 0.2)',
                    type: 'bar',
                    yAxisID: 'y1',
                }
            ]
        },
        options: {
            responsive: true,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    filter: function(tooltipItem) {
                        // 不显示模拟路径的详细信息，除非是平均预测价格
                        if (tooltipItem.dataset.simulationPath && tooltipItem.dataset.label !== '平均预测价格') {
                            return false;
                        }
                        return true;
                    }
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: '价格 ($)'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: '交易量'
                    },
                    grid: {
                        drawOnChartArea: false,
                    },
                }
            }
        }
    });
}

/**
 * 运行蒙特卡洛模拟
 */
async function runMonteCarloSimulation() {
    const ticker = document.getElementById('stockSelector').value;
    const days = document.getElementById('simulationDays').value;
    const simulations = document.getElementById('simulationCount').value;
    
    try {
        // 显示加载提示
        document.getElementById('loadingMessage').textContent = '正在运行蒙特卡洛模拟...';
        document.getElementById('loadingMessage').style.display = 'block';
        
        const response = await fetch(`/api/monte-carlo/${ticker}?days=${days}&simulations=${simulations}`);
        const data = await response.json();
        
        // 隐藏加载提示
        document.getElementById('loadingMessage').style.display = 'none';
        
        if (data.status === 'success') {
            console.log("模拟数据获取成功:", data.data);
            monteCarloData = data.data;
            
            // 检查必要的字段是否存在
            if (!monteCarloData.dates || !Array.isArray(monteCarloData.dates)) {
                console.error("模拟数据缺少必要的日期字段", monteCarloData);
                alert("模拟数据缺少必要的日期字段，请联系管理员");
                return;
            }
            
            // 自动切换到模拟模式
            setViewMode('simulation');
            
            // 更新图表
            updateChartWithSimulation();
            displaySimulationStats();
            
            // 显示视图模式切换按钮
            document.getElementById('viewModeToggle').style.display = 'flex';
        } else {
            alert('模拟失败: ' + data.message);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('请求失败，请稍后重试');
    }
}

/**
 * 使用模拟数据更新图表
 */
function updateChartWithSimulation() {
    if (!monteCarloData || !currentData || !Array.isArray(currentData) || currentData.length === 0) {
        console.error("模拟数据或当前数据不可用", {monteCarloData, currentData});
        alert("请先选择股票并加载历史数据后再进行模拟");
        return;
    }

    // 检查monteCarloData中是否有必要的字段
    if (!monteCarloData.dates || !Array.isArray(monteCarloData.dates)) {
        console.error("模拟数据格式不正确，缺少dates字段", monteCarloData);
        alert("模拟数据格式不正确，请联系管理员");
        return;
    }

    // 获取当前数据（已经根据时间范围过滤后的数据）
    let historicalDates = [...currentData.map(item => formatDate(new Date(item.date)))];
    let historicalPrices = [...currentData.map(item => item.close)];
    let volumes = [...currentData.map(item => item.volume)];

    // 在模拟模式下，只显示最近的历史数据以使图表清晰
    const displayHistoryDays = 60; // 可调整的常数
    if (viewMode === 'simulation' && historicalDates.length > displayHistoryDays) {
        historicalDates = historicalDates.slice(-displayHistoryDays);
        historicalPrices = historicalPrices.slice(-displayHistoryDays);
        volumes = volumes.slice(-displayHistoryDays);
    }

    // 准备模拟数据，确保从最后一个历史数据点开始
    const lastHistoricalDate = new Date(currentData[currentData.length - 1].date);
    const simulationDates = monteCarloData.dates.map(d => formatDate(new Date(d)));
    const allDates = [...historicalDates, ...simulationDates];

    // 基础数据集
    const datasets = [];
    
    // 根据视图模式确定历史数据的显示方式
    const historyOpacity = viewMode === 'history' ? 1 : 0.5;
    
    // 历史价格数据
    datasets.push({
        label: '历史价格',
        data: historicalPrices,
        borderColor: `rgba(75, 192, 192, ${historyOpacity})`,
        tension: 0.1,
        yAxisID: 'y',
        borderWidth: viewMode === 'history' ? 2 : 1
    });
    
    // 交易量数据
    datasets.push({
        label: '交易量',
        data: [...volumes, ...Array(simulationDates.length).fill(null)],
        borderColor: 'rgb(153, 102, 255)',
        backgroundColor: 'rgba(153, 102, 255, 0.2)',
        type: 'bar',
        yAxisID: 'y1'
    });

    // 根据视图模式确定模拟路径的显示方式
    const pathsToShow = viewMode === 'simulation' ? 500 : 50;
    
    // 生成一组彩色但半透明的颜色
    const colors = [
        'rgba(255, 99, 132, 0.3)',   // 红色
        'rgba(54, 162, 235, 0.3)',   // 蓝色
        'rgba(255, 206, 86, 0.3)',   // 黄色
        'rgba(75, 192, 192, 0.3)',   // 青色
        'rgba(153, 102, 255, 0.3)',  // 紫色
        'rgba(255, 159, 64, 0.3)',   // 橙色
        'rgba(199, 199, 199, 0.3)',  // 灰色
        'rgba(83, 102, 255, 0.3)',   // 蓝紫色
        'rgba(255, 99, 71, 0.3)',    // 番茄色
        'rgba(50, 205, 50, 0.3)'     // 绿色
    ];
    
    // 添加模拟路径，但不显示在图例中
    if (monteCarloData.all_paths && Array.isArray(monteCarloData.all_paths)) {
        monteCarloData.all_paths.forEach((path, index) => {
            if (index < pathsToShow && Array.isArray(path)) {
                const colorIndex = index % colors.length;
                datasets.push({
                    label: `模拟路径`,
                    data: [...Array(historicalPrices.length).fill(null), ...path],
                    borderColor: colors[colorIndex],
                    borderWidth: 1,
                    pointRadius: 0,
                    tension: 0.1,
                    yAxisID: 'y',
                    simulationPath: true,
                    hidden: viewMode === 'history',
                    showLine: true,
                    // 不在图例中显示
                    display: false
                });
            }
        });
    }

    // 添加平均预测线，始终显示
    const meanPath = simulationDates.map((_, i) => {
        return monteCarloData.all_paths.reduce((sum, path) => sum + path[i], 0) / monteCarloData.all_paths.length;
    });

    datasets.push({
        label: '平均预测价格',
        data: [...Array(historicalPrices.length).fill(null), ...meanPath],
        borderColor: 'rgba(255, 99, 132, 1)',
        borderWidth: 2,
        pointRadius: 0,
        tension: 0.1,
        yAxisID: 'y',
        hidden: false // 始终显示
    });

    // 更新图表数据
    stockChart.data.labels = allDates;
    stockChart.data.datasets = datasets;
    
    // 更新图表选项
    stockChart.options.plugins.legend = {
        display: true,
        position: 'top',
        labels: {
            filter: function(legendItem, chartData) {
                // 只显示主要数据集的图例项
                return !legendItem.text.includes('模拟路径');
            }
        }
    };
    
    // 更新图表
    stockChart.update();
}

/**
 * 显示模拟统计结果
 */
function displaySimulationStats() {
    if (!monteCarloData) {
        console.error("无模拟数据可显示");
        return;
    }
    
    // 检查必要的字段
    if (typeof monteCarloData.mean_price === 'undefined' || 
        typeof monteCarloData.percentile_5 === 'undefined' || 
        typeof monteCarloData.percentile_95 === 'undefined') {
        console.error("模拟数据缺少必要的统计字段", monteCarloData);
        return;
    }
    
    const statsDiv = document.getElementById('simulationStats');
    statsDiv.style.display = 'block';
    statsDiv.innerHTML = `
        <div class="row">
            <div class="col-md-4">
                <div class="data-item">
                    <h4><i class="fas fa-calculator"></i> 预测平均价格</h4>
                    <p class="value text-primary">$${monteCarloData.mean_price.toFixed(2)}</p>
                </div>
            </div>
            <div class="col-md-4">
                <div class="data-item">
                    <h4><i class="fas fa-chart-area"></i> 90% 置信区间下限</h4>
                    <p class="value text-danger">$${monteCarloData.percentile_5.toFixed(2)}</p>
                </div>
            </div>
            <div class="col-md-4">
                <div class="data-item">
                    <h4><i class="fas fa-chart-line"></i> 90% 置信区间上限</h4>
                    <p class="value text-success">$${monteCarloData.percentile_95.toFixed(2)}</p>
                </div>
            </div>
        </div>
        <div class="mt-3 text-center">
            <small class="text-muted">基于 ${monteCarloData.all_paths ? monteCarloData.all_paths.length : '多'} 次蒙特卡洛模拟计算的结果</small>
        </div>
    `;
}

/**
 * 格式化日期为YYYY-MM-DD格式
 * @param {Date} date - 日期对象
 * @returns {string} - 格式化后的日期字符串
 */
function formatDate(date) {
    if (!date) return '-';
    
    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    
    return `${year}-${month}-${day}`;
}

/**
 * 格式化日期为HTML日期输入框格式YYYY-MM-DD
 * @param {Date} date - 日期对象
 * @returns {string} 格式化后的日期字符串
 */
function formatDateForInput(date) {
    return formatDate(date);
}

// 添加获取实时股票数据的函数
async function fetchRealTimeData(symbol) {
    // 显示加载中状态
    document.getElementById('loadingRealTimeData').style.display = 'block';
    document.getElementById('realTimeDataError').style.display = 'none';
    document.getElementById('realTimeDataContent').style.display = 'none';
    
    try {
        // 使用正确的路径，包含/user前缀（与Flask蓝图配置匹配）
        const url = `/user/api/real_time_stock_data?symbol=${symbol}`;
        
        // 发送请求
        const response = await fetch(url);
        
        // 检查HTTP状态码
        if (response.status === 429) {
            throw new Error('API请求次数限制已达到，请稍后再试。Alpha Vantage免费API每天限制25次请求。');
        } else if (!response.ok) {
            throw new Error(`网络响应错误：状态码 ${response.status}`);
        }
        
        const data = await response.json();
        
        // 检查是否有错误
        if (data.error) {
            // 检查是否是API限制错误
            if (data.error.includes('API rate limit') || data.error.includes('standard API rate limit')) {
                throw new Error(`API请求限制：${data.error}。请考虑升级API计划或等待限制重置。`);
            } else {
                throw new Error(data.error);
            }
        }
        
        // 检查是否有全局报价数据
        if (!data['Global Quote'] || Object.keys(data['Global Quote']).length === 0) {
            throw new Error('无法获取股票数据');
        }
        
        // 提取所需数据
        const quote = data['Global Quote'];
        const price = parseFloat(quote['05. price']).toFixed(2);
        const previousClose = parseFloat(quote['08. previous close']).toFixed(2);
        const change = parseFloat(quote['09. change']).toFixed(2);
        const changePercent = quote['10. change percent'].replace('%', '');
        const volume = parseInt(quote['06. volume']).toLocaleString();
        const highPrice = parseFloat(quote['03. high']).toFixed(2);
        const lowPrice = parseFloat(quote['04. low']).toFixed(2);
        
        // 更新DOM
        document.getElementById('rtPrice').textContent = price;
        document.getElementById('rtPriceChange').textContent = `${change} (${changePercent}%)`;
        document.getElementById('rtPriceChange').className = parseFloat(change) >= 0 ? 'change positive' : 'change negative';
        document.getElementById('rtVolume').textContent = volume;
        document.getElementById('rtHigh').textContent = highPrice;
        document.getElementById('rtLow').textContent = lowPrice;
        
        // 更新最后更新时间
        const now = new Date();
        document.getElementById('lastUpdated').textContent = `最后更新: ${now.toLocaleTimeString()}`;
        
        // 显示数据内容
        document.getElementById('loadingRealTimeData').style.display = 'none';
        document.getElementById('realTimeDataContent').style.display = 'block';
    } catch (error) {
        console.error('获取实时数据失败:', error);
        
        // 显示错误信息
        document.getElementById('loadingRealTimeData').style.display = 'none';
        document.getElementById('realTimeDataError').style.display = 'block';
        
        // 检查是否是API限制错误，提供更友好的消息
        let errorMessage = error.message;
        if (errorMessage.includes('API请求限制') || errorMessage.includes('API请求次数限制')) {
            document.getElementById('realTimeDataError').className = 'alert alert-warning';
            document.getElementById('realTimeDataError').innerHTML = `
                <strong>API限制提醒:</strong> ${errorMessage}<br>
                <small>建议：使用限价单交易，或等待明天API限制重置。</small>
            `;
        } else {
            document.getElementById('realTimeDataError').className = 'alert alert-danger';
            document.getElementById('realTimeDataError').textContent = `获取实时数据失败: ${errorMessage}`;
        }
    }
}

// 在股票选择器变化时更新实时数据
function addRealTimeDataListeners() {
    // 添加刷新按钮的事件监听器
    document.getElementById('refreshRealTimeData').addEventListener('click', function() {
        const symbol = document.getElementById('stockSelector').value;
        fetchRealTimeData(symbol);
    });
    
    // 在选择新股票时更新实时数据
    document.getElementById('stockSelector').addEventListener('change', function() {
        const symbol = this.value;
        fetchRealTimeData(symbol);
    });
} 