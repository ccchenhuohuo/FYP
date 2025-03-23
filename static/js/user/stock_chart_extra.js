document.addEventListener('DOMContentLoaded', function() {
    // 选项卡切换功能
    const tabs = document.querySelectorAll('.tab-button');
    const contents = document.querySelectorAll('.tab-content');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // 移除所有活动状态
            tabs.forEach(t => t.classList.remove('active'));
            contents.forEach(c => c.classList.remove('active'));
            
            // 添加当前活动状态
            tab.classList.add('active');
            const target = tab.id.replace('tab', 'content');
            document.getElementById(target).classList.add('active');
        });
    });
    
    // 加载基本面数据
    const stockSelector = document.getElementById('stockSelector');
    
    function formatNumber(num) {
        if (num === null || num === undefined) return '-';
        
        // 对于大数值，转换为适当的单位（百万或十亿）
        if (Math.abs(num) >= 1e9) {
            return (num / 1e9).toFixed(2) + '十亿';
        } else if (Math.abs(num) >= 1e6) {
            return (num / 1e6).toFixed(2) + '百万';
        } else {
            return num.toLocaleString();
        }
    }
    
    function formatPercentage(num) {
        if (num === null || num === undefined) return '-';
        return num.toFixed(2) + '%';
    }
    
    function formatRatio(num) {
        if (num === null || num === undefined) return '-';
        return num.toFixed(2);
    }
    
    function formatDate(date) {
        if (!date || isNaN(date)) return '-';
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }
    
    function loadFundamentalData(ticker) {
        document.getElementById('loadingFundamental').style.display = 'block';
        document.getElementById('fundamentalData').style.display = 'none';
        document.getElementById('errorFundamental').style.display = 'none';
        
        fetch(`${window.location.origin}/user/api/fundamental_data?ticker=${ticker}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP状态码: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                // 填充数据
                document.getElementById('marketCap').textContent = formatNumber(data.market_cap);
                document.getElementById('peRatio').textContent = formatRatio(data.pe_ratio);
                document.getElementById('pbRatio').textContent = formatRatio(data.pb_ratio);
                document.getElementById('dividendYield').textContent = formatPercentage(data.dividend_yield);
                document.getElementById('revenue').textContent = formatNumber(data.revenue);
                document.getElementById('netIncome').textContent = formatNumber(data.net_income);
                document.getElementById('operatingCashFlow').textContent = formatNumber(data.operating_cash_flow);
                
                document.getElementById('fundamentalDate').textContent = `数据更新日期: ${formatDate(new Date(data.date))}`;
                document.getElementById('fundamentalData').style.display = 'grid';
            })
            .catch(error => {
                console.error('加载基本面数据错误:', error);
                document.getElementById('errorFundamental').querySelector('span').textContent = `加载基本面数据失败: ${error.message}`;
                document.getElementById('errorFundamental').style.display = 'block';
            })
            .finally(() => {
                document.getElementById('loadingFundamental').style.display = 'none';
            });
    }
    
    function loadBalanceSheet(ticker) {
        document.getElementById('loadingBalance').style.display = 'block';
        document.getElementById('balanceData').style.display = 'none';
        document.getElementById('errorBalance').style.display = 'none';
        
        fetch(`${window.location.origin}/user/api/balance_sheet?ticker=${ticker}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP状态码: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('资产负债表数据:', data); // 调试输出
                
                try {
                    // 安全地设置元素内容 - 添加元素存在性检查
                    const safeSetText = (id, value) => {
                        const element = document.getElementById(id);
                        if (element) {
                            element.textContent = formatNumber(value);
                        } else {
                            console.warn(`元素 #${id} 不存在`);
                        }
                    };
                    
                    // 填充数据 - 使用安全的方法
                    safeSetText('currentAssets', data.current_assets);
                    safeSetText('nonCurrentAssets', data.non_current_assets);
                    safeSetText('totalAssets', data.total_assets);
                    safeSetText('currentLiabilities', data.current_liabilities);
                    safeSetText('nonCurrentLiabilities', data.non_current_liabilities);
                    safeSetText('totalLiabilities', data.total_liabilities);
                    safeSetText('totalEquity', data.total_equity);
                    
                    // 注意: HTML中使用了"equity"而不是"totalEquity"
                    safeSetText('equity', data.total_equity);
                    
                    const dateElement = document.getElementById('balanceDate');
                    if (dateElement) {
                        dateElement.textContent = `数据更新日期: ${formatDate(new Date(data.date))}`;
                    }
                    
                    const balanceData = document.getElementById('balanceData');
                    if (balanceData) {
                        balanceData.style.display = 'block';
                    }
                } catch (err) {
                    console.error('处理资产负债表数据时出错:', err);
                    throw new Error(`处理数据时出错: ${err.message}`);
                }
            })
            .catch(error => {
                console.error('加载资产负债表数据错误:', error);
                const errorElement = document.getElementById('errorBalance');
                if (errorElement && errorElement.querySelector('span')) {
                    errorElement.querySelector('span').textContent = `加载资产负债表数据失败: ${error.message}`;
                    errorElement.style.display = 'block';
                }
            })
            .finally(() => {
                const loadingElement = document.getElementById('loadingBalance');
                if (loadingElement) {
                    loadingElement.style.display = 'none';
                }
            });
    }
    
    function loadIncomeStatement(ticker) {
        document.getElementById('loadingIncome').style.display = 'block';
        document.getElementById('incomeData').style.display = 'none';
        document.getElementById('errorIncome').style.display = 'none';
        
        fetch(`${window.location.origin}/user/api/income_statement?ticker=${ticker}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP状态码: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                // 填充数据
                document.getElementById('incomeRevenue').textContent = formatNumber(data.revenue);
                document.getElementById('costOfRevenue').textContent = formatNumber(data.cost_of_revenue);
                document.getElementById('grossProfit').textContent = formatNumber(data.gross_profit);
                document.getElementById('operatingIncome').textContent = formatNumber(data.operating_income);
                document.getElementById('incomeBeforeTax').textContent = formatNumber(data.income_before_tax);
                document.getElementById('incomeNetIncome').textContent = formatNumber(data.net_income);
                
                // 计算利润率
                const profitMargin = data.revenue ? (data.net_income / data.revenue * 100) : null;
                document.getElementById('profitMargin').textContent = formatPercentage(profitMargin);
                
                document.getElementById('incomeDate').textContent = `数据更新日期: ${formatDate(new Date(data.date))}`;
                document.getElementById('incomeData').style.display = 'block';
            })
            .catch(error => {
                console.error('加载利润表数据错误:', error);
                document.getElementById('errorIncome').querySelector('span').textContent = `加载利润表数据失败: ${error.message}`;
                document.getElementById('errorIncome').style.display = 'block';
            })
            .finally(() => {
                document.getElementById('loadingIncome').style.display = 'none';
            });
    }
    
    function loadMonteCarloSimulation(ticker) {
        const simulationDays = document.getElementById('simulationDays').value || 60;
        const simulationCount = document.getElementById('simulationCount').value || 200;
        
        // 更新URL中的查询参数
        const url = `${window.location.origin}/user/api/monte-carlo/${ticker}?days=${simulationDays}&simulations=${simulationCount}`;
        
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP状态码: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                
                // 保存模拟数据到全局变量，供图表使用
                window.monteCarloData = data; // 直接使用整个数据对象
                
                // 显示模拟统计数据
                const statsDiv = document.getElementById('simulationStats');
                statsDiv.innerHTML = `
                    <div class="row">
                        <div class="col-md-6">
                            <h5><i class="fas fa-calculator"></i> 模拟统计</h5>
                            <table class="table table-sm table-bordered">
                                <tr>
                                    <td>当前价格</td>
                                    <td class="text-end">${formatNumber(data.current_price)}</td>
                                </tr>
                                <tr>
                                    <td>模拟天数</td>
                                    <td class="text-end">${simulationDays} 天</td>
                                </tr>
                                <tr>
                                    <td>模拟次数</td>
                                    <td class="text-end">${simulationCount}</td>
                                </tr>
                                <tr>
                                    <td>预测平均价格</td>
                                    <td class="text-end">${formatNumber(data.mean_price)}</td>
                                </tr>
                                <tr>
                                    <td>预测价格区间 (90%置信度)</td>
                                    <td class="text-end">${formatNumber(data.percentile_5)} - ${formatNumber(data.percentile_95)}</td>
                                </tr>
                            </table>
                        </div>
                    </div>
                `;
                statsDiv.style.display = 'block';
                
                // 显示视图模式切换按钮
                document.getElementById('viewModeToggle').style.display = 'flex';
                
                // 触发更新图表
                const simulateEvent = new Event('monte-carlo-ready');
                document.dispatchEvent(simulateEvent);
            })
            .catch(error => {
                console.error('模拟失败:', error);
                alert(`蒙特卡洛模拟失败: ${error.message}`);
            });
    }
    
    function loadAllData(ticker) {
        loadFundamentalData(ticker);
        loadBalanceSheet(ticker);
        loadIncomeStatement(ticker);
    }
    
    // 初始加载
    loadAllData(stockSelector.value);
    
    // 股票选择变化时重新加载数据
    stockSelector.addEventListener('change', function() {
        loadAllData(this.value);
        // 同步更新创建订单表单中的股票代码
        document.getElementById('ticker').value = this.value;
    });
    
    // 处理市价单和限价单切换
    document.getElementById('order_execution_type').addEventListener('change', function() {
        const priceField = document.querySelector('.price-field');
        if (this.value === 'market') {
            priceField.style.display = 'none';
            document.getElementById('price').removeAttribute('required');
        } else {
            priceField.style.display = 'block';
            document.getElementById('price').setAttribute('required', '');
        }
    });
    
    // 初始化页面时，设置订单表单中的股票代码为当前选中的股票
    document.getElementById('ticker').value = stockSelector.value;
    
    // 蒙特卡洛模拟相关
    const simulateButton = document.getElementById('simulateButton');
    if (simulateButton) {
        simulateButton.addEventListener('click', function() {
            loadMonteCarloSimulation(stockSelector.value);
        });
    }
    
    // 监听模式切换按钮
    const historyModeBtn = document.getElementById('historyModeBtn');
    const simulationModeBtn = document.getElementById('simulationModeBtn');
    
    if (historyModeBtn && simulationModeBtn) {
        historyModeBtn.addEventListener('click', function() {
            if (window.updateChartViewMode) {
                window.updateChartViewMode('history');
                
                historyModeBtn.classList.add('active');
                simulationModeBtn.classList.remove('active');
            }
        });
        
        simulationModeBtn.addEventListener('click', function() {
            if (window.updateChartViewMode) {
                window.updateChartViewMode('simulation');
                
                simulationModeBtn.classList.add('active');
                historyModeBtn.classList.remove('active');
            }
        });
    }
}); 