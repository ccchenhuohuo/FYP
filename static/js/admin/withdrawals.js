/**
 * Admin Withdrawal Management Page Script
 */
document.addEventListener('DOMContentLoaded', function() {
    // Add click event listeners to all reject buttons
    document.querySelectorAll('.reject-btn').forEach(function(button) {
        button.addEventListener('click', function() {
            const withdrawalId = this.getAttribute('data-id');
            openRejectModal(withdrawalId);
        });
    });
});

/**
 * Open the reject withdrawal modal
 * @param {string} withdrawalId - The withdrawal record ID
 */
function openRejectModal(withdrawalId) {
    const modal = document.getElementById('rejectModal');
    const form = document.getElementById('rejectForm');
    form.action = "/admin/withdrawals/" + withdrawalId + "/reject";
    modal.style.display = 'block';
}

/**
 * Close the reject withdrawal modal
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