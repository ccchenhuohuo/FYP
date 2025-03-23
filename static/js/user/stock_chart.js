/**
 * 股票历史数据可视化脚本
 * 用于获取和展示股票的历史价格走势图，以及蒙特卡洛模拟预测
 */

// 全局变量
let stockChart = null; // 图表实例
let currentData = null; // 当前加载的数据
let monteCarloData = null; // 蒙特卡洛模拟数据
let viewMode = 'simulation'; // 视图模式：'history'(历史数据)或'simulation'(模拟数据)
let completeHistoricalData = null; // 存储完整的历史数据

// 添加全局函数用于视图模式切换
window.updateChartViewMode = function(mode) {
    viewMode = mode;
    if (stockChart && monteCarloData) {
        updateChartWithSimulation();
    }
};

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
        // 更新按钮文本和图标
        historyModeBtn.innerHTML = '<i class="fas fa-history"></i> 历史数据视图';
        historyModeBtn.addEventListener('click', function() {
            setViewMode('history');
        });
    }
    
    if (simulationModeBtn) {
        // 更新按钮文本和图标
        simulationModeBtn.innerHTML = '<i class="fas fa-chart-line"></i> 模拟预测视图';
        simulationModeBtn.addEventListener('click', function() {
            setViewMode('simulation');
        });
    }
    
    // 监听蒙特卡洛模拟事件
    document.addEventListener('monte-carlo-ready', function() {
        // 如果全局变量中存在蒙特卡洛模拟数据，更新图表
        if (window.monteCarloData) {
            monteCarloData = window.monteCarloData;
            updateChartWithSimulation();
        }
    });
    
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
    
    // 初始化实时数据功能
    addRealTimeDataListeners();
    
    // 初始化时间范围选择
    initTimeRangeSelector();
    
    // 初始化图表
    initStockChart();
    
    // 设置初始视图模式
    // 注意：确保这行代码在按钮初始化后执行
    setViewMode(viewMode); // 使用全局变量中的初始视图模式
    
    console.log('所有功能初始化完成');

    // 获取订单表单
    const orderForm = document.getElementById('orderForm');
    if (orderForm) {
        // 监听表单提交事件
        orderForm.addEventListener('submit', async function(e) {
            e.preventDefault(); // 阻止表单默认提交
            console.log('订单表单提交事件触发');
            
            // 获取表单数据
            const ticker = document.getElementById('stockSelector').value;  // 使用stockSelector的值
            const orderType = document.getElementById('order_type').value;
            const executionType = document.getElementById('order_execution_type').value;
            const price = executionType === 'market' ? null : parseFloat(document.getElementById('price').value);
            const quantity = parseInt(document.getElementById('quantity').value);
            
            console.log('获取到的原始表单数据:', {
                ticker, orderType, executionType, price, quantity
            });
            
            // 验证数据
            if (!ticker) {
                console.log('验证失败: 未选择股票');
                alert('请选择股票');
                return;
            }
            
            if (isNaN(quantity) || quantity <= 0) {
                console.log('验证失败: 无效的数量');
                alert('请输入有效的数量');
                return;
            }
            
            if (executionType === 'limit' && (isNaN(price) || price <= 0)) {
                console.log('验证失败: 无效的价格');
                alert('请输入有效的价格');
                return;
            }
            
            const requestData = {
                ticker: ticker,
                order_type: orderType,
                order_execution_type: executionType,
                order_price: price,
                order_quantity: quantity
            };
            
            console.log('验证通过，准备发送的订单数据:', requestData);
            
            try {
                console.log('开始发送API请求到:', '/user/api/create_order');
                // 发送API请求
                const response = await fetch('/user/api/create_order', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(requestData)
                });
                
                console.log('API响应状态:', response.status);
                console.log('API响应头:', Object.fromEntries(response.headers.entries()));
                
                const data = await response.json();
                console.log('API响应数据:', data);
                
                if (response.ok) {
                    alert('订单创建成功！');
                    // 重置表单
                    orderForm.reset();
                    // 刷新页面以显示新订单
                    location.reload();
                } else {
                    alert(data.error || '创建订单失败');
                }
            } catch (error) {
                console.error('请求错误详情:', error);
                console.error('错误堆栈:', error.stack);
                alert('创建订单时发生错误');
            }
        });
        
        // 监听执行类型变化
        const executionTypeSelect = document.getElementById('order_execution_type');
        const priceField = document.querySelector('.price-field');
        
        executionTypeSelect.addEventListener('change', function() {
            console.log('执行类型变更为:', this.value);
            if (this.value === 'market') {
                priceField.style.display = 'none';
                document.getElementById('price').removeAttribute('required');
                document.getElementById('price').value = '';  // 清空价格输入
            } else {
                priceField.style.display = 'block';
                document.getElementById('price').setAttribute('required', 'required');
            }
        });
    }
});

