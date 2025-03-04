document.addEventListener('DOMContentLoaded', function() {
    const navToggle = document.getElementById('navToggle');
    const navMenu = document.getElementById('navMenu');
    
    // 移动端菜单切换
    if (navToggle && navMenu) {
        navToggle.addEventListener('click', function() {
            navMenu.classList.toggle('active');
            
            // 更新无障碍属性
            const expanded = navMenu.classList.contains('active');
            navToggle.setAttribute('aria-expanded', expanded);
            
            // 动画图标变换
            if (expanded) {
                navToggle.innerHTML = '<i class="fas fa-times"></i>';
            } else {
                navToggle.innerHTML = '<i class="fas fa-bars"></i>';
            }
        });
        
        // 点击页面其他地方关闭菜单
        document.addEventListener('click', function(event) {
            if (!navToggle.contains(event.target) && !navMenu.contains(event.target) && navMenu.classList.contains('active')) {
                navMenu.classList.remove('active');
                navToggle.innerHTML = '<i class="fas fa-bars"></i>';
                navToggle.setAttribute('aria-expanded', false);
            }
        });
    }
    
    // 高亮当前页面菜单项
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('nav a');
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
}); 