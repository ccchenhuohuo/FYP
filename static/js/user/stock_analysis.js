/**
 * 股票风险分析页面脚本
 * 处理表单提交、数据获取和结果展示
 */
document.addEventListener('DOMContentLoaded', function() {
    // 初始化日期选择器
    initDatePickers();
    
    // 初始化股票输入
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
 * 初始化股票代码输入
 */
function initTickerInputs() {
    // 添加股票输入字段
    document.getElementById('add-ticker').addEventListener('click', function() {
        const tickersContainer = document.getElementById('tickers-container');
        const tickerCount = tickersContainer.querySelectorAll('.ticker-input').length;
        
        const newTickerGroup = document.createElement('div');
        newTickerGroup.className = 'ticker-input input-group mb-2';
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
        
        // 获取所有股票代码
        const tickerInputs = document.querySelectorAll('input[name="tickers"]');
        const tickers = Array.from(tickerInputs).map(input => input.value.trim()).filter(val => val !== '');
        
        if (tickers.length === 0) {
            showError('请至少输入一个股票代码');
            showLoading(false);
            return;
        }
        
        // 获取日期范围
        const startDate = document.getElementById('start_date').value;
        const endDate = document.getElementById('end_date').value;
        
        // 构建请求数据
        const requestData = {
            tickers: tickers,
            start_date: startDate,
            end_date: endDate
        };
        
        console.log('发送分析请求数据:', requestData);
        
        // 发送请求
        fetch('/user/api/stock_analysis', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        })
        .then(response => {
            if (!response.ok) {
                if (response.status === 415) {
                    throw new Error('媒体类型不支持，请检查请求格式');
                }
                return response.json().then(err => {
                    throw new Error(err.error || '请求失败');
                }).catch(e => {
                    if (e instanceof SyntaxError) {
                        throw new Error(`服务器返回错误: ${response.status} ${response.statusText}`);
                    }
                    throw e;
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
    if (!data || !data.results || data.results.length === 0) {
        showError('没有可用的风险分析结果');
        return;
    }
    
    // 显示结果容器
    const resultsContainer = document.getElementById('results-container');
    resultsContainer.classList.remove('d-none');
    
    // 设置日期范围
    document.getElementById('analysis-date-range').textContent = 
        `${data.start_date || '未知'} 至 ${data.end_date || '未知'}`;
    
    // 清空仪表盘
    const dashboard = document.getElementById('risk-dashboard');
    dashboard.innerHTML = '';
    
    // 获取用户设置的阈值
    const thresholds = {
        volatility: parseFloat(document.getElementById('volatility_threshold').value) / 100,
        drawdown: -parseFloat(document.getElementById('drawdown_threshold').value) / 100,
        sharpe: parseFloat(document.getElementById('sharpe_threshold').value),
        beta: parseFloat(document.getElementById('beta_threshold').value),
        var: -parseFloat(document.getElementById('var_threshold').value) / 100,
        sortino: parseFloat(document.getElementById('sortino_threshold').value)
    };
    
    // 处理每只股票的结果
    data.results.forEach(stockResult => {
        const ticker = stockResult.ticker;
        
        // 检查是否有错误信息
        if (stockResult.error) {
            createErrorCard(dashboard, ticker, stockResult.error);
            return; // 继续下一只股票
        }
        
        // 检查是否有风险评估数据
        if (stockResult.risk_assessment) {
            // 根据用户阈值评估风险
            const evaluatedRisk = evaluateRiskWithUserThresholds(stockResult.risk_assessment, thresholds);
            
            // 添加风险评估卡片
            createRiskCard(dashboard, ticker, evaluatedRisk);
        } else {
            createErrorCard(dashboard, ticker, '没有风险评估数据');
        }
    });
}

/**
 * 根据用户设置的阈值评估风险
 */
function evaluateRiskWithUserThresholds(riskData, userThresholds) {
    // 创建一个新的风险数据对象，以保留原始数据
    const evaluatedRisk = {...riskData};
    
    // 添加用户自定义阈值评级
    
    // 1. 波动率
    if (evaluatedRisk.volatility !== undefined) {
        evaluatedRisk.user_volatility_rating = 
            evaluatedRisk.volatility / 100 > userThresholds.volatility ? "高" : "低";
    }
    
    // 2. 最大回撤
    if (evaluatedRisk.max_drawdown !== undefined) {
        evaluatedRisk.user_drawdown_rating = 
            evaluatedRisk.max_drawdown / 100 < userThresholds.drawdown ? "高" : "低";
    }
    
    // 3. 夏普比率
    if (evaluatedRisk.sharpe_ratio !== undefined) {
        evaluatedRisk.user_sharpe_rating = 
            evaluatedRisk.sharpe_ratio < userThresholds.sharpe ? "差" : "好";
    }
    
    // 4. 贝塔系数
    if (evaluatedRisk.beta !== undefined) {
        evaluatedRisk.user_beta_rating = 
            evaluatedRisk.beta > userThresholds.beta ? "高" : "低";
    }
    
    // 5. 风险价值(VaR)
    if (evaluatedRisk.var_95 !== undefined) {
        evaluatedRisk.user_var_rating = 
            evaluatedRisk.var_95 / 100 < userThresholds.var ? "高" : "低";
    }
    
    // 6. 索提诺比率
    if (evaluatedRisk.sortino_ratio !== undefined && evaluatedRisk.sortino_ratio !== "∞") {
        const sortinoValue = typeof evaluatedRisk.sortino_ratio === 'string' 
            ? parseFloat(evaluatedRisk.sortino_ratio) 
            : evaluatedRisk.sortino_ratio;
        
        evaluatedRisk.user_sortino_rating = 
            sortinoValue < userThresholds.sortino ? "差" : "好";
    }
    
    // 计算整体风险评级（基于用户阈值）
    let highRiskCount = 0;
    let totalIndicators = 0;
    
    if (evaluatedRisk.user_volatility_rating) {
        highRiskCount += (evaluatedRisk.user_volatility_rating === "高") ? 1 : 0;
        totalIndicators++;
    }
    
    if (evaluatedRisk.user_drawdown_rating) {
        highRiskCount += (evaluatedRisk.user_drawdown_rating === "高") ? 1 : 0;
        totalIndicators++;
    }
    
    if (evaluatedRisk.user_sharpe_rating) {
        highRiskCount += (evaluatedRisk.user_sharpe_rating === "差") ? 1 : 0;
        totalIndicators++;
    }
    
    if (evaluatedRisk.user_beta_rating) {
        highRiskCount += (evaluatedRisk.user_beta_rating === "高") ? 1 : 0;
        totalIndicators++;
    }
    
    if (evaluatedRisk.user_var_rating) {
        highRiskCount += (evaluatedRisk.user_var_rating === "高") ? 1 : 0;
        totalIndicators++;
    }
    
    if (evaluatedRisk.user_sortino_rating) {
        highRiskCount += (evaluatedRisk.user_sortino_rating === "差") ? 1 : 0;
        totalIndicators++;
    }
    
    // 计算用户自定义的整体风险等级
    if (totalIndicators > 0) {
        const riskRatio = highRiskCount / totalIndicators;
        
        if (riskRatio >= 0.7) {
            evaluatedRisk.user_overall_risk = "高";
        } else if (riskRatio <= 0.3) {
            evaluatedRisk.user_overall_risk = "低";
        } else {
            evaluatedRisk.user_overall_risk = "中";
        }
    }
    
    return evaluatedRisk;
}

/**
 * 创建风险分析卡片
 */
function createRiskCard(container, ticker, data) {
    // 创建卡片容器
    const card = document.createElement('div');
    card.className = 'risk-card mb-4';
    
    // 创建卡片头部
    const cardHeader = document.createElement('div');
    cardHeader.className = 'risk-header';
    
    // 优先使用基于用户阈值的风险评级，如果不可用则使用默认风险评级
    const useUserRiskLevel = data.user_overall_risk !== undefined;
    const riskLevel = useUserRiskLevel ? 
        (data.user_overall_risk === "高" ? 3 : data.user_overall_risk === "中" ? 2 : 1) : 
        determineRiskLevel(data);
    const riskClass = getRiskClass(riskLevel);
    
    // 设置卡片标题
    cardHeader.innerHTML = `
        <h3 class="risk-title">
            ${ticker}
            <span class="${riskClass}">${getRiskLevelText(riskLevel)}</span>
            ${useUserRiskLevel ? '<small>(基于您的阈值设置)</small>' : ''}
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
    
    // 添加波动率
    if (data.volatility !== undefined) {
        const metricItem = document.createElement('div');
        metricItem.className = 'metric-item';
        
        const ratingClass = (data.user_volatility_rating === "高") ? 'risk-high' : 'risk-low';
        const ratingText = data.user_volatility_rating || data.volatility_rating || '';
        
        metricItem.innerHTML = `
            <span class="metric-name">年化波动率</span>
            <span class="metric-value">
                ${data.volatility}% 
                <small class="${ratingClass}">${ratingText}</small>
            </span>
        `;
        metricsGroup.appendChild(metricItem);
    }
    
    // 添加最大回撤
    if (data.max_drawdown !== undefined) {
        const metricItem = document.createElement('div');
        metricItem.className = 'metric-item';
        
        const ratingClass = (data.user_drawdown_rating === "高") ? 'risk-high' : 'risk-low';
        const ratingText = data.user_drawdown_rating || data.drawdown_rating || '';
        
        metricItem.innerHTML = `
            <span class="metric-name">最大回撤</span>
            <span class="metric-value">
                ${data.max_drawdown}% 
                <small class="${ratingClass}">${ratingText}</small>
            </span>
        `;
        metricsGroup.appendChild(metricItem);
    }
    
    // 添加夏普比率
    if (data.sharpe_ratio !== undefined) {
        const metricItem = document.createElement('div');
        metricItem.className = 'metric-item';
        
        const ratingClass = (data.user_sharpe_rating === "差") ? 'risk-high' : 'risk-low';
        const ratingText = data.user_sharpe_rating || data.sharpe_rating || '';
        
        metricItem.innerHTML = `
            <span class="metric-name">夏普比率</span>
            <span class="metric-value">
                ${data.sharpe_ratio} 
                <small class="${ratingClass}">${ratingText}</small>
            </span>
        `;
        metricsGroup.appendChild(metricItem);
    }
    
    // 添加贝塔系数
    if (data.beta !== undefined) {
        const metricItem = document.createElement('div');
        metricItem.className = 'metric-item';
        
        const ratingClass = (data.user_beta_rating === "高") ? 'risk-high' : 'risk-low';
        const ratingText = data.user_beta_rating || data.beta_rating || '';
        
        metricItem.innerHTML = `
            <span class="metric-name">贝塔系数</span>
            <span class="metric-value">
                ${data.beta} 
                <small class="${ratingClass}">${ratingText}</small>
            </span>
        `;
        metricsGroup.appendChild(metricItem);
    }
    
    // 添加VaR
    if (data.var_95 !== undefined) {
        const metricItem = document.createElement('div');
        metricItem.className = 'metric-item';
        
        const ratingClass = (data.user_var_rating === "高") ? 'risk-high' : 'risk-low';
        const ratingText = data.user_var_rating || data.var_rating || '';
        
        metricItem.innerHTML = `
            <span class="metric-name">95% VaR</span>
            <span class="metric-value">
                ${data.var_95}% 
                <small class="${ratingClass}">${ratingText}</small>
            </span>
        `;
        metricsGroup.appendChild(metricItem);
    }
    
    // 添加索提诺比率
    if (data.sortino_ratio !== undefined) {
        const metricItem = document.createElement('div');
        metricItem.className = 'metric-item';
        
        const ratingClass = (data.user_sortino_rating === "差") ? 'risk-high' : 'risk-low';
        const ratingText = data.user_sortino_rating || data.sortino_rating || '';
        
        metricItem.innerHTML = `
            <span class="metric-name">索提诺比率</span>
            <span class="metric-value">
                ${data.sortino_ratio} 
                <small class="${ratingClass}">${ratingText}</small>
            </span>
        `;
        metricsGroup.appendChild(metricItem);
    }
    
    // 添加风险评估总结
    if (data.risk_summary && data.risk_summary.length > 0) {
        const summaryGroup = document.createElement('div');
        summaryGroup.className = 'metrics-group';
        summaryGroup.innerHTML = `<h4 class="metrics-group-title">风险评估总结</h4>`;
        
        const summaryList = document.createElement('ul');
        summaryList.className = 'summary-list';
        
        data.risk_summary.forEach(item => {
            const listItem = document.createElement('li');
            listItem.textContent = item;
            summaryList.appendChild(listItem);
        });
        
        summaryGroup.appendChild(summaryList);
        cardBody.appendChild(summaryGroup);
    }
    
    // 组装卡片
    cardBody.appendChild(gaugeContainer);
    cardBody.appendChild(metricsGroup);
    card.appendChild(cardHeader);
    card.appendChild(cardBody);
    container.appendChild(card);
}

/**
 * 创建错误卡片
 */
function createErrorCard(container, ticker, errorMessage) {
    const card = document.createElement('div');
    card.className = 'risk-card mb-4';
    
    const cardHeader = document.createElement('div');
    cardHeader.className = 'risk-header';
    cardHeader.innerHTML = `
        <h3 class="risk-title">${ticker}</h3>
    `;
    
    const cardBody = document.createElement('div');
    cardBody.className = 'risk-body';
    
    const errorContainer = document.createElement('div');
    errorContainer.className = 'alert alert-danger';
    errorContainer.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${errorMessage}`;
    
    cardBody.appendChild(errorContainer);
    card.appendChild(cardHeader);
    card.appendChild(cardBody);
    container.appendChild(card);
}

/**
 * 创建风险仪表盘
 */
function createGauge(container, riskLevel) {
    const gaugeColor = getGaugeColor(riskLevel);
    const gaugeDegree = (riskLevel - 1) * 90; // 1=0度(低), 2=90度(中), 3=180度(高)
    
    container.innerHTML = `
        <div class="gauge-background"></div>
        <div class="gauge-fill" style="--gauge-color: ${gaugeColor}; transform: rotate(${gaugeDegree - 180}deg);"></div>
        <div class="gauge-center"></div>
        <div class="gauge-value">${getRiskLevelText(riskLevel)}</div>
    `;
}

/**
 * 确定风险等级 (1-3)
 * 1 = 低风险, 2 = 中等风险, 3 = 高风险
 */
function determineRiskLevel(data) {
    // 初始化风险指标评分
    let riskScore = 0;
    let totalMetrics = 0;
    
    // 检查波动率
    if (data.volatility !== undefined) {
        if (data.volatility > 30) riskScore += 3;
        else if (data.volatility > 20) riskScore += 2;
        else riskScore += 1;
        totalMetrics++;
    }
    
    // 检查最大回撤
    if (data.max_drawdown !== undefined) {
        if (data.max_drawdown < -30) riskScore += 3;
        else if (data.max_drawdown < -20) riskScore += 2;
        else riskScore += 1;
        totalMetrics++;
    }
    
    // 检查夏普比率
    if (data.sharpe_ratio !== undefined) {
        if (data.sharpe_ratio < 0) riskScore += 3;
        else if (data.sharpe_ratio < 1) riskScore += 2;
        else riskScore += 1;
        totalMetrics++;
    }
    
    // 检查贝塔系数
    if (data.beta !== undefined) {
        if (data.beta > 1.5) riskScore += 3;
        else if (data.beta > 1.0) riskScore += 2;
        else riskScore += 1;
        totalMetrics++;
    }
    
    // 检查VaR
    if (data.var_95 !== undefined) {
        if (data.var_95 < -3) riskScore += 3;
        else if (data.var_95 < -2) riskScore += 2;
        else riskScore += 1;
        totalMetrics++;
    }
    
    // 如果有整体风险评级，直接使用
    if (data.overall_risk !== undefined) {
        if (data.overall_risk === "高") return 3;
        if (data.overall_risk === "中") return 2;
        if (data.overall_risk === "低") return 1;
    }
    
    // 计算平均分并确定等级
    if (totalMetrics > 0) {
        const avgScore = riskScore / totalMetrics;
        if (avgScore > 2.3) return 3; // 高风险
        if (avgScore > 1.7) return 2; // 中等风险
        return 1; // 低风险
    }
    
    return 2; // 默认为中等风险
}

/**
 * 获取风险等级CSS类
 */
function getRiskClass(riskLevel) {
    if (riskLevel === 3) return 'risk-high';
    if (riskLevel === 1) return 'risk-low';
    return 'risk-medium';
}

/**
 * 获取风险等级文本描述
 */
function getRiskLevelText(riskLevel) {
    if (riskLevel === 3) return '高风险';
    if (riskLevel === 1) return '低风险';
    return '中等风险';
}

/**
 * 获取仪表盘颜色
 */
function getGaugeColor(riskLevel) {
    if (riskLevel === 3) return '#dc3545'; // 红色 - 高风险
    if (riskLevel === 1) return '#28a745'; // 绿色 - 低风险
    return '#fd7e14'; // 橙色 - 中等风险
}

/**
 * 显示或隐藏加载状态
 */
function showLoading(show) {
    const loadingContainer = document.getElementById('loading-container');
    if (show) {
        loadingContainer.classList.remove('d-none');
    } else {
        loadingContainer.classList.add('d-none');
    }
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
    const errorContainer = document.getElementById('error-container');
    errorContainer.classList.add('d-none');
}

/**
 * 格式化日期
 */
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
} 