/**
 * 设置视图模式并更新图表
 * @param {string} mode - 视图模式 ('history' 或 'simulation')
 */
function setViewMode(mode) {
    console.log(`切换视图模式: ${viewMode} => ${mode}`);
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
        // 显示或隐藏相关UI元素
        const simulationStatsDiv = document.getElementById('simulationStats');
        if (simulationStatsDiv) {
            simulationStatsDiv.style.display = viewMode === 'simulation' ? 'block' : 'none';
        }
        
        // 获取当前选择的股票和时间范围
        const ticker = document.getElementById('stockSelector').value;
        const range = document.getElementById('timeRange').value;
        
        // 如果是历史模式，考虑重新加载完整的历史数据
        if (mode === 'history' && completeHistoricalData) {
            console.log(`历史模式: 重新加载 ${ticker} 的完整历史数据`);
            // 使用完整历史数据更新图表，同时保持模拟数据
            currentData = [...completeHistoricalData];
            // 更新带有模拟数据的图表
            updateChartWithSimulation();
        } else {
            // 直接更新图表，使用现有数据
            updateChartWithSimulation();
        }
    } else {
        console.log("无蒙特卡洛模拟数据可显示");
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
    
    console.log(`正在获取股票数据: ${url}`); // 调试日志
    
    // 发送AJAX请求
    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error('网络响应失败');
            }
            return response.json();
        })
        .then(data => {
            console.log(`收到 ${ticker} 的数据: ${data.length} 条记录`); // 调试日志
            console.log(`数据时间范围: ${data.length > 0 ? data[0].date : '无'} 至 ${data.length > 0 ? data[data.length-1].date : '无'}`);
            
            // 保存完整的历史数据
            if (range === 'all' || !completeHistoricalData) {
                completeHistoricalData = [...data];
                console.log(`已保存 ${completeHistoricalData.length} 条完整历史数据`);
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
                            console.log(`自定义日期范围筛选后: ${filteredData.length} 条记录`);
                            break;
                        }
                        // 如果没有提供有效的日期范围，则默认回退到显示全部数据
                        filteredData = completeHistoricalData;
                        console.log(`使用完整历史数据: ${filteredData.length} 条记录`);
                        break;
                    default:
                        // 默认使用所有数据
                        filteredData = completeHistoricalData;
                        console.log(`默认使用完整历史数据: ${filteredData.length} 条记录`);
                }
                
                // 对于非自定义日期范围，只筛选开始日期
                if (range !== 'custom') {
                    filteredData = completeHistoricalData.filter(item => {
                        return new Date(item.date) >= startDate;
                    });
                    console.log(`时间范围 ${range} 筛选后: ${filteredData.length} 条记录`);
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
        
        // 调用API
        const response = await fetch(`/user/api/monte-carlo/${ticker}?days=${days}&simulations=${simulations}`);
        
        // 隐藏加载提示
        document.getElementById('loadingMessage').style.display = 'none';
        
        // 检查响应状态
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `服务器返回错误: ${response.status}`);
        }
        
        // 解析数据
        const data = await response.json();
        console.log("蒙特卡洛模拟数据:", data);
        
        // 检查数据格式
        if (!data || !data.dates || !Array.isArray(data.dates) || !data.all_paths || !Array.isArray(data.all_paths)) {
            throw new Error("接收到的数据格式无效，缺少必要字段");
        }
        
        // 保存模拟数据
        monteCarloData = data;
        
        // 自动切换到模拟模式
        setViewMode('simulation');
        
        // 更新图表和统计数据
        updateChartWithSimulation();
        displaySimulationStats();
        
        // 显示视图模式切换按钮
        document.getElementById('viewModeToggle').style.display = 'flex';
    } catch (error) {
        console.error('蒙特卡洛模拟失败:', error);
        alert(`蒙特卡洛模拟失败: ${error.message}`);
    }
}

