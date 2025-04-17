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
    const addTickerButton = document.getElementById('add-ticker');
        const tickersContainer = document.getElementById('tickers-container');

    addTickerButton.addEventListener('click', function() {
        const tickerCount = tickersContainer.querySelectorAll('.ticker-input').length;
        
        const newTickerGroup = document.createElement('div');
        // Add alignment and spacing classes
        newTickerGroup.className = 'ticker-input d-flex align-items-center mb-2'; 
        newTickerGroup.innerHTML = `
            <input type="text" name="tickers" class="form-control me-2" placeholder="Enter stock ticker ${tickerCount + 1}" required>
            <button type="button" class="btn btn-outline-danger btn-sm remove-ticker-btn" aria-label="Remove Ticker">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        tickersContainer.appendChild(newTickerGroup);
        
        // Add event listener to the new remove button
        newTickerGroup.querySelector('.remove-ticker-btn').addEventListener('click', function() {
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
            showError('Please enter at least one stock ticker');
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
        
        console.log('Sending analysis request data:', requestData);
        
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
                    throw new Error('Media type not supported, please check request format');
                }
                return response.json().then(err => {
                    throw new Error(err.error || 'Request failed');
                }).catch(e => {
                    if (e instanceof SyntaxError) {
                        throw new Error(`Server returned error: ${response.status} ${response.statusText}`);
                    }
                    throw e;
                });
            }
            return response.json();
        })
        .then(data => {
            console.log('Received analysis data:', data);
            
            // 隐藏加载状态
            showLoading(false);
            
            // 处理并显示结果
            processAndDisplayResults(data);
            
            // 获取AI分析报告
            if (data.results && data.results.length > 0) {
                requestAIAnalysis(data, tickers);
            }
        })
        .catch(error => {
            // 隐藏加载状态
            showLoading(false);
            
            // 显示错误信息
            showError(error.message || 'Analysis request failed');
            console.error('Analysis request failed:', error);
        });
    });
}

/**
 * 向AI请求分析报告
 */
function requestAIAnalysis(analysisData, tickers) {
    // 显示AI分析加载状态
    const resultsContainer = document.getElementById('results-container');
    
    // 检查是否已有AI报告区域，如果没有则创建
    let aiReportContainer = document.getElementById('ai-report-container');
    if (!aiReportContainer) {
        aiReportContainer = document.createElement('div');
        aiReportContainer.id = 'ai-report-container';
        aiReportContainer.className = 'analysis-card mt-4';
        aiReportContainer.innerHTML = `
            <div class="card-header">
                <h2><i class="fas fa-robot"></i> AI Analysis Report</h2>
            </div>
            <div class="card-body">
                <div id="ai-report-loading" class="loading-container">
                    <div class="loading-spinner"></div>
                    <p>Generating AI insights, please wait...</p>
                </div>
                <div id="ai-report-content" class="d-none"></div>
            </div>
        `;
        resultsContainer.appendChild(aiReportContainer);
    } else {
        // 如果已存在，重置为加载状态
        document.getElementById('ai-report-loading').classList.remove('d-none');
        document.getElementById('ai-report-content').classList.add('d-none');
        document.getElementById('ai-report-content').innerHTML = '';
    }
    
    // 构建用于AI分析的prompt
    const thresholds = {
        volatility: document.getElementById('volatility_value').textContent,
        drawdown: document.getElementById('drawdown_value').textContent,
        sharpe: document.getElementById('sharpe_value').textContent,
        beta: document.getElementById('beta_value').textContent,
        var: document.getElementById('var_value').textContent,
        sortino: document.getElementById('sortino_value').textContent
    };
    
    // 为每个股票构建单独的分析提示
    const prompts = [];
    
    analysisData.results.forEach(result => {
        if (!result.error) {
            const ticker = result.ticker;
            // 使用generate_analysis_prompt的相似逻辑构建prompt
            const prompt = `
As a financial expert, analyze the risk profile of ${ticker} based on historical data from ${analysisData.start_date} to ${analysisData.end_date}.

First, provide a brief company profile for ${ticker} (2-3 sentences about what the company does, its industry, and key information).

Then analyze the following risk metrics:
- Annualized Volatility: ${result.risk_assessment.volatility}% (Threshold: ${thresholds.volatility})
- Maximum Drawdown: ${result.risk_assessment.max_drawdown}% (Threshold: ${thresholds.drawdown})
- Sharpe Ratio: ${result.risk_assessment.sharpe_ratio} (Threshold: ${thresholds.sharpe})
- Beta: ${result.risk_assessment.beta || 'N/A'} (Threshold: ${thresholds.beta})
- Value at Risk (95%): ${result.risk_assessment.var_95}% (Threshold: ${thresholds.var})
- Sortino Ratio: ${result.risk_assessment.sortino_ratio} (Threshold: ${thresholds.sortino})

Provide an insightful analysis that includes:
1. The company profile
2. An overall assessment of the stock's risk level
3. Explanation of concerning risk factors
4. Interpretation of key metrics in the context of the market
5. Recommendations for risk management strategies

Important notes:
- Format your response using HTML with proper paragraphs, headers, and bullet points
- Do not include any markdown code blocks like \`\`\`html - write HTML directly
- Write your analysis in English only
- Use professional financial language`;
            prompts.push({ ticker, prompt });
        }
    });

    // 一次性处理所有股票的分析，逐个发送到AI助手接口
    const processPrompts = async () => {
        const reports = [];
        
        for (const { ticker, prompt } of prompts) {
            try {
                // 使用AI助手接口而不是AI分析接口
                const response = await fetch('/user/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ message: prompt })
                });
                
                const data = await response.json();
                
                if (data.response) {
                    reports.push({
                        ticker: ticker,
                        content: data.response
                    });
                } else if (data.error) {
                    reports.push({
                        ticker: ticker,
                        content: `<p class="text-danger">Error generating analysis: ${data.error}</p>`
                    });
                }
            } catch (error) {
                console.error(`Error analyzing ${ticker}:`, error);
                reports.push({
                    ticker: ticker,
                    content: `<p class="text-danger">Failed to generate analysis: ${error.message}</p>`
                });
            }
        }
        
        return { reports };
    };
    
    // 执行分析并处理结果
    processPrompts()
        .then(data => {
            // 隐藏加载状态并显示报告
            document.getElementById('ai-report-loading').classList.add('d-none');
            const reportContent = document.getElementById('ai-report-content');
            reportContent.classList.remove('d-none');
            
            // 如果有多支股票，为每个创建单独的报告区块
            if (data.reports && data.reports.length > 0) {
                data.reports.forEach(report => {
                    // 处理可能存在的```html标记
                    let cleanContent = report.content;
                    // 移除可能的```html和```标记
                    cleanContent = cleanContent.replace(/```html|```/g, '');
                    
                    const reportBlock = document.createElement('div');
                    reportBlock.className = 'ai-report-block mb-3';
                    reportBlock.innerHTML = `
                        <h4 class="report-ticker">${report.ticker}</h4>
                        <div class="report-content">${cleanContent}</div>
                    `;
                    reportContent.appendChild(reportBlock);
                });
            } else if (data.report) {
                // 单一报告，同样处理标记
                let cleanContent = data.report;
                cleanContent = cleanContent.replace(/```html|```/g, '');
                reportContent.innerHTML = `<div class="report-content">${cleanContent}</div>`;
            } else {
                reportContent.innerHTML = '<p class="text-muted">No insights available for this data.</p>';
            }
        })
        .catch(error => {
            console.error('AI analysis request failed:', error);
            document.getElementById('ai-report-loading').classList.add('d-none');
            document.getElementById('ai-report-content').classList.remove('d-none');
            document.getElementById('ai-report-content').innerHTML = 
                '<div class="alert alert-warning">Failed to generate AI insights. Please try again later.</div>';
    });
}

