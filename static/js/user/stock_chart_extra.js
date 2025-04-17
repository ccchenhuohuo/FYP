document.addEventListener('DOMContentLoaded', function() {
    // Tab switching functionality
    const tabs = document.querySelectorAll('.tab-button');
    const contents = document.querySelectorAll('.tab-content');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove all active states
            tabs.forEach(t => t.classList.remove('active'));
            contents.forEach(c => c.classList.remove('active'));
            
            // Add current active state
            tab.classList.add('active');
            const target = tab.id.replace('tab', 'content');
            document.getElementById(target).classList.add('active');
        });
    });
    
    // Load fundamental data
    const stockSelector = document.getElementById('stockSelector');
    
    function formatNumber(num) {
        if (num === null || num === undefined) return '-';
        
        // For large values, convert to appropriate units (million or billion)
        if (Math.abs(num) >= 1e9) {
            return (num / 1e9).toFixed(2) + ' B'; // Billion
        } else if (Math.abs(num) >= 1e6) {
            return (num / 1e6).toFixed(2) + ' M'; // Million
        } else {
            // Format with commas for thousands separator
            return num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
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
    
    function formatDate(dateString) {
        if (!dateString) return '-';
        try {
            const date = new Date(dateString);
            if (isNaN(date.getTime())) return '-'; // Check for invalid date
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            return `${year}-${month}-${day}`;
        } catch (e) {
            console.error("Error formatting date:", dateString, e);
            return '-';
        }
    }
    
    function loadFundamentalData(ticker) {
        document.getElementById('loadingFundamental').style.display = 'block';
        document.getElementById('fundamentalData').style.display = 'none';
        document.getElementById('errorFundamental').style.display = 'none';
        
        fetch(`${window.location.origin}/user/api/fundamental_data?ticker=${ticker}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP status code: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                // Fill data
                document.getElementById('marketCap').textContent = formatNumber(data.market_cap);
                document.getElementById('peRatio').textContent = formatRatio(data.pe_ratio);
                document.getElementById('pbRatio').textContent = formatRatio(data.pb_ratio);
                document.getElementById('dividendYield').textContent = formatPercentage(data.dividend_yield);
                document.getElementById('revenue').textContent = formatNumber(data.revenue);
                document.getElementById('netIncome').textContent = formatNumber(data.net_income);
                document.getElementById('operatingCashFlow').textContent = formatNumber(data.operating_cash_flow);
                
                document.getElementById('fundamentalDate').textContent = `Data as of: ${formatDate(data.date)}`;
                document.getElementById('fundamentalData').style.display = 'grid';
            })
            .catch(error => {
                console.error('Error loading fundamental data:', error);
                document.getElementById('errorFundamental').querySelector('span').textContent = `Failed to load fundamental data: ${error.message}`;
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
                    throw new Error(`HTTP status code: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Balance sheet data:', data); // Debug output
                
                try {
                    // Safely set element content - add element existence check
                    const safeSetText = (id, value) => {
                        const element = document.getElementById(id);
                        if (element) {
                            element.textContent = formatNumber(value);
                        } else {
                            console.warn(`Element #${id} not found`);
                        }
                    };
                    
                    // Fill data - use safe method
                    safeSetText('currentAssets', data.current_assets);
                    safeSetText('nonCurrentAssets', data.non_current_assets);
                    safeSetText('totalAssets', data.total_assets);
                    safeSetText('currentLiabilities', data.current_liabilities);
                    safeSetText('nonCurrentLiabilities', data.non_current_liabilities);
                    safeSetText('totalLiabilities', data.total_liabilities);
                    
                    // Use the correct ID that exists in the HTML
                    safeSetText('equity', data.total_equity);
                    
                    const dateElement = document.getElementById('balanceDate');
                    if (dateElement) {
                        dateElement.textContent = `Data as of: ${formatDate(data.date)}`;
                    }
                    
                    const balanceDataElement = document.getElementById('balanceData');
                    if (balanceDataElement) {
                        balanceDataElement.style.display = 'block'; // Changed to display: block (or grid)
                    }
                } catch (err) {
                    console.error('Error processing balance sheet data:', err);
                    throw new Error(`Error processing data: ${err.message}`);
                }
            })
            .catch(error => {
                console.error('Error loading balance sheet data:', error);
                const errorElement = document.getElementById('errorBalance');
                if (errorElement && errorElement.querySelector('span')) {
                    errorElement.querySelector('span').textContent = `Failed to load balance sheet data: ${error.message}`;
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
                    throw new Error(`HTTP status code: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                // Fill data
                document.getElementById('incomeRevenue').textContent = formatNumber(data.revenue);
                document.getElementById('costOfRevenue').textContent = formatNumber(data.cost_of_revenue);
                document.getElementById('grossProfit').textContent = formatNumber(data.gross_profit);
                document.getElementById('operatingIncome').textContent = formatNumber(data.operating_income);
                document.getElementById('incomeBeforeTax').textContent = formatNumber(data.income_before_tax);
                document.getElementById('incomeNetIncome').textContent = formatNumber(data.net_income);
                
                // Calculate profit margin
                const profitMargin = data.revenue ? (data.net_income / data.revenue * 100) : null;
                document.getElementById('profitMargin').textContent = formatPercentage(profitMargin);
                
                document.getElementById('incomeDate').textContent = `Data as of: ${formatDate(data.date)}`;
                document.getElementById('incomeData').style.display = 'block'; // Changed to display: block (or grid)
            })
            .catch(error => {
                console.error('Error loading income statement data:', error);
                document.getElementById('errorIncome').querySelector('span').textContent = `Failed to load income statement data: ${error.message}`;
                document.getElementById('errorIncome').style.display = 'block';
            })
            .finally(() => {
                document.getElementById('loadingIncome').style.display = 'none';
            });
    }
    
    function loadMonteCarloSimulation(ticker) {
        const simulationDays = document.getElementById('simulationDays').value || 60;
        const simulationCount = document.getElementById('simulationCount').value || 200;
        
        // Update URL with query parameters
        const url = `${window.location.origin}/user/api/monte-carlo/${ticker}?days=${simulationDays}&simulations=${simulationCount}`;
        
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP status code: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                
                // Save simulation data to global variable for chart use
                window.monteCarloData = data; // Use the whole data object
                
                // Display simulation statistics
                const statsDiv = document.getElementById('simulationStats');
                statsDiv.innerHTML = `
                    <div class="row">
                        <div class="col-md-6">
                            <h5><i class="fas fa-calculator"></i> Simulation Statistics</h5>
                            <table class="table table-sm table-bordered">
                                <tr>
                                    <td>Current Price</td>
                                    <td class="text-end">${formatNumber(data.current_price)}</td>
                                </tr>
                                <tr>
                                    <td>Simulation Days</td>
                                    <td class="text-end">${simulationDays} days</td>
                                </tr>
                                <tr>
                                    <td>Simulation Count</td>
                                    <td class="text-end">${simulationCount}</td>
                                </tr>
                                <tr>
                                    <td>Predicted Mean Price</td>
                                    <td class="text-end">${formatNumber(data.mean_price)}</td>
                                </tr>
                                <tr>
                                    <td>Predicted Price Range (90% Confidence)</td>
                                    <td class="text-end">${formatNumber(data.percentile_5)} - ${formatNumber(data.percentile_95)}</td>
                                </tr>
                            </table>
                        </div>
                    </div>
                `;
                statsDiv.style.display = 'block';
                
                // Show view mode toggle buttons
                document.getElementById('viewModeToggle').style.display = 'flex';
                
                // Trigger chart update
                const simulateEvent = new Event('monte-carlo-ready');
                document.dispatchEvent(simulateEvent);
            })
            .catch(error => {
                console.error('Simulation failed:', error);
                alert(`Monte Carlo simulation failed: ${error.message}`);
            });
    }
    
    function loadAllData(ticker) {
        loadFundamentalData(ticker);
        loadBalanceSheet(ticker);
        loadIncomeStatement(ticker);
    }
    
    // Initial load
    loadAllData(stockSelector.value);
    
    // Reload data when stock selection changes
    stockSelector.addEventListener('change', function() {
        loadAllData(this.value);
        // Synchronize the stock ticker in the order form
        document.getElementById('ticker').value = this.value;
    });
    
    // Handle market/limit order type switch
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
    
    // Set the stock ticker in the order form on page load
    document.getElementById('ticker').value = stockSelector.value;
    
    // Monte Carlo simulation related
    const simulateButton = document.getElementById('simulateButton');
    if (simulateButton) {
        simulateButton.addEventListener('click', function() {
            loadMonteCarloSimulation(stockSelector.value);
        });
    }
    
    // Listen for mode switch buttons
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