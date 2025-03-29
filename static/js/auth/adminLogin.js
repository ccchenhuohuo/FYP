document.addEventListener('DOMContentLoaded', function() {
    const adminLoginForm = document.getElementById('adminLoginForm');
    
    // 处理账户锁定倒计时
    const lockCountdownElement = document.getElementById('lockCountdown');
    if (lockCountdownElement) {
        const lockedUntilElement = document.querySelector('.account-locked-info');
        if (lockedUntilElement) {
            const lockedUntilStr = lockedUntilElement.getAttribute('data-locked-until');
            if (lockedUntilStr) {
                const lockedUntil = new Date(lockedUntilStr);
                
                function updateCountdown() {
                    const now = new Date();
                    const diff = lockedUntil - now;
                    
                    if (diff <= 0) {
                        lockCountdownElement.textContent = "已解锁，请刷新页面";
                        return;
                    }
                    
                    const minutes = Math.floor(diff / 60000);
                    const seconds = Math.floor((diff % 60000) / 1000);
                    lockCountdownElement.textContent = 
                        `${minutes}分${seconds}秒`;
                }
                
                // 初始更新
                updateCountdown();
                // 每秒更新一次
                setInterval(updateCountdown, 1000);
            }
        }
    }
    
    // 显示密码复杂度要求
    const passwordField = document.getElementById('password');
    const passwordRequirements = document.getElementById('passwordRequirements');
    
    if (passwordField && passwordRequirements) {
        // 点击密码输入框时显示密码要求
        passwordField.addEventListener('focus', function() {
            passwordRequirements.style.display = 'block';
        });
        
        // 离开密码输入框时隐藏密码要求
        passwordField.addEventListener('blur', function() {
            setTimeout(() => {
                passwordRequirements.style.display = 'none';
            }, 200);
        });
    }
    
    // 表单提交验证
    if (adminLoginForm) {
        adminLoginForm.addEventListener('submit', function(e) {
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            if (!username || !password) {
                e.preventDefault();
                alert('请填写管理员用户名和密码');
            }
        });
    }
});