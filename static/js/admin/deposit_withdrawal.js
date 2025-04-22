/**
 * JavaScript for Admin Deposit/Withdrawal Management Page
 */
document.addEventListener('DOMContentLoaded', () => {
    const rejectModal = document.getElementById('rejectModal');
    const rejectForm = document.getElementById('rejectForm');

    // Ensure modal elements exist before proceeding
    if (!rejectModal || !rejectForm) {
        console.error('Reject modal elements not found!');
        return;
    }

    // Function to open the reject modal
    window.openRejectModal = function(transactionId) {
        console.log("Opening reject modal for transaction ID:", transactionId);
        const urlTemplate = rejectForm.dataset.urlTemplate;
        if (!urlTemplate) {
            console.error('Reject form URL template not found!');
            return;
        }
        rejectForm.action = urlTemplate.replace('/0/', '/' + transactionId + '/');
        console.log("Form action set to:", rejectForm.action);
        rejectModal.style.display = 'block'; 
        // Optional: Add class for transition effects if using CSS transitions
        // rejectModal.classList.add('show'); 
        const reasonInput = rejectForm.elements['reject_reason'];
        if (reasonInput) {
            reasonInput.focus();
        }
    }

    // Function to close the reject modal
    window.closeRejectModal = function() {
        console.log("Closing reject modal");
        // Optional: Remove class for transition effects
        // rejectModal.classList.remove('show');
        rejectModal.style.display = 'none';
        rejectForm.reset();
    }

    // Attach event listener to close button within the modal
    const closeButton = rejectModal.querySelector('.close-button');
    if (closeButton) {
        closeButton.addEventListener('click', closeRejectModal);
    }

    // Attach event listener to cancel button within the modal form
    const cancelButton = rejectModal.querySelector('.btn-secondary');
    if (cancelButton) {
        cancelButton.addEventListener('click', closeRejectModal);
    }

    // Close modal if clicking outside the modal content
    window.addEventListener('click', (event) => {
        if (event.target === rejectModal) {
            closeRejectModal();
        }
    });

    // === Add listener for the form submission ===
    if (rejectForm) {
        rejectForm.addEventListener('submit', (event) => {
            console.log("Reject form submit event triggered.");
            const reason = rejectForm.elements['reject_reason'].value.trim();
            console.log("Reason entered:", reason);
            
            // Optional: You could uncomment the next line to see if preventing default helps,
            // but ideally the native submission should work.
            // event.preventDefault(); 
            
            if (!reason) {
                console.log("Reason is empty, browser validation should prevent submission unless bypassed.");
                // We rely on the 'required' attribute for validation here.
            } else {
                console.log("Form seems valid, allowing native submission...");
            }
        });
    }
    // === End of added listener ===

    // --- Tab Switching Logic (copied from inline script) --- 
    // Function to show top-level tab
    window.showTopTab = function(tabGroupId) {
        document.querySelectorAll('.top-tab-content').forEach(content => content.classList.remove('active'));
        document.querySelectorAll('.top-tab-button').forEach(button => button.classList.remove('active'));

        const contentToShow = document.getElementById(tabGroupId + '-content');
        const buttonToActivate = document.querySelector(`.top-tab-button[data-tab-group='${tabGroupId}']`);
        
        if (contentToShow) contentToShow.classList.add('active');
        if (buttonToActivate) buttonToActivate.classList.add('active');
        
        // Activate the default sub-tab (pending) for the new top-level tab
        showSubTab(tabGroupId, 'pending'); 
    }

    // Function to show sub-tab within a specific top-level group
    window.showSubTab = function(tabGroupId, subTabId) {
        const subTabContents = document.querySelectorAll(`#${tabGroupId}-content .tab-content`);
        const subTabButtons = document.querySelectorAll(`#${tabGroupId}-content .tab-button`);

        subTabContents.forEach(tab => tab.classList.remove('active'));
        subTabButtons.forEach(button => button.classList.remove('active'));

        const subContentToShow = document.getElementById(`${tabGroupId}-${subTabId}-tab`);
        const subButtonToActivate = document.querySelector(`#${tabGroupId}-content .tab-button[onclick*="showSubTab('${tabGroupId}', '${subTabId}')"]`);
        
        if (subContentToShow) subContentToShow.classList.add('active');
        if (subButtonToActivate) subButtonToActivate.classList.add('active');
    }

    // Add event listeners for top-level tabs
    document.querySelectorAll('.top-tab-button').forEach(button => {
        button.addEventListener('click', function() {
            showTopTab(this.dataset.tabGroup);
        });
    });

    // Ensure the correct tab is shown on initial load (copied from inline script)
    const urlParams = new URLSearchParams(window.location.search);
    const initialTab = urlParams.get('tab') || 'deposits'; // Default to 'deposits'
    const validTabs = ['deposits', 'withdrawals'];
    const tabToShow = validTabs.includes(initialTab) ? initialTab : 'deposits';
    showTopTab(tabToShow);
}); 