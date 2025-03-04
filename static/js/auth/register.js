document.addEventListener('DOMContentLoaded', function() {
    const registerForm = document.getElementById('registerForm');
    
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            const username = document.getElementById('username').value;
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirm-password').value;
            
            if (!username || !email || !password || !confirmPassword) {
                e.preventDefault();
                alert('请填写所有字段');
                return;
            }
            
            // 验证邮箱格式
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(email)) {
                e.preventDefault();
                alert('请输入有效的邮箱地址');
                return;
            }
            
            if (password !== confirmPassword) {
                e.preventDefault();
                alert('两次输入的密码不一致');
                return;
            }
        });
    }
}); 