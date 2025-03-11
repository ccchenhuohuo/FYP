/**
 * 股票风险分析页面脚本
 * 处理表单提交、数据获取和结果展示
 */
document.addEventListener('DOMContentLoaded', function() {
    // 初始化日期选择器
    initDatePickers();
    
    // 初始化风险阈值设置面板
    initThresholdSettings();
    
    // 初始化股票代码输入
    initTickerInputs();
    
    // 初始化表单提交
    initFormSubmission();
});

/**
 * 初始化日期选择器
 */
function initDatePickers() {
    // 设置默认日期范围（当前日期到一年前）
    const today = new Date();
    const oneYearAgo = new Date();
    oneYearAgo.setFullYear(today.getFullYear() - 1);
    
    document.getElementById('end_date').value = formatDate(today);
    document.getElementById('start_date').value = formatDate(oneYearAgo);
}

/**
 * 初始化风险阈值设置面板（可折叠）
 */
function initThresholdSettings() {
    const thresholdToggle = document.getElementById('threshold-toggle');
    const thresholdBody = document.getElementById('threshold-body');
    
    // 默认展开状态
    let isExpanded = true;
    
    thresholdToggle.addEventListener('click', function() {
        isExpanded = !isExpanded;
        
        if (isExpanded) {
            thresholdBody.style.maxHeight = thresholdBody.scrollHeight + 'px';
            thresholdBody.style.opacity = '1';
            thresholdToggle.querySelector('i').className = 'fas fa-chevron-down';
        } else {
            thresholdBody.style.maxHeight = '0';
            thresholdBody.style.opacity = '0';
            thresholdToggle.querySelector('i').className = 'fas fa-chevron-right';
        }
        
        document.querySelector('.threshold-settings').classList.toggle('collapsed', !isExpanded);
    });
    
    // 初始状态设置
    thresholdBody.style.maxHeight = thresholdBody.scrollHeight + 'px';
    thresholdBody.style.opacity = '1';
}

/**
 * 初始化股票代码输入
 */
