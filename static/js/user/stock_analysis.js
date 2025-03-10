document.addEventListener('DOMContentLoaded', function() {
    // 设置默认日期
    const today = new Date();
    const oneYearAgo = new Date();
    oneYearAgo.setFullYear(today.getFullYear() - 1);
    
    document.getElementById('end_date').value = formatDate(today);
    document.getElementById('start_date').value = formatDate(oneYearAgo);
    
    // 表单提交处理
    document.getElementById('stock-analysis-form').addEventListener('submit', function(e) {
        e.preventDefault();
        
        // 显示加载状态
        document.getElementById('loading-indicator').classList.remove('d-none');
        document.getElementById('risk-dashboard').innerHTML = '';
        document.getElementById('error-container').classList.add('d-none');
        
        // 获取表单数据
        const formData = new FormData(this);
        
        // 发送请求
        fetch('/user/api/stock_analysis', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            console.log('收到响应:', response.status, response.statusText);
            if (!response.ok) {
                return response.json().then(err => {
                    console.error('响应错误:', err);
                    throw new Error(err.error || '请求失败');
                });
            }
            return response.json();
        })
        .then(data => {
            console.log('收到数据:', data);
            // 隐藏加载状态
            document.getElementById('loading-indicator').classList.add('d-none');
            
            // 处理并显示结果
            const processedResults = processResults(data);
            console.log('处理后的数据:', processedResults);
            createRiskDashboard(processedResults);
        })
        .catch(error => {
            // 隐藏加载状态
            document.getElementById('loading-indicator').classList.add('d-none');
            
            // 显示错误信息
            displayError('分析请求失败: ' + error.message);
            console.error('分析请求失败:', error);
        });
    });
    
    // 添加股票输入字段
    document.getElementById('add-ticker').addEventListener('click', function() {
        const tickersContainer = document.getElementById('tickers-container');
        const tickerCount = tickersContainer.querySelectorAll('.ticker-input').length;
        
        const newTickerGroup = document.createElement('div');
        newTickerGroup.className = 'ticker-input input-group mb-2';
        newTickerGroup.innerHTML = `
            <input type="text" name="tickers" class="form-control" placeholder="股票代码 ${tickerCount + 1}" required>
            <button type="button" class="btn btn-outline-danger remove-ticker">删除</button>
        `;
        
        tickersContainer.appendChild(newTickerGroup);
        
        // 添加删除按钮事件
        newTickerGroup.querySelector('.remove-ticker').addEventListener('click', function() {
            newTickerGroup.remove();
        });
    });
});

// 显示错误信息
function showError(message) {
    const dashboard = document.getElementById('risk-dashboard');
    dashboard.innerHTML = `<div class="risk-card"><div class="risk-header risk-high">
        <h2 class="risk-title">错误</h2></div>
        <p>${message}</p></div>`;
    document.getElementById('analysis-results').style.display = 'block';
}

