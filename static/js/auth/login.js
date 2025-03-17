document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            // 表单提交前的验证
            const username = document.getElementById('user_name').value.trim();
            const password = document.getElementById('user_password').value.trim();
            
            if (!username || !password) {
                e.preventDefault(); // 阻止表单提交
                alert('请填写用户名和密码');
                return false;
            }
            
            // 如果验证通过，表单正常提交
            return true;
        });
    }
}); 