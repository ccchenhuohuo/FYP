/**
 * Admin Layout JavaScript
 * Handles sidebar toggling and active navigation link highlighting.
 */
document.addEventListener('DOMContentLoaded', function() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const adminLayout = document.querySelector('.admin-layout');
    
    if (sidebarToggle && adminLayout) {
        sidebarToggle.addEventListener('click', function() {
            adminLayout.classList.toggle('sidebar-collapsed');
        });
    }
    
    // Check current page link and add active state
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.sidebar-nav a');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.parentElement.classList.add('active');
            
            // If it's a sub-menu item, also activate the parent
            const parentLi = link.closest('ul').closest('li');
            if (parentLi && parentLi.classList.contains('has-submenu')) {
                parentLi.classList.add('active');
            }
        }
    });
}); 