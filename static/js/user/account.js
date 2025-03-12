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
    
    // 充值表单验证
    const depositForm = document.getElementById('depositForm');
    if (depositForm) {
        depositForm.addEventListener('submit', function(e) {
            const amount = parseFloat(document.getElementById('amount').value);
            
            if (isNaN(amount) || amount <= 0) {
                e.preventDefault();
                alert('请输入有效的充值金额');
                return;
            }
            
            if (!confirm(`您确定要充值 ¥${amount.toFixed(2)} 吗？`)) {
                e.preventDefault();
            }
        });
    }
    
    // 提现表单验证
    const withdrawalForm = document.getElementById('withdrawalForm');
    if (withdrawalForm) {
        withdrawalForm.addEventListener('submit', function(e) {
            const amount = parseFloat(document.getElementById('withdrawAmount').value);
            const balance = parseFloat(document.querySelector('.current-balance').textContent.replace('¥', '').trim());
            
            if (isNaN(amount) || amount <= 0) {
                e.preventDefault();
                alert('请输入有效的提现金额');
                return;
            }
            
            if (amount > balance) {
                e.preventDefault();
                alert('提现金额不能超过可用余额');
                return;
            }
            
            if (!confirm(`您确定要提现 ¥${amount.toFixed(2)} 吗？`)) {
                e.preventDefault();
            }
        });
    }
    
    // 高亮当前导航菜单项
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('nav a');
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
}); 