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
                if (data.status === 'success') {
                    // 填充数据
                    document.getElementById('marketCap').textContent = formatNumber(data.data.market_cap);
                    document.getElementById('peRatio').textContent = formatRatio(data.data.pe_ratio);
                    document.getElementById('pbRatio').textContent = formatRatio(data.data.pb_ratio);
                    document.getElementById('dividendYield').textContent = formatPercentage(data.data.dividend_yield);
                    document.getElementById('revenue').textContent = formatNumber(data.data.revenue);
                    document.getElementById('netIncome').textContent = formatNumber(data.data.net_income);
                    document.getElementById('operatingCashFlow').textContent = formatNumber(data.data.operating_cash_flow);
                    
                    document.getElementById('fundamentalDate').textContent = `数据更新日期: ${data.data.date}`;
                    
                    document.getElementById('fundamentalData').style.display = 'grid';
                } else {
                    document.getElementById('errorFundamental').querySelector('span').textContent = data.message || '加载基本面数据失败';
                    document.getElementById('errorFundamental').style.display = 'block';
                }
            })
            .catch(error => {
                console.error('加载基本面数据错误:', error);
                document.getElementById('errorFundamental').querySelector('span').textContent = `请求基本面数据时发生错误: ${error.message}`;
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
                if (data.status === 'success') {
                    // 填充数据
                    document.getElementById('currentAssets').textContent = formatNumber(data.data.current_assets);
                    document.getElementById('nonCurrentAssets').textContent = formatNumber(data.data.non_current_assets);
                    document.getElementById('totalAssets').textContent = formatNumber(data.data.total_assets);
                    document.getElementById('currentLiabilities').textContent = formatNumber(data.data.current_liabilities);
                    document.getElementById('nonCurrentLiabilities').textContent = formatNumber(data.data.non_current_liabilities);
                    document.getElementById('totalLiabilities').textContent = formatNumber(data.data.total_liabilities);
                    document.getElementById('equity').textContent = formatNumber(data.data.equity);
                    
                    document.getElementById('balanceDate').textContent = `数据更新日期: ${data.data.date}`;
                    
                    document.getElementById('balanceData').style.display = 'block';
                } else {
                    document.getElementById('errorBalance').querySelector('span').textContent = data.message || '加载资产负债表数据失败';
                    document.getElementById('errorBalance').style.display = 'block';
                }
            })
            .catch(error => {
                console.error('加载资产负债表数据错误:', error);
                document.getElementById('errorBalance').querySelector('span').textContent = `请求资产负债表数据时发生错误: ${error.message}`;
                document.getElementById('errorBalance').style.display = 'block';
            })
            .finally(() => {
                document.getElementById('loadingBalance').style.display = 'none';
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
                if (data.status === 'success') {
                    // 填充数据
                    document.getElementById('incomeRevenue').textContent = formatNumber(data.data.revenue);
                    document.getElementById('costOfRevenue').textContent = formatNumber(data.data.cost_of_revenue);
                    document.getElementById('grossProfit').textContent = formatNumber(data.data.gross_profit);
                    document.getElementById('operatingIncome').textContent = formatNumber(data.data.operating_income);
                    document.getElementById('incomeBeforeTax').textContent = formatNumber(data.data.income_before_tax);
                    document.getElementById('incomeNetIncome').textContent = formatNumber(data.data.net_income);
                    document.getElementById('profitMargin').textContent = formatPercentage(data.data.profit_margin);
                    
                    document.getElementById('incomeDate').textContent = `数据更新日期: ${data.data.date}`;
                    
                    document.getElementById('incomeData').style.display = 'block';
                } else {
                    document.getElementById('errorIncome').querySelector('span').textContent = data.message || '加载利润表数据失败';
                    document.getElementById('errorIncome').style.display = 'block';
                }
            })
            .catch(error => {
                console.error('加载利润表数据错误:', error);
                document.getElementById('errorIncome').querySelector('span').textContent = `请求利润表数据时发生错误: ${error.message}`;
                document.getElementById('errorIncome').style.display = 'block';
            })
            .finally(() => {
                document.getElementById('loadingIncome').style.display = 'none';
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
}); 