// 解析分析结果文本
function parseAnalysisResults(resultsText) {
    const results = {};
    const tickerRegex = /\n([A-Z]+) 详细分析:/g;
    let match;
    let tickers = [];
    
    // 提取所有股票代码
    while ((match = tickerRegex.exec(resultsText)) !== null) {
        tickers.push(match[1]);
    }
    
    // 为每个股票解析详细信息
    tickers.forEach(ticker => {
        const tickerData = {};
        
        // 提取估值指标
        const valuationRegex = new RegExp(`${ticker} 详细分析:[\\s\\S]*?估值指标:[\\s\\S]*?-{40}([\\s\\S]*?)(?:风险指标:|$)`, 'i');
        const valuationMatch = resultsText.match(valuationRegex);
        if (valuationMatch) {
            tickerData.valuation = parseMetrics(valuationMatch[1]);
        }
        
        // 提取风险指标
        const riskRegex = new RegExp(`${ticker} 详细分析:[\\s\\S]*?风险指标:[\\s\\S]*?-{40}([\\s\\S]*?)(?:内在价值估计:|警报:|$)`, 'i');
        const riskMatch = resultsText.match(riskRegex);
        if (riskMatch) {
            tickerData.risk = parseMetrics(riskMatch[1]);
        }
        
        // 提取内在价值估计
        const intrinsicRegex = new RegExp(`${ticker} 详细分析:[\\s\\S]*?内在价值估计:[\\s\\S]*?-{40}([\\s\\S]*?)(?:警报:|$)`, 'i');
        const intrinsicMatch = resultsText.match(intrinsicRegex);
        if (intrinsicMatch) {
            tickerData.intrinsic = parseMetrics(intrinsicMatch[1]);
        }
        
        // 提取警报
        const alertsRegex = new RegExp(`${ticker} 详细分析:[\\s\\S]*?警报:[\\s\\S]*?-{40}([\\s\\S]*?)(?:=+|$)`, 'i');
        const alertsMatch = resultsText.match(alertsRegex);
        if (alertsMatch) {
            tickerData.alerts = parseAlerts(alertsMatch[1]);
        }
        
        results[ticker] = tickerData;
    });
    
    return { tickers, data: results };
}

// 解析指标文本
function parseMetrics(metricsText) {
    const metrics = {};
    const lines = metricsText.split('\n');
    
    lines.forEach(line => {
        line = line.trim();
        if (!line) return;
        
        // 匹配 "  指标名称: 值" 格式
        const match = line.match(/^\s*(.+?):\s*(.+)$/);
        if (match) {
            const key = match[1].trim();
            const value = match[2].trim();
            metrics[key] = value;
        }
    });
    
    return metrics;
}

// 解析警报文本
function parseAlerts(alertsText) {
    const alerts = {
        valuation: [],
        risk: []
    };
    
    const lines = alertsText.split('\n');
    let currentType = null;
    
    lines.forEach(line => {
        line = line.trim();
        if (!line) return;
        
        if (line.includes('估值警报:')) {
            currentType = 'valuation';
        } else if (line.includes('风险警报:')) {
            currentType = 'risk';
        } else if (line.startsWith('-') && currentType) {
            alerts[currentType].push(line.substring(1).trim());
        }
    });
    
    return alerts;
}

// 创建风险仪表盘
function createRiskDashboard(results) {
    try {
        console.log('创建仪表盘，数据:', results);
        const dashboardContainer = document.getElementById('risk-dashboard');
        dashboardContainer.innerHTML = ''; // 清空现有内容
        
        // 检查数据结构
        if (!results || !results.tickers || !results.data) {
            displayError('数据结构不正确，无法创建仪表盘');
            console.error('数据结构不正确:', results);
            return;
        }
        
        // 显示分析日期范围
        const dateRangeInfo = document.createElement('div');
        dateRangeInfo.className = 'date-range-info mb-4';
        dateRangeInfo.innerHTML = `<strong>分析日期范围:</strong> ${results.start_date || '未知'} 至 ${results.end_date || '未知'}`;
        dashboardContainer.appendChild(dateRangeInfo);
        
        // 为每个股票创建风险卡片
        results.tickers.forEach(ticker => {
            const tickerData = results.data[ticker];
            if (!tickerData) {
                console.warn(`没有找到 ${ticker} 的数据`);
                return;
            }
            
            // 确保metrics字段存在
            if (!tickerData.metrics) {
                tickerData.metrics = {};
                // 尝试从旧格式转换
                if (tickerData.risk) tickerData.metrics['风险指标'] = tickerData.risk;
                if (tickerData.valuation) tickerData.metrics['估值指标'] = tickerData.valuation;
            }
            
            // 创建股票卡片
            const card = document.createElement('div');
            card.className = 'card mb-4 risk-card';
            
            // 计算总体风险评级
            const riskRating = calculateRiskRating(tickerData);
            const riskColor = getRiskColor(riskRating);
            
            // 卡片头部
            const cardHeader = document.createElement('div');
            cardHeader.className = 'card-header d-flex justify-content-between align-items-center';
            cardHeader.innerHTML = `
                <h5 class="mb-0">${ticker} - ${tickerData.name || '股票'}</h5>
                <span class="badge" style="background-color: ${riskColor}">风险评级: ${riskRating.toFixed(1)}/10</span>
            `;
            card.appendChild(cardHeader);
            
            // 卡片内容
            const cardBody = document.createElement('div');
            cardBody.className = 'card-body';
            
            // 创建仪表盘行
            const gaugeRow = document.createElement('div');
            gaugeRow.className = 'row mb-4';
            
            // 创建仪表盘列
            const gaugeCol = document.createElement('div');
            gaugeCol.className = 'col-md-4 text-center';
            gaugeCol.innerHTML = `<h6>总体风险评级</h6>`;
            
            // 直接创建仪表盘
            const gaugeElement = createGaugeChart(ticker, riskRating, riskColor);
            if (gaugeElement) {
                gaugeCol.appendChild(gaugeElement);
            } else {
                // 如果创建失败，显示简单的文本
                gaugeCol.innerHTML += `
                    <div class="gauge-container">
                        <div class="gauge-value" style="color: ${riskColor}; font-size: 24px; font-weight: bold;">
                            ${riskRating.toFixed(1)}/10
                        </div>
                    </div>
                `;
            }
            
            gaugeRow.appendChild(gaugeCol);
            
            // 添加指标表格
            const metricsCol = document.createElement('div');
            metricsCol.className = 'col-md-8';
            
            // 创建指标表格
            const metricsTable = document.createElement('table');
            metricsTable.className = 'table table-sm table-bordered metrics-table';
            metricsTable.innerHTML = `
                <thead>
                    <tr>
                        <th>指标类别</th>
                        <th>指标</th>
                        <th>值</th>
                        <th>风险等级</th>
                    </tr>
                </thead>
                <tbody>
                    ${createMetricsTableRows(tickerData)}
                </tbody>
            `;
            metricsCol.appendChild(metricsTable);
            gaugeRow.appendChild(metricsCol);
            
            cardBody.appendChild(gaugeRow);
            
            // 添加警报（如果有）
            if (tickerData.alerts && tickerData.alerts.length > 0) {
                const alertsContainer = document.createElement('div');
                alertsContainer.className = 'alerts-container mt-3';
                
                const alertsTitle = document.createElement('h6');
                alertsTitle.textContent = '风险警报:';
                alertsContainer.appendChild(alertsTitle);
                
                const alertsList = document.createElement('ul');
                alertsList.className = 'list-group';
                
                tickerData.alerts.forEach(alert => {
                    const alertItem = document.createElement('li');
                    alertItem.className = 'list-group-item list-group-item-danger';
                    alertItem.textContent = alert;
                    alertsList.appendChild(alertItem);
                });
                
                alertsContainer.appendChild(alertsList);
                cardBody.appendChild(alertsContainer);
            }
            
            card.appendChild(cardBody);
            dashboardContainer.appendChild(card);
        });
        
        // 显示原始结果切换按钮
        const toggleContainer = document.createElement('div');
        toggleContainer.className = 'text-center mt-4';
        toggleContainer.innerHTML = `
            <button id="toggle-raw-results" class="btn btn-outline-secondary">
                显示原始结果
            </button>
        `;
        dashboardContainer.appendChild(toggleContainer);
        
        // 添加原始结果容器（默认隐藏）
        const rawResultsContainer = document.createElement('div');
        rawResultsContainer.id = 'raw-results-container';
        rawResultsContainer.className = 'mt-4 d-none';
        rawResultsContainer.innerHTML = `<pre>${JSON.stringify(results, null, 2)}</pre>`;
        dashboardContainer.appendChild(rawResultsContainer);
        
        // 添加切换按钮事件
        document.getElementById('toggle-raw-results').addEventListener('click', function() {
            const rawResults = document.getElementById('raw-results-container');
            const button = document.getElementById('toggle-raw-results');
            
            if (rawResults.classList.contains('d-none')) {
                rawResults.classList.remove('d-none');
                button.textContent = '隐藏原始结果';
            } else {
                rawResults.classList.add('d-none');
                button.textContent = '显示原始结果';
            }
        });
        
    } catch (error) {
        console.error('创建风险仪表盘时出错:', error);
        displayError('创建仪表盘时出错: ' + error.message);
    }
}

// 创建文本版仪表盘（当Chart.js无法加载时使用）
function createTextDashboard(results) {
    const dashboard = document.getElementById('risk-dashboard');
    
    results.tickers.forEach(ticker => {
        const tickerData = results.tickersData[ticker];
        if (!tickerData) return;
        
        // 计算风险评级
        const riskRating = calculateRiskRating(tickerData);
        
        // 创建股票卡片
        const card = document.createElement('div');
        card.className = 'risk-card';
        
        // 添加标题
        const header = document.createElement('div');
        header.className = 'risk-header';
        header.classList.add(getRiskClass(riskRating.overall));
        
        header.innerHTML = `
            <h2 class="risk-title">${ticker} 风险评级: ${getRiskLabel(riskRating.overall)}</h2>
            <p class="risk-subtitle">主要风险: ${getMainRisks(tickerData)}</p>
        `;
        card.appendChild(header);
        
        // 添加文本版仪表盘
        const gaugeContainer = document.createElement('div');
        gaugeContainer.className = 'gauge-container';
        
        // 财务健康
        const financialHealth = document.createElement('div');
        financialHealth.className = 'gauge-item';
        financialHealth.innerHTML = `
            <div class="gauge-label">财务健康</div>
            <div class="gauge-value ${getRiskClass(riskRating.financial, true)}">${riskRating.financial.toFixed(1)}</div>
            <div class="gauge-scale">/10</div>
        `;
        gaugeContainer.appendChild(financialHealth);
        
        // 运营风险
        const operationalRisk = document.createElement('div');
        operationalRisk.className = 'gauge-item';
        operationalRisk.innerHTML = `
            <div class="gauge-label">运营风险</div>
            <div class="gauge-value ${getRiskClass(riskRating.operational, true)}">${riskRating.operational.toFixed(1)}</div>
            <div class="gauge-scale">/10</div>
        `;
        gaugeContainer.appendChild(operationalRisk);
        
        // 估值风险
        const valuationRisk = document.createElement('div');
        valuationRisk.className = 'gauge-item';
        valuationRisk.innerHTML = `
            <div class="gauge-label">估值风险</div>
            <div class="gauge-value ${getRiskClass(riskRating.valuation, true)}">${riskRating.valuation.toFixed(1)}</div>
            <div class="gauge-scale">/10</div>
        `;
        gaugeContainer.appendChild(valuationRisk);
        
        card.appendChild(gaugeContainer);
        
        // 添加指标表格
        const metricsTable = document.createElement('table');
        metricsTable.className = 'metrics-table';
        metricsTable.innerHTML = `
            <thead>
                <tr>
                    <th>指标</th>
                    <th>当前值</th>
                    <th>风险评级</th>
                </tr>
            </thead>
            <tbody>
                ${createSimpleMetricsTableRows(tickerData)}
            </tbody>
        `;
        card.appendChild(metricsTable);
        
        // 添加警报部分
        if (tickerData.alerts && (tickerData.alerts.valuation.length > 0 || tickerData.alerts.risk.length > 0)) {
            const alertsSection = document.createElement('div');
            alertsSection.innerHTML = `<h3>风险警报</h3>`;
            
            if (tickerData.alerts.valuation.length > 0) {
                const valAlerts = document.createElement('div');
                valAlerts.innerHTML = `
                    <h4>估值警报</h4>
                    <ul>${tickerData.alerts.valuation.map(a => `<li>${a}</li>`).join('')}</ul>
                `;
                alertsSection.appendChild(valAlerts);
            }
            
            if (tickerData.alerts.risk.length > 0) {
                const riskAlerts = document.createElement('div');
                riskAlerts.innerHTML = `
                    <h4>风险警报</h4>
                    <ul>${tickerData.alerts.risk.map(a => `<li>${a}</li>`).join('')}</ul>
                `;
                alertsSection.appendChild(riskAlerts);
            }
            
            card.appendChild(alertsSection);
        }
        
        dashboard.appendChild(card);
    });
}

// 创建简化版指标表格行（用于文本版仪表盘）
function createSimpleMetricsTableRows(tickerData) {
    const rows = [];
    
    // 合并风险和估值指标
    const allMetrics = {};
    
    if (tickerData.risk) {
        Object.entries(tickerData.risk).forEach(([key, value]) => {
            allMetrics[key] = { value, type: 'risk' };
        });
    }
    
    if (tickerData.valuation) {
        Object.entries(tickerData.valuation).forEach(([key, value]) => {
            allMetrics[key] = { value, type: 'valuation' };
        });
    }
    
    // 创建表格行
    Object.entries(allMetrics).forEach(([key, data]) => {
        // 跳过一些不需要显示的指标
        if (['状态'].includes(key)) return;
        
        // 计算风险评级
        const riskLevel = calculateMetricRiskLevel(key, data.value);
        const riskClass = getRiskClass(riskLevel, false);
        
        rows.push(`
            <tr>
                <td>${formatMetricName(key)}</td>
                <td>${data.value}</td>
                <td class="${riskClass}">${getRiskLabel(riskLevel)}</td>
            </tr>
        `);
    });
    
    return rows.join('');
}

// 创建指标表格行
function createMetricsTableRows(tickerData) {
    let rows = '';
    
    // 检查数据结构
    if (!tickerData || !tickerData.metrics) {
        console.warn('无法创建指标表格行，metrics字段不存在');
        return '<tr><td colspan="4" class="text-center">无可用指标数据</td></tr>';
    }
    
    // 遍历所有指标类别
    for (const category in tickerData.metrics) {
        const metrics = tickerData.metrics[category];
        
        // 检查metrics是否为对象
        if (!metrics || typeof metrics !== 'object') {
            continue;
        }
        
        // 遍历该类别下的所有指标
        for (const metric in metrics) {
            const value = metrics[metric];
            
            // 只处理数值型指标
            if (typeof value === 'number') {
                // 计算风险等级
                const riskLevel = value;
                const riskColor = getRiskColor(riskLevel);
                
                // 创建表格行
                rows += `
                    <tr>
                        <td>${category}</td>
                        <td>${formatMetricName(metric)}</td>
                        <td>${value.toFixed(2)}</td>
                        <td><span class="badge" style="background-color: ${riskColor}">${riskLevel.toFixed(1)}</span></td>
                    </tr>
                `;
            }
        }
    }
    
    // 如果没有行，返回一个提示
    if (!rows) {
        return '<tr><td colspan="4" class="text-center">无可用指标数据</td></tr>';
    }
    
    return rows;
}

// 计算风险评级
function calculateRiskRating(tickerData) {
    // 检查数据结构
    if (!tickerData || !tickerData.metrics) {
        console.warn('无法计算风险评级，metrics字段不存在');
        return 5; // 返回默认中等风险
    }
    
    // 简单计算风险评级 (0-10，10为最高风险)
    let riskScore = 0;
    let metricCount = 0;
    
    // 遍历所有指标
    for (const category in tickerData.metrics) {
        const metrics = tickerData.metrics[category];
        
        // 检查metrics是否为对象
        if (!metrics || typeof metrics !== 'object') {
            continue;
        }
        
        for (const metric in metrics) {
            const value = metrics[metric];
            if (typeof value === 'number') {
                // 假设每个指标的风险在0-10之间
                riskScore += value;
                metricCount++;
            }
        }
    }
    
    // 计算平均风险
    return metricCount > 0 ? riskScore / metricCount : 5;
}

// 获取风险颜色
function getRiskColor(riskRating) {
    // 根据风险评级返回颜色
    if (riskRating < 3) return '#28a745'; // 低风险 - 绿色
    if (riskRating < 6) return '#ffc107'; // 中等风险 - 黄色
    if (riskRating < 8) return '#fd7e14'; // 高风险 - 橙色
    return '#dc3545'; // 极高风险 - 红色
}

// 计算单个指标的风险等级
function calculateMetricRiskLevel(metricName, value) {
    // 默认风险等级为中等
    let riskLevel = 5;
    
    // 尝试提取数值
    let numValue = parseFloat(value.replace(/[%$]/g, ''));
    if (isNaN(numValue)) return riskLevel;
    
    // 根据不同指标计算风险等级
    switch(metricName.toLowerCase()) {
        case '市盈率 (p/e)':
        case '预期市盈率':
            if (numValue > 30) riskLevel = 8;
            else if (numValue > 20) riskLevel = 6;
            else if (numValue > 15) riskLevel = 5;
            else if (numValue > 10) riskLevel = 3;
            else if (numValue > 0) riskLevel = 2;
            break;
            
        case '市净率 (p/b)':
            if (numValue > 5) riskLevel = 8;
            else if (numValue > 3) riskLevel = 6;
            else if (numValue > 2) riskLevel = 5;
            else if (numValue > 1) riskLevel = 3;
            else if (numValue > 0) riskLevel = 2;
            break;
            
        case '市销率 (p/s)':
            if (numValue > 10) riskLevel = 8;
            else if (numValue > 5) riskLevel = 6;
            else if (numValue > 3) riskLevel = 5;
            else if (numValue > 1) riskLevel = 3;
            else if (numValue > 0) riskLevel = 2;
            break;
            
        case '年化波动率':
            if (numValue > 0.3) riskLevel = 8;
            else if (numValue > 0.2) riskLevel = 6;
            else if (numValue > 0.15) riskLevel = 5;
            else if (numValue > 0.1) riskLevel = 3;
            else riskLevel = 2;
            break;
            
        case '贝塔系数':
        case '回归贝塔':
            if (numValue > 1.5) riskLevel = 8;
            else if (numValue > 1.2) riskLevel = 6;
            else if (numValue > 1) riskLevel = 5;
            else if (numValue > 0.8) riskLevel = 4;
            else if (numValue > 0) riskLevel = 2;
            break;
            
        case '夏普比率':
            if (numValue > 2) riskLevel = 2;
            else if (numValue > 1.5) riskLevel = 3;
            else if (numValue > 1) riskLevel = 4;
            else if (numValue > 0.5) riskLevel = 6;
            else riskLevel = 8;
            break;
            
        case '最大回撤':
            numValue = Math.abs(numValue);
            if (numValue > 0.3) riskLevel = 8;
            else if (numValue > 0.2) riskLevel = 6;
            else if (numValue > 0.15) riskLevel = 5;
            else if (numValue > 0.1) riskLevel = 3;
            else riskLevel = 2;
            break;
    }
    
    return riskLevel;
}

// 获取风险等级标签
function getRiskLabel(riskLevel) {
    if (riskLevel >= 7) return '高风险';
    if (riskLevel >= 4) return '中等风险';
    return '低风险';
}

// 获取风险等级CSS类
function getRiskClass(riskLevel, isGauge = false) {
    if (isGauge) {
        // 对于仪表盘，值越高越好
        if (riskLevel <= 3) return 'risk-high';
        if (riskLevel <= 6) return 'risk-medium';
        return 'risk-low';
    } else {
        // 对于风险评级，值越高风险越高
        if (riskLevel >= 7) return 'risk-high';
        if (riskLevel >= 4) return 'risk-medium';
        return 'risk-low';
    }
}

// 获取主要风险描述
function getMainRisks(tickerData) {
    const risks = [];
    
    // 检查估值风险
    if (tickerData.valuation) {
        const pe = parseFloat(tickerData.valuation['市盈率 (P/E)']) || 0;
        if (pe > 25) {
            risks.push('估值过高');
        }
    }
    
    // 检查财务风险
    if (tickerData.risk) {
        const volatility = parseFloat(tickerData.risk['年化波动率']) || 0;
        if (volatility > 0.25) {
            risks.push('波动率高');
        }
        
        const beta = parseFloat(tickerData.risk['贝塔系数'] || tickerData.risk['回归贝塔']) || 0;
        if (beta > 1.3) {
            risks.push('市场敏感度高');
        }
        
        const sharpe = parseFloat(tickerData.risk['夏普比率']) || 0;
        if (sharpe < 0.8) {
            risks.push('风险调整回报低');
        }
    }
    
    // 检查内在价值
    if (tickerData.intrinsic && tickerData.intrinsic['价格/价值比']) {
        const priceToValue = parseFloat(tickerData.intrinsic['价格/价值比']) || 1;
        if (priceToValue > 1.3) {
            risks.push('高于内在价值');
        }
    }
    
    // 如果没有发现明显风险
    if (risks.length === 0) {
        return '未发现明显风险';
    }
    
    return risks.join('，');
}

// 格式化指标名称
function formatMetricName(metricName) {
    // 将下划线替换为空格，并将首字母大写
    return metricName
        .replace(/_/g, ' ')
        .replace(/\b\w/g, l => l.toUpperCase());
}

// 创建仪表盘图表 - 使用纯CSS和HTML
function createGaugeChart(id, value, color) {
    try {
        // 直接创建一个新的仪表盘容器
        const gaugeContainer = document.createElement('div');
        gaugeContainer.className = 'gauge-container';
        gaugeContainer.id = `gauge-container-${id}`;
        
        // 创建CSS仪表盘
        const gaugeVisual = document.createElement('div');
        gaugeVisual.className = 'gauge-visual';
        
        // 背景
        const gaugeBackground = document.createElement('div');
        gaugeBackground.className = 'gauge-background';
        gaugeVisual.appendChild(gaugeBackground);
        
        // 填充部分
        const gaugeFill = document.createElement('div');
        gaugeFill.className = 'gauge-fill';
        gaugeFill.style.backgroundColor = color;
        
        // 计算填充角度 (0-10 => 0-180度)
        const fillDegree = (value / 10) * 180;
        gaugeFill.style.transform = `rotate(${fillDegree - 180}deg)`;
        gaugeVisual.appendChild(gaugeFill);
        
        // 中心空白
        const gaugeCenter = document.createElement('div');
        gaugeCenter.className = 'gauge-center';
        gaugeVisual.appendChild(gaugeCenter);
        
        // 添加刻度标记
        for (let i = 0; i <= 10; i += 2) {
            const marker = document.createElement('div');
            marker.className = 'gauge-marker';
            marker.style.transform = `rotate(${(i / 10) * 180 - 90}deg)`;
            gaugeVisual.appendChild(marker);
        }
        
        // 添加值显示
        const gaugeValue = document.createElement('div');
        gaugeValue.className = 'gauge-value';
        gaugeValue.textContent = value.toFixed(1);
        
        // 将仪表盘添加到容器
        gaugeContainer.appendChild(gaugeVisual);
        gaugeContainer.appendChild(gaugeValue);
        
        console.log(`成功创建CSS仪表盘: ${id}`);
        return gaugeContainer;
    } catch (error) {
        console.error('创建仪表盘时出错:', error);
        return null;
    }
}

// 辅助函数：格式化日期为 YYYY-MM-DD
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    
    return `${year}-${month}-${day}`;
}

// 显示错误信息
function displayError(message) {
    const errorContainer = document.getElementById('error-container');
    errorContainer.textContent = message;
    errorContainer.classList.remove('d-none');
    
    // 5秒后自动隐藏错误信息
    setTimeout(() => {
        errorContainer.classList.add('d-none');
    }, 5000);
}

// 处理分析结果
function processResults(results) {
    try {
        console.log('处理分析结果:', results);
        
        // 如果结果为空，返回一个基本结构
        if (!results) {
            console.error('结果为空');
            return {
                tickers: [],
                data: {},
                start_date: formatDate(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)),
                end_date: formatDate(new Date())
            };
        }
        
        // 提取股票代码列表
        let tickers = results.tickers || [];
        
        // 如果tickers不是数组，尝试从其他字段提取
        if (!Array.isArray(tickers)) {
            console.warn('tickers不是数组，尝试从其他字段提取');
            tickers = [];
            
            // 尝试从data字段提取
            if (results.data && typeof results.data === 'object') {
                tickers = Object.keys(results.data);
            }
            // 尝试从结果对象本身提取
            else {
                for (const key in results) {
                    if (typeof results[key] === 'object' && results[key] !== null && key !== 'data' && key !== 'tickers') {
                        tickers.push(key);
                    }
                }
            }
        }
        
        // 确保data字段存在
        if (!results.data || typeof results.data !== 'object') {
            console.warn('data字段不存在或不是对象，尝试创建');
            results.data = {};
            
            // 如果没有data字段，尝试从旧格式转换
            tickers.forEach(ticker => {
                if (results[ticker] && typeof results[ticker] === 'object') {
                    results.data[ticker] = results[ticker];
                }
            });
        }
        
        // 确保每个股票数据中有metrics字段
        tickers.forEach(ticker => {
            const tickerData = results.data[ticker];
            if (tickerData && typeof tickerData === 'object') {
                // 如果没有metrics字段，创建一个
                if (!tickerData.metrics || typeof tickerData.metrics !== 'object') {
                    console.warn(`${ticker} 没有metrics字段，尝试创建`);
                    tickerData.metrics = {};
                    
                    // 尝试从旧格式转换
                    if (tickerData.risk && typeof tickerData.risk === 'object') {
                        tickerData.metrics['风险指标'] = tickerData.risk;
                    }
                    
                    if (tickerData.valuation && typeof tickerData.valuation === 'object') {
                        tickerData.metrics['估值指标'] = tickerData.valuation;
                    }
                    
                    // 尝试从内在价值字段转换
                    if (tickerData.intrinsic && typeof tickerData.intrinsic === 'object') {
                        tickerData.metrics['内在价值'] = tickerData.intrinsic;
                    }
                }
                
                // 确保有alerts字段
                if (!tickerData.alerts || !Array.isArray(tickerData.alerts)) {
                    console.warn(`${ticker} 没有alerts字段或不是数组，尝试创建`);
                    tickerData.alerts = [];
                    
                    // 尝试从旧格式转换
                    if (tickerData.alerts_risk && Array.isArray(tickerData.alerts_risk)) {
                        tickerData.alerts = tickerData.alerts.concat(tickerData.alerts_risk);
                    }
                    
                    if (tickerData.alerts_valuation && Array.isArray(tickerData.alerts_valuation)) {
                        tickerData.alerts = tickerData.alerts.concat(tickerData.alerts_valuation);
                    }
                }
            } else {
                console.warn(`${ticker} 的数据不存在或不是对象`);
                results.data[ticker] = {
                    name: ticker,
                    metrics: {},
                    alerts: []
                };
            }
        });
        
        // 添加日期范围
        if (!results.start_date) {
            results.start_date = formatDate(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000));
        }
        
        if (!results.end_date) {
            results.end_date = formatDate(new Date());
        }
        
        // 更新tickers字段
        results.tickers = tickers;
        
        return results;
    } catch (error) {
        console.error('处理结果时出错:', error);
        return {
            tickers: [],
            data: {},
            start_date: formatDate(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)),
            end_date: formatDate(new Date()),
            error: error.message
        };
    }
} 