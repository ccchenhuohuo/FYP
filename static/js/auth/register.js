document.addEventListener('DOMContentLoaded', function() {
    const registerForm = document.getElementById('registerForm');
    
    if (registerForm) {
        // 清除表单中可能的错误状态
        clearErrors();
        
        registerForm.addEventListener('submit', function(e) {
            // 清除之前的错误提示
            clearErrors();
            
            const userName = document.getElementById('user_name').value.trim();
            const userEmail = document.getElementById('user_email').value.trim();
            const userPassword = document.getElementById('user_password').value;
            const confirmPassword = document.getElementById('confirm_password').value;
            
            let isValid = true;
            
            // 验证用户名
            if (!userName) {
                isValid = false;
                showError('user_name', '请输入用户名');
            }
            
            // 验证邮箱
            if (!userEmail) {
                isValid = false;
                showError('user_email', '请输入邮箱');
            } else {
                // 验证邮箱格式
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailRegex.test(userEmail)) {
                    isValid = false;
                    showError('user_email', '请输入有效的邮箱地址');
                }
            }
            
            // 验证密码
            if (!userPassword) {
                isValid = false;
                showError('user_password', '请输入密码');
            }
            
            // 验证确认密码
            if (!confirmPassword) {
                isValid = false;
                showError('confirm_password', '请确认密码');
            } else if (userPassword !== confirmPassword) {
                isValid = false;
                showError('confirm_password', '两次输入的密码不一致');
            }
            
            if (!isValid) {
                e.preventDefault(); // 阻止表单提交
            }
        });
    }
    
    // 辅助函数：显示错误消息
    function showError(inputId, message) {
        const input = document.getElementById(inputId);
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        
        input.parentNode.appendChild(errorDiv);
        input.classList.add('error');
    }
    
    // 辅助函数：清除所有错误
    function clearErrors() {
        // 移除所有错误消息
        const errorMessages = document.querySelectorAll('.error-message');
        errorMessages.forEach(msg => msg.remove());
        
        // 移除所有错误样式
        const errorInputs = document.querySelectorAll('.error');
        errorInputs.forEach(input => input.classList.remove('error'));
    }
}); 