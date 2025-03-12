/**
 * 管理员提现管理页面脚本
 */
document.addEventListener('DOMContentLoaded', function() {
    // 为所有拒绝按钮添加点击事件
    document.querySelectorAll('.reject-btn').forEach(function(button) {
        button.addEventListener('click', function() {
            const withdrawalId = this.getAttribute('data-id');
            openRejectModal(withdrawalId);
        });
    });
});

/**
 * 打开拒绝提现模态框
 * @param {string} withdrawalId - 提现记录ID
 */
function openRejectModal(withdrawalId) {
    const modal = document.getElementById('rejectModal');
    const form = document.getElementById('rejectForm');
    form.action = "/admin/withdrawals/" + withdrawalId + "/reject";
    modal.style.display = 'block';
}

/**
 * 关闭拒绝提现模态框
 */
function closeRejectModal() {
    const modal = document.getElementById('rejectModal');
    modal.style.display = 'none';
}

// 点击模态框外部关闭
window.onclick = function(event) {
    const modal = document.getElementById('rejectModal');
    if (event.target == modal) {
        closeRejectModal();
    }
} 