/**
 * 使用模拟数据更新图表
 */
function updateChartWithSimulation() {
    if (!monteCarloData || !currentData || !Array.isArray(currentData) || currentData.length === 0) {
        console.error("模拟数据或当前数据不可用", {monteCarloData, currentData});
        return;
    }

    // 检查必要字段
    if (!monteCarloData.dates || !Array.isArray(monteCarloData.dates) || 
        !monteCarloData.all_paths || !Array.isArray(monteCarloData.all_paths)) {
        console.error("模拟数据格式不正确", monteCarloData);
        return;
    }

    // 获取历史数据（根据视图模式决定显示多少历史数据）
    let historicalDates = [...currentData.map(item => formatDate(new Date(item.date)))];
    let historicalPrices = [...currentData.map(item => item.close)];
    let volumes = [...currentData.map(item => item.volume)];
    
    // 在历史模式下显示完整的历史数据，在模拟模式下仅显示最近60天数据
    const maxHistoryDays = viewMode === 'history' ? historicalDates.length : 60;
    if (historicalDates.length > maxHistoryDays && viewMode === 'simulation') {
        historicalDates = historicalDates.slice(-maxHistoryDays);
        historicalPrices = historicalPrices.slice(-maxHistoryDays);
        volumes = volumes.slice(-maxHistoryDays);
    }

    // 准备日期数据
    const simulationDates = monteCarloData.dates.map(d => formatDate(new Date(d)));
    const allDates = [...historicalDates, ...simulationDates];

    // 准备图表数据集
    const datasets = [];
    
    // 历史价格 - 根据模式调整样式
    datasets.push({
        label: '历史价格',
        data: historicalPrices,
        borderColor: viewMode === 'history' ? 'rgba(75, 192, 192, 1.0)' : 'rgba(75, 192, 192, 0.8)',
        borderWidth: viewMode === 'history' ? 3 : 2,
        pointRadius: viewMode === 'history' ? 2 : 0,
        tension: 0.1,
        yAxisID: 'y',
        fill: viewMode === 'history' ? {
            target: 'origin',
            above: 'rgba(75, 192, 192, 0.1)'
        } : false
    });
    
    // 交易量
    datasets.push({
        label: '交易量',
        data: [...volumes, ...Array(simulationDates.length).fill(null)],
        borderColor: 'rgb(153, 102, 255)',
        backgroundColor: 'rgba(153, 102, 255, 0.2)',
        type: 'bar',
        yAxisID: 'y1'
    });

    // 添加模拟路径 - 根据模式调整透明度和数量
    const pathOpacity = viewMode === 'simulation' ? 0.4 : 0.1;
    const pathsToShow = Math.min(monteCarloData.all_paths.length, viewMode === 'simulation' ? 500 : 30);
    
    // 颜色列表
    const colors = [
        `rgba(255, 99, 132, ${pathOpacity})`,   // 红色
        `rgba(54, 162, 235, ${pathOpacity})`,   // 蓝色
        `rgba(255, 206, 86, ${pathOpacity})`,   // 黄色
        `rgba(75, 192, 192, ${pathOpacity})`,   // 青色
        `rgba(153, 102, 255, ${pathOpacity})`,  // 紫色
        `rgba(255, 159, 64, ${pathOpacity})`,   // 橙色
        `rgba(199, 199, 199, ${pathOpacity})`,  // 灰色
        `rgba(83, 102, 255, ${pathOpacity})`,   // 蓝紫色
        `rgba(255, 99, 71, ${pathOpacity})`,    // 番茄色
        `rgba(50, 205, 50, ${pathOpacity})`     // 绿色
    ];
    
    // 添加所有路径
    for (let i = 0; i < pathsToShow; i++) {
        if (i < monteCarloData.all_paths.length) {
            const path = monteCarloData.all_paths[i];
            if (Array.isArray(path)) {
                const colorIndex = i % colors.length;
                datasets.push({
                    label: '模拟路径',
                    data: [...Array(historicalPrices.length).fill(null), ...path],
                    borderColor: colors[colorIndex],
                    borderWidth: viewMode === 'simulation' ? 1 : 0.5,
                    pointRadius: 0,
                    tension: 0.1,
                    yAxisID: 'y',
                    simulationPath: true,
                    hidden: false,
                    showLine: true,
                    display: false  // 不在图例中显示
                });
            }
        }
    }

    // 添加主要百分位数线
    const percentileColors = {
        'median': `rgba(255, 99, 132, ${viewMode === 'simulation' ? 1 : 0.5})`,     // 中位数 - 红色
        'p25_p75': `rgba(255, 159, 64, ${viewMode === 'simulation' ? 1 : 0.4})`,    // 25-75百分位 - 橙色
        'p5_p95': `rgba(54, 162, 235, ${viewMode === 'simulation' ? 1 : 0.4})`      // 5-95百分位 - 蓝色
    };
    
    // 计算每个时间点的中位数（50百分位）
    const medianLine = simulationDates.map((_, i) => {
        const values = monteCarloData.all_paths.map(path => path[i]);
        return values.sort((a, b) => a - b)[Math.floor(values.length / 2)];
    });
    
    // 添加中位数线
    datasets.push({
        label: '预测中位数',
        data: [...Array(historicalPrices.length).fill(null), ...medianLine],
        borderColor: percentileColors.median,
        borderWidth: viewMode === 'simulation' ? 2 : 1,
        pointRadius: 0,
        borderDash: [],
        tension: 0.1,
        yAxisID: 'y'
    });

    // 更新图表
    stockChart.data.labels = allDates;
    stockChart.data.datasets = datasets;
    
    // 更新图表选项
    stockChart.options.plugins.legend = {
        display: true,
        position: 'top',
        labels: {
            filter: function(legendItem) {
                return !legendItem.text.includes('模拟路径');
            }
        }
    };
    
    // 根据视图模式调整图表显示
    stockChart.options.scales.y.title.text = viewMode === 'history' ? '历史价格 ($)' : '价格预测 ($)';
    
    // 更新图表
    stockChart.update();
    
    // 显示或隐藏模拟统计信息
    const statsDiv = document.getElementById('simulationStats');
    if (statsDiv) {
        statsDiv.style.display = viewMode === 'simulation' ? 'block' : 'none';
    }
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
    
    // 格式化函数
    const formatCurrency = (value) => {
        return value ? `$${value.toFixed(2)}` : 'N/A';
    };
    
    const formatPercent = (value) => {
        return value ? `${value.toFixed(2)}%` : 'N/A';
    };
    
    // 更新统计区域
    const statsDiv = document.getElementById('simulationStats');
    statsDiv.style.display = 'block';
    statsDiv.innerHTML = `
        <div class="row">
            <div class="col-md-4">
                <div class="data-item">
                    <h4><i class="fas fa-calculator"></i> 预测平均价格</h4>
                    <p class="value text-primary">${formatCurrency(monteCarloData.mean_price)}</p>
                </div>
            </div>
            <div class="col-md-4">
                <div class="data-item">
                    <h4><i class="fas fa-chart-area"></i> 90% 置信区间下限</h4>
                    <p class="value text-danger">${formatCurrency(monteCarloData.percentile_5)}</p>
                </div>
            </div>
            <div class="col-md-4">
                <div class="data-item">
                    <h4><i class="fas fa-chart-line"></i> 90% 置信区间上限</h4>
                    <p class="value text-success">${formatCurrency(monteCarloData.percentile_95)}</p>
                </div>
            </div>
        </div>
        <div class="row mt-3">
            <div class="col-md-4">
                <div class="data-item">
                    <h4><i class="fas fa-percentage"></i> 年化收益率</h4>
                    <p class="value text-info">${formatPercent(monteCarloData.annual_return)}</p>
                </div>
            </div>
            <div class="col-md-4">
                <div class="data-item">
                    <h4><i class="fas fa-chart-bar"></i> 年化波动率</h4>
                    <p class="value text-secondary">${formatPercent(monteCarloData.annual_volatility)}</p>
                </div>
            </div>
            <div class="col-md-4">
                <div class="data-item">
                    <h4><i class="fas fa-coins"></i> 当前价格</h4>
                    <p class="value text-primary">${formatCurrency(monteCarloData.current_price)}</p>
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
    try {
        // 显示加载状态
        const loadingElement = document.getElementById('loadingRealTimeData');
        const contentElement = document.getElementById('realTimeDataContent');
        const errorElement = document.getElementById('realTimeDataError');
        
        // 检查元素是否存在
        if (loadingElement) loadingElement.style.display = 'block';
        if (contentElement) contentElement.style.display = 'none';
        if (errorElement) errorElement.style.display = 'none';
        
        const response = await fetch(`/user/api/real_time_stock_data?symbol=${symbol}`);
        if (!response.ok) {
            throw new Error(`HTTP状态码: ${response.status}`);
        }
        const data = await response.json();
        
        console.log('实时行情数据:', data); // 调试输出
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // 安全地更新DOM元素内容
        const safeUpdateElement = (id, content) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = content;
            } else {
                console.warn(`实时行情更新: 元素 #${id} 不存在`);
            }
        };
        
        // 安全地更新DOM元素类名
        const safeUpdateClass = (id, className) => {
            const element = document.getElementById(id);
            if (element) {
                element.className = className;
            } else {
                console.warn(`实时行情更新: 元素 #${id} 不存在`);
            }
        };
        
        // 更新价格
        safeUpdateElement('rtPrice', `¥${data.price.toFixed(2)}`);
        
        // 更新价格变化
        const changeValue = data.change;
        const changePercent = data.change_percent;
        const changeClass = changeValue >= 0 ? 'positive' : 'negative';
        const changeSign = changeValue >= 0 ? '+' : '';
        
        safeUpdateElement('rtPriceChange', `${changeSign}${changeValue.toFixed(2)} (${changeSign}${changePercent.toFixed(2)}%)`);
        
        // 更新其他信息
        safeUpdateElement('rtVolume', formatNumber(data.volume));
        safeUpdateElement('rtHigh', `¥${data.high.toFixed(2)}`);
        safeUpdateElement('rtLow', `¥${data.low.toFixed(2)}`);
        safeUpdateElement('lastUpdated', `最后更新: ${data.last_updated || new Date().toLocaleTimeString()}`);
        
        // 隐藏加载状态，显示内容
        if (loadingElement) loadingElement.style.display = 'none';
        if (contentElement) contentElement.style.display = 'block';
        
    } catch (error) {
        console.error('获取实时数据失败:', error);
        
        // 显示错误信息
        const errorElement = document.getElementById('realTimeDataError');
        const loadingElement = document.getElementById('loadingRealTimeData');
        
        if (errorElement) {
            errorElement.textContent = `获取实时数据失败: ${error.message}`;
            errorElement.style.display = 'block';
        }
        
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
    }
}

function formatNumber(num) {
    if (!num && num !== 0) return '-';
    
    if (num >= 1e9) {
        return (num / 1e9).toFixed(2) + '十亿';
    } else if (num >= 1e6) {
        return (num / 1e6).toFixed(2) + '百万';
    } else if (num >= 1e3) {
        return (num / 1e3).toFixed(2) + '千';
    }
    return num.toString();
}

function addRealTimeDataListeners() {
    // 获取股票选择器
    const stockSelector = document.getElementById('stockSelector');
    
    if (!stockSelector) {
        console.error('无法找到股票选择器元素');
        return;
    }
    
    // 初始加载
    fetchRealTimeData(stockSelector.value);
    
    // 添加change事件监听器
    stockSelector.addEventListener('change', function() {
        fetchRealTimeData(this.value);
    });
    
    // 添加刷新按钮事件监听
    const refreshButton = document.getElementById('refreshRealTimeData');
    if (refreshButton) {
        refreshButton.addEventListener('click', function() {
            fetchRealTimeData(stockSelector.value);
        });
    }
}

// 文档加载完成后执行的函数
function initializeAll() {
    // 初始化实时数据功能
    addRealTimeDataListeners();
    
    // 初始化时间范围选择
    initTimeRangeSelector();
    
    // 初始化图表
    initStockChart();
    
    console.log('所有功能初始化完成');
}

// 当文档加载完成时执行初始化
document.addEventListener('DOMContentLoaded', initializeAll); 