/**
 * Admin Deposit Management Page Script
 */
document.addEventListener('DOMContentLoaded', function() {
    // Add click event listeners to all reject buttons
    document.querySelectorAll('.reject-btn').forEach(function(button) {
        button.addEventListener('click', function() {
            const depositId = this.getAttribute('data-id');
            openRejectModal(depositId);
        });
    });
});

/**
 * Open the reject deposit modal
 * @param {string} depositId - The deposit record ID
 */
function openRejectModal(depositId) {
    const modal = document.getElementById('rejectModal');
    const form = document.getElementById('rejectForm');
    form.action = "/admin/deposits/" + depositId + "/reject";
    modal.style.display = 'block';
}

/**
 * Close the reject deposit modal
 */
function closeRejectModal() {
    const modal = document.getElementById('rejectModal');
    modal.style.display = 'none';
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('rejectModal');
    if (event.target == modal) {
        closeRejectModal();
    }
} 