/**
 * 处理并显示分析结果
 */
function processAndDisplayResults(data) {
    // 检查数据有效性
    if (!data || !data.results || data.results.length === 0) {
        showError('No risk analysis results available');
        return;
    }
    
    // 显示结果容器
    const resultsContainer = document.getElementById('results-container');
    resultsContainer.classList.remove('d-none');
    
    // 设置日期范围
    document.getElementById('analysis-date-range').textContent = 
        `${data.start_date || 'Unknown'} to ${data.end_date || 'Unknown'}`;
    
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
            createErrorCard(dashboard, ticker, 'No risk assessment data available');
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
            evaluatedRisk.volatility / 100 > userThresholds.volatility ? "High" : "Low";
    }
    
    // 2. 最大回撤
    if (evaluatedRisk.max_drawdown !== undefined) {
        evaluatedRisk.user_drawdown_rating = 
            evaluatedRisk.max_drawdown / 100 < userThresholds.drawdown ? "High" : "Low";
    }
    
    // 3. 夏普比率
    if (evaluatedRisk.sharpe_ratio !== undefined) {
        evaluatedRisk.user_sharpe_rating = 
            evaluatedRisk.sharpe_ratio < userThresholds.sharpe ? "Poor" : "Good";
    }
    
    // 4. 贝塔系数
    if (evaluatedRisk.beta !== undefined) {
        evaluatedRisk.user_beta_rating = 
            evaluatedRisk.beta > userThresholds.beta ? "High" : "Low";
    }
    
    // 5. 风险价值(VaR)
    if (evaluatedRisk.var_95 !== undefined) {
        evaluatedRisk.user_var_rating = 
            evaluatedRisk.var_95 / 100 < userThresholds.var ? "High" : "Low";
    }
    
    // 6. 索提诺比率
    if (evaluatedRisk.sortino_ratio !== undefined && evaluatedRisk.sortino_ratio !== "∞") {
        const sortinoValue = typeof evaluatedRisk.sortino_ratio === 'string' 
            ? parseFloat(evaluatedRisk.sortino_ratio) 
            : evaluatedRisk.sortino_ratio;
        
        evaluatedRisk.user_sortino_rating = 
            sortinoValue < userThresholds.sortino ? "Poor" : "Good";
    }
    
    // 计算整体风险评级（基于用户阈值）
    let highRiskCount = 0;
    let totalIndicators = 0;
    
    if (evaluatedRisk.user_volatility_rating) {
        highRiskCount += (evaluatedRisk.user_volatility_rating === "High") ? 1 : 0;
        totalIndicators++;
    }
    if (evaluatedRisk.user_drawdown_rating) {
        highRiskCount += (evaluatedRisk.user_drawdown_rating === "High") ? 1 : 0;
        totalIndicators++;
    }
    if (evaluatedRisk.user_sharpe_rating) {
        highRiskCount += (evaluatedRisk.user_sharpe_rating === "Poor") ? 1 : 0; // Poor is treated as high risk
        totalIndicators++;
    }
    if (evaluatedRisk.user_beta_rating) {
        highRiskCount += (evaluatedRisk.user_beta_rating === "High") ? 1 : 0;
        totalIndicators++;
    }
    if (evaluatedRisk.user_var_rating) {
        highRiskCount += (evaluatedRisk.user_var_rating === "High") ? 1 : 0;
        totalIndicators++;
    }
    if (evaluatedRisk.user_sortino_rating) {
        highRiskCount += (evaluatedRisk.user_sortino_rating === "Poor") ? 1 : 0; // Poor is treated as high risk
        totalIndicators++;
    }
    
    // Determine overall risk level based on the number of high-risk indicators
    let overallRiskLevel = "Low"; // Default to Low
    if (totalIndicators > 0) {
        const highRiskPercentage = highRiskCount / totalIndicators;
        if (highRiskPercentage >= 0.6) { // Example threshold: 60% or more high risk indicators -> High
            overallRiskLevel = "High";
        } else if (highRiskPercentage >= 0.3) { // Example threshold: 30% to 60% -> Medium
            overallRiskLevel = "Medium";
        }
    }
    
    evaluatedRisk.user_overall_risk = overallRiskLevel;
    
    return evaluatedRisk;
}