function initTickerInputs() {
    // 添加股票输入字段
    document.getElementById('add-ticker').addEventListener('click', function() {
        const tickersContainer = document.getElementById('tickers-container');
        const tickerCount = tickersContainer.querySelectorAll('.ticker-input').length;
        
        const newTickerGroup = document.createElement('div');
        newTickerGroup.className = 'ticker-input input-group';
        newTickerGroup.innerHTML = `
            <input type="text" name="tickers" class="form-control" placeholder="输入股票代码 ${tickerCount + 1}" required>
            <button type="button" class="btn btn-outline-danger remove-ticker">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        tickersContainer.appendChild(newTickerGroup);
        
        // 添加删除按钮事件
        newTickerGroup.querySelector('.remove-ticker').addEventListener('click', function() {
            newTickerGroup.remove();
        });
    });
}

/**
 * 初始化表单提交
 */
function initFormSubmission() {
    document.getElementById('stock-analysis-form').addEventListener('submit', function(e) {
        e.preventDefault();
        
        // 清除之前的错误
        hideError();
        
        // 显示加载状态
        showLoading(true);
        
        // 隐藏结果容器
        document.getElementById('results-container').classList.add('d-none');
        
        // 获取表单数据
        const formData = new FormData(this);
        
        // 发送请求
        fetch('/user/api/stock_analysis', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(err.error || '请求失败');
                });
            }
            return response.json();
        })
        .then(data => {
            console.log('收到分析数据:', data);
            
            // 隐藏加载状态
            showLoading(false);
            
            // 处理并显示结果
            processAndDisplayResults(data);
        })
        .catch(error => {
            // 隐藏加载状态
            showLoading(false);
            
            // 显示错误信息
            showError(error.message || '分析请求失败');
            console.error('分析请求失败:', error);
        });
    });
}

/**
 * 处理并显示分析结果
 */
function processAndDisplayResults(data) {
    // 检查数据有效性
    if (!data || !data.data || Object.keys(data.data).length === 0) {
        showError('没有可用的分析结果');
        return;
    }
    
    // 显示结果容器
    const resultsContainer = document.getElementById('results-container');
    resultsContainer.classList.remove('d-none');
    
    // 设置日期范围
    document.getElementById('analysis-date-range').textContent = 
        `${data.start_date || '未知'} 至 ${data.end_date || '未知'}`;
    
    // 获取股票代码列表
    const tickers = Object.keys(data.data);
    
    // 清空仪表盘
    const dashboard = document.getElementById('risk-dashboard');
    dashboard.innerHTML = '';
    
    // 为每个股票创建风险卡片
    tickers.forEach(ticker => {
        const tickerData = data.data[ticker];
        
        // 检查数据是否可用
        if (!tickerData.data_available) {
            createErrorCard(dashboard, ticker, tickerData.error_message || '数据不可用');
            return;
        }
        
        // 创建风险卡片
        createRiskCard(dashboard, ticker, tickerData);
    });
}

/**
 * 创建风险分析卡片
 */
function createRiskCard(container, ticker, data) {
    // 创建卡片容器
    const card = document.createElement('div');
    card.className = 'risk-card';
    
    // 创建卡片头部
    const cardHeader = document.createElement('div');
    cardHeader.className = 'risk-header';
    
    // 确定整体风险等级
    const riskLevel = determineRiskLevel(data);
    const riskClass = getRiskClass(riskLevel);
    
    // 设置卡片标题
    cardHeader.innerHTML = `
        <h3 class="risk-title">
            ${ticker}
            <span class="${riskClass}">${getRiskLevelText(riskLevel)}</span>
        </h3>
    `;
    
    // 创建卡片内容
    const cardBody = document.createElement('div');
    cardBody.className = 'risk-body';
    
    // 添加风险仪表盘
    const gaugeContainer = document.createElement('div');
    gaugeContainer.className = 'gauge-container';
    
    // 创建仪表盘
    createGauge(gaugeContainer, riskLevel);
    
    // 添加风险指标组
    const metricsGroup = document.createElement('div');
    metricsGroup.className = 'metrics-group';
    metricsGroup.innerHTML = `<h4 class="metrics-group-title">风险指标</h4>`;
    
    // 添加关键风险指标
    const keyMetrics = [
        { name: '年化波动率', key: 'volatility', format: 'percent' },
        { name: '最大回撤', key: 'max_drawdown', format: 'percent' },
        { name: '夏普比率', key: 'sharpe_ratio', format: 'decimal' },
        { name: '贝塔系数', key: 'beta', format: 'decimal' },
        { name: '索提诺比率', key: 'sortino_ratio', format: 'decimal' },
        { name: 'VaR (95%)', key: 'var_95', format: 'percent' }
    ];
    
    keyMetrics.forEach(metric => {
        if (data[metric.key] !== undefined && data[metric.key] !== null) {
            const metricItem = document.createElement('div');
            metricItem.className = 'metric-item';
            
            // 格式化指标值
            let formattedValue = formatMetricValue(data[metric.key], metric.format);
            
            // 确定指标风险等级
            const metricRiskLevel = determineMetricRiskLevel(metric.key, data[metric.key]);
            const metricRiskClass = getRiskClass(metricRiskLevel);
            
            metricItem.innerHTML = `
                <span class="metric-name">${metric.name}</span>
                <span class="metric-value ${metricRiskClass}">${formattedValue}</span>
            `;
            
            metricsGroup.appendChild(metricItem);
        }
    });
    
    // 添加警报容器
    const alertsContainer = document.createElement('div');
    alertsContainer.className = 'alerts-container';
    
    // 添加警报
    if (data.alerts && data.alerts.length > 0) {
        data.alerts.forEach(alert => {
            const alertElement = document.createElement('div');
            alertElement.className = `alert alert-${alert.type}`;
            alertElement.textContent = alert.message;
            alertsContainer.appendChild(alertElement);
        });
    }
    
    // 组装卡片
    cardBody.appendChild(gaugeContainer);
    cardBody.appendChild(metricsGroup);
    
    if (data.alerts && data.alerts.length > 0) {
        cardBody.appendChild(alertsContainer);
    }
    
    card.appendChild(cardHeader);
    card.appendChild(cardBody);
    container.appendChild(card);
}

/**
 * 创建错误卡片
 */
function createErrorCard(container, ticker, errorMessage) {
    const card = document.createElement('div');
    card.className = 'risk-card';
    
    card.innerHTML = `
        <div class="risk-header">
            <h3 class="risk-title">
                ${ticker}
                <span class="risk-high">数据错误</span>
            </h3>
        </div>
        <div class="risk-body">
            <div class="alert alert-danger">
                ${errorMessage || '无法获取数据'}
            </div>
        </div>
    `;
    
    container.appendChild(card);
}

/**
 * 创建风险仪表盘
 */
function createGauge(container, riskLevel) {
    // 计算仪表盘角度 (0-1 映射到 -180 到 0 度)
    const angle = -180 + (riskLevel * 180);
    
    // 设置仪表盘颜色
    const gaugeColor = getGaugeColor(riskLevel);
    
    // 创建仪表盘元素
    container.innerHTML = `
        <div class="gauge-background"></div>
        <div class="gauge-fill" style="transform: rotate(${angle}deg); background-color: ${gaugeColor};"></div>
        <div class="gauge-center"></div>
        <div class="gauge-value">${(riskLevel * 100).toFixed(0)}%</div>
    `;
}

/**
 * 确定整体风险等级 (0-1)
 */
function determineRiskLevel(data) {
    // 基于多个指标计算综合风险等级
    let riskScore = 0;
    let factorsCount = 0;
    
    // 波动率 (高 = 高风险)
    if (data.volatility !== undefined && data.volatility !== null) {
        const volatilityScore = Math.min(data.volatility / 0.5, 1); // 50%波动率为最高风险
        riskScore += volatilityScore;
        factorsCount++;
    }
    
    // 最大回撤 (负值，越低 = 高风险)
    if (data.max_drawdown !== undefined && data.max_drawdown !== null) {
        const drawdownScore = Math.min(Math.abs(data.max_drawdown) / 0.5, 1); // 50%回撤为最高风险
        riskScore += drawdownScore;
        factorsCount++;
    }
    
    // 夏普比率 (低 = 高风险)
    if (data.sharpe_ratio !== undefined && data.sharpe_ratio !== null) {
        // 夏普比率从-2到2映射到1到0
        const sharpeScore = Math.max(0, Math.min(1, (2 - data.sharpe_ratio) / 4));
        riskScore += sharpeScore;
        factorsCount++;
    }
    
    // 贝塔系数 (高 = 高风险)
    if (data.beta !== undefined && data.beta !== null && !isNaN(data.beta)) {
        const betaScore = Math.min(data.beta / 2, 1); // 贝塔2为最高风险
        riskScore += betaScore;
        factorsCount++;
    }
    
    // 计算平均风险分数
    return factorsCount > 0 ? riskScore / factorsCount : 0.5;
}

/**
 * 确定单个指标的风险等级
 */
function determineMetricRiskLevel(metricKey, value) {
    if (value === null || value === undefined) return 0;
    
    switch (metricKey) {
        case 'volatility':
            // 波动率: <20% 低, 20-30% 中, >30% 高
            if (value < 0.2) return 0;
            if (value < 0.3) return 0.5;
            return 1;
            
        case 'max_drawdown':
            // 最大回撤: >-15% 低, -15%到-25% 中, <-25% 高
            if (value > -0.15) return 0;
            if (value > -0.25) return 0.5;
            return 1;
            
        case 'sharpe_ratio':
            // 夏普比率: >1 低, 0-1 中, <0 高
            if (value > 1) return 0;
            if (value >= 0) return 0.5;
            return 1;
            
        case 'beta':
            // 贝塔: <0.8 低, 0.8-1.2 中, >1.2 高
            if (value < 0.8) return 0;
            if (value <= 1.2) return 0.5;
            return 1;
            
        case 'sortino_ratio':
            // 索提诺比率: >1.5 低, 0-1.5 中, <0 高
            if (value > 1.5) return 0;
            if (value >= 0) return 0.5;
            return 1;
            
        case 'var_95':
            // VaR: >-0.01 低, -0.01到-0.02 中, <-0.02 高
            if (value > -0.01) return 0;
            if (value > -0.02) return 0.5;
            return 1;
            
        default:
            return 0.5;
    }
}

/**
 * 获取风险等级对应的CSS类
 */
function getRiskClass(riskLevel) {
    if (riskLevel >= 0.7) return 'risk-high';
    if (riskLevel >= 0.3) return 'risk-medium';
    return 'risk-low';
}

/**
 * 获取风险等级对应的文本
 */
function getRiskLevelText(riskLevel) {
    if (riskLevel >= 0.7) return '高风险';
    if (riskLevel >= 0.3) return '中等风险';
    return '低风险';
}

/**
 * 获取仪表盘颜色
 */
function getGaugeColor(riskLevel) {
    if (riskLevel >= 0.7) return '#dc3545'; // 红色
    if (riskLevel >= 0.3) return '#fd7e14'; // 橙色
    return '#28a745'; // 绿色
}

/**
 * 格式化指标值
 */
function formatMetricValue(value, format) {
    if (value === null || value === undefined) return '无数据';
    
    switch (format) {
        case 'percent':
            return (value * 100).toFixed(2) + '%';
        case 'decimal':
            return value.toFixed(2);
        default:
            return value.toString();
    }
}

/**
 * 显示/隐藏加载状态
 */
function showLoading(show) {
    document.getElementById('loading-container').classList.toggle('d-none', !show);
}

/**
 * 显示错误信息
 */
function showError(message) {
    const errorContainer = document.getElementById('error-container');
    errorContainer.textContent = message;
    errorContainer.classList.remove('d-none');
}

/**
 * 隐藏错误信息
 */
function hideError() {
    document.getElementById('error-container').classList.add('d-none');
}

/**
 * 格式化日期为YYYY-MM-DD格式
 */
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
} 