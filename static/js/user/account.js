// 初始化表单验证
document.addEventListener('DOMContentLoaded', function() {
    // 创建订单表单验证
    const orderForm = document.getElementById('orderForm');
    if (orderForm) {
        orderForm.addEventListener('submit', function(e) {
            const price = parseFloat(document.getElementById('price').value);
            const quantity = parseFloat(document.getElementById('quantity').value);
            
            if (isNaN(price) || price <= 0 || isNaN(quantity) || quantity <= 0) {
                e.preventDefault();
                alert('请输入有效的价格和数量');
            }
        });
    }
    
    // 充值表单验证和提交
    const depositForm = document.getElementById('depositForm');
    if (depositForm) {
        depositForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const amount = parseFloat(document.getElementById('amount').value);
            
            // 客户端验证：金额必须大于0
            if (isNaN(amount) || amount <= 0) {
                alert('充值金额必须大于0');
                return;
            }
            
            try {
                const response = await fetch('/user/api/deposit', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ amount: amount })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    alert('充值申请已提交，等待管理员审核');
                    location.reload();  // 刷新页面以显示最新状态
                } else {
                    alert(data.error || '充值申请提交失败');
                }
            } catch (error) {
                alert('提交充值申请时发生错误');
                console.error('Error:', error);
            }
            
            // 关闭模态框
            const modal = bootstrap.Modal.getInstance(document.getElementById('depositModal'));
            modal.hide();
        });
    }
    
    // 提现表单验证
    const withdrawalForm = document.getElementById('withdrawalForm');
    if (withdrawalForm) {
        withdrawalForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const amount = parseFloat(document.getElementById('withdrawAmount').value);
            const availableBalance = parseFloat(document.getElementById('availableBalance')?.dataset?.balance || 0);
            
            // 客户端验证：金额必须大于0
            if (isNaN(amount) || amount <= 0) {
                alert('提现金额必须大于0');
                return;
            }
            
            // 客户端验证：提现金额不能超过可用余额
            if (amount > availableBalance) {
                alert(`提现金额不能超过可用余额 ${availableBalance}`);
                return;
            }
            
            try {
                const response = await fetch('/user/api/withdraw', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ amount: amount })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    alert('提现申请已提交，等待管理员审核');
                    location.reload();  // 刷新页面以显示最新状态
                } else {
                    alert(data.error || '提现申请提交失败');
                }
            } catch (error) {
                alert('提交提现申请时发生错误');
                console.error('Error:', error);
            }
            
            // 关闭模态框
            const modal = bootstrap.Modal.getInstance(document.getElementById('withdrawalModal'));
            modal.hide();
        });
    }
    
    // 处理取消订单按钮的点击事件
    const cancelOrderForms = document.querySelectorAll('form[action*="/orders/"][action*="/cancel"]');
    cancelOrderForms.forEach(form => {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            try {
                const response = await fetch(form.action, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                if (response.ok) {
                    alert('订单已成功取消');
                    location.reload(); // 刷新页面以显示最新状态
                } else {
                    const errorData = await response.json();
                    alert(errorData.error || '取消订单失败');
                }
            } catch (error) {
                alert('取消订单时发生错误');
                console.error('Error:', error);
            }
        });
    });
    
    // 高亮当前导航菜单项
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('nav a');
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
});