/**
 * 创建风险分析卡片
 */
function createRiskCard(container, ticker, data) {
    const card = document.createElement('div');
    card.className = 'risk-card';
    
    const overallRiskLevel = data.user_overall_risk || "N/A"; // Use user-evaluated risk level
    const riskLevelText = getRiskLevelText(overallRiskLevel); 
    const riskClass = getRiskClass(overallRiskLevel);
    
    // 提取指标数据
    const metricsData = {
        "Annualized Volatility": { value: data.volatility !== undefined ? `${data.volatility.toFixed(2)}%` : 'N/A', rating: data.user_volatility_rating },
        "Max Drawdown": { value: data.max_drawdown !== undefined ? `${data.max_drawdown.toFixed(2)}%` : 'N/A', rating: data.user_drawdown_rating },
        "Sharpe Ratio": { value: data.sharpe_ratio !== undefined ? (data.sharpe_ratio === "∞" ? "∞" : data.sharpe_ratio.toFixed(2)) : 'N/A', rating: data.user_sharpe_rating },
        "Beta": { value: data.beta !== undefined ? data.beta.toFixed(2) : 'N/A', rating: data.user_beta_rating },
        "VaR (95%)": { value: data.var_95 !== undefined ? `${data.var_95.toFixed(2)}%` : 'N/A', rating: data.user_var_rating },
        "Sortino Ratio": { value: data.sortino_ratio !== undefined ? (data.sortino_ratio === "∞" ? "∞" : data.sortino_ratio.toFixed(2)) : 'N/A', rating: data.user_sortino_rating }
    };

    // 生成指标表格HTML
    let metricsTableHtml = '<table class="risk-metrics-table"><tbody>';
    for (const [name, metric] of Object.entries(metricsData)) {
        metricsTableHtml += `
            <tr>
                <td>${name}</td>
                <td>${metric.value}</td>
                <td>${getRiskIndicatorHtml(metric.rating)}</td>
            </tr>
        `;
    }
    metricsTableHtml += '</tbody></table>';

    // 构建卡片内容
    card.innerHTML = `
        <div class="risk-header">
            <h3 class="risk-title">
                <span>${ticker}</span>
                <span class="badge ${riskClass} ms-2">${riskLevelText}</span>
                <small class="text-muted ms-auto">(Based on your thresholds)</small>
            </h3>
        </div>
        <div class="risk-body">
            <div class="risk-content-grid">
                <div class="risk-details">
                    <div class="metrics-group mb-4">
                        <h4 class="metrics-group-title">Risk Assessment Summary</h4>
                        <ul>
                            ${generateSummaryPoints(data)} 
                        </ul>
                    </div>
                    <div class="metrics-group">
                        <h4 class="metrics-group-title">Risk Metrics</h4>
                        ${metricsTableHtml}
                    </div>
                </div>
                <div class="risk-gauge-area">
                    ${createGaugeHtml(overallRiskLevel)} 
                </div>
            </div>
        </div>
    `;
    
    container.appendChild(card);
}

/**
 * 生成风险总结点
 */
function generateSummaryPoints(data) {
    let points = [];
    points.push(`Overall risk level assessed as <strong>${getRiskLevelText(data.user_overall_risk)}</strong>.`);
    
    const highRiskMetrics = [];
    if (data.user_volatility_rating === "High") highRiskMetrics.push("Volatility");
    if (data.user_drawdown_rating === "High") highRiskMetrics.push("Max Drawdown");
    if (data.user_sharpe_rating === "Poor") highRiskMetrics.push("Sharpe Ratio");
    if (data.user_beta_rating === "High") highRiskMetrics.push("Beta");
    if (data.user_var_rating === "High") highRiskMetrics.push("VaR (95%)");
    if (data.user_sortino_rating === "Poor") highRiskMetrics.push("Sortino Ratio");

    if (highRiskMetrics.length > 0) {
        points.push(`High risk detected in: <strong>${highRiskMetrics.join(', ')}</strong>.`);
    } else if (data.user_overall_risk !== "N/A") {
        points.push("All individual metrics are within acceptable risk levels based on your thresholds.");
    }

    return points.map(p => `<li>${p}</li>`).join('');
}

/**
 * 获取风险指标的指示符HTML
 */
function getRiskIndicatorHtml(rating) {
    if (rating === "High" || rating === "Poor") {
        // Use smaller badge for table context
        return `<span class="badge bg-danger badge-sm">${rating} Risk</span>`; 
    } else if (rating === "Low" || rating === "Good") {
        // Use smaller badge for table context
        return `<span class="badge bg-success badge-sm">Acceptable</span>`; 
    } else {
        return ''; // No indicator for N/A or potentially Medium
    }
}

/**
 * 创建错误信息卡片
 */
function createErrorCard(container, ticker, errorMessage) {
    const card = document.createElement('div');
    card.className = 'risk-card error-card';
    card.innerHTML = `
        <div class="risk-header">
            <h3 class="risk-title text-danger">
                <i class="fas fa-exclamation-triangle me-2"></i> ${ticker} - Error
            </h3>
        </div>
        <div class="risk-body">
            <p>Could not perform risk analysis for ${ticker}.</p>
            <p class="text-danger"><strong>Error:</strong> ${errorMessage}</p>
        </div>
    `;
    container.appendChild(card);
}

/**
 * 创建仪表盘HTML
 */
function createGaugeHtml(riskLevel) {
    // 将风险等级映射到百分比值
    const riskPercentage = {
        "Low": 25,      // 25%
        "Medium": 50,   // 50%
        "High": 75      // 75%
    };
    
    // 获取对应百分比
    const percentage = riskPercentage[riskLevel] || 0;
    
    // 获取颜色和文本
    const color = getGaugeColor(riskLevel);
    const text = getRiskLevelText(riskLevel);
    
    // 生成仪表盘HTML
    return `
        <div class="gauge-container" style="--gauge-percentage: ${percentage}%; --gauge-color: ${color};">
        <div class="gauge-background"></div>
            <div class="gauge-fill"></div>
            <div class="gauge-center">
                <div class="gauge-center-content">
                    <div class="gauge-value ${getRiskClass(riskLevel)}">${text}</div>
                </div>
            </div>
        </div>
        <div class="gauge-label">Overall Risk Assessment</div>
    `;
}

/**
 * 获取风险等级对应的CSS类
 */
function getRiskClass(riskLevel) {
    switch(riskLevel) {
        case "High": return 'risk-high';
        case "Medium": return 'risk-medium';
        case "Low": return 'risk-low';
        default: return 'risk-unknown';
    }
}

/**
 * 获取风险等级的文本描述
 */
function getRiskLevelText(riskLevel) {
    switch(riskLevel) {
        case "High": return 'High Risk';
        case "Medium": return 'Medium Risk';
        case "Low": return 'Low Risk';
        default: return 'N/A';
    }
}

/**
 * 获取仪表盘颜色
 */
function getGaugeColor(riskLevel) {
    switch(riskLevel) {
        case "High": return '#dc3545'; // Red
        case "Medium": return '#fd7e14'; // Orange
        case "Low": return '#28a745'; // Green
        default: return '#adb5bd'; // Gray
    }
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
    let month = date.getMonth() + 1;
    let day = date.getDate();
    
    month = month < 10 ? '0' + month : month;
    day = day < 10 ? '0' + day : day;
    
    return `${year}-${month}-${day}`;
} 