document.addEventListener('DOMContentLoaded', function() {
    // Order form validation
    const orderForm = document.getElementById('orderForm');
    if (orderForm) {
        orderForm.addEventListener('submit', function(e) {
            const price = parseFloat(document.getElementById('price').value);
            const quantity = parseFloat(document.getElementById('quantity').value);
            
            if (isNaN(price) || price <= 0 || isNaN(quantity) || quantity <= 0) {
                e.preventDefault();
                alert('Please enter a valid price and quantity');
            }
        });
    }
    
    // Deposit form validation and submission
    const depositForm = document.getElementById('depositForm');
    if (depositForm) {
        depositForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const amount = parseFloat(document.getElementById('amount').value);
            
            // Client-side validation: amount must be greater than 0
            if (isNaN(amount) || amount <= 0) {
                alert('Deposit amount must be greater than 0');
                return;
            }
            
            try {
                const response = await fetch('/user/api/deposit', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ amount: amount })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    alert('Deposit request submitted, pending administrator approval');
                    location.reload();  // Reload page to show latest status
                } else {
                    alert(data.error || 'Failed to submit deposit request');
                }
            } catch (error) {
                alert('An error occurred while submitting the deposit request');
                console.error('Error:', error);
            }
            
            // Close modal
            const depositModalElement = document.getElementById('depositModal');
            if (depositModalElement) {
                const modal = bootstrap.Modal.getInstance(depositModalElement);
                if (modal) {
                    modal.hide();
                }
            }
        });
    }
    
    // Withdrawal form validation
    const withdrawalForm = document.getElementById('withdrawalForm');
    if (withdrawalForm) {
        withdrawalForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const amount = parseFloat(document.getElementById('withdrawAmount').value);
            const availableBalanceElement = document.getElementById('availableBalance');
            const availableBalance = parseFloat(availableBalanceElement?.dataset?.balance || 0);
            
            // Client-side validation: amount must be greater than 0
            if (isNaN(amount) || amount <= 0) {
                alert('Withdrawal amount must be greater than 0');
                return;
            }
            
            // Client-side validation: withdrawal amount cannot exceed available balance
            if (amount > availableBalance) {
                alert(`Withdrawal amount cannot exceed available balance: ¥${availableBalance.toFixed(2)}`);
                return;
            }
            
            try {
                const response = await fetch('/user/api/withdraw', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ amount: amount })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    alert('Withdrawal request submitted, pending administrator approval');
                    location.reload();  // Reload page to show latest status
                } else {
                    alert(data.error || 'Failed to submit withdrawal request');
                }
            } catch (error) {
                alert('An error occurred while submitting the withdrawal request');
                console.error('Error:', error);
            }
            
            // Close modal
            const withdrawalModalElement = document.getElementById('withdrawalModal');
            if (withdrawalModalElement) {
                const modal = bootstrap.Modal.getInstance(withdrawalModalElement);
                if (modal) {
                    modal.hide();
                }
            }
        });
    }
    
    // Handle cancel order button click events
    const cancelOrderForms = document.querySelectorAll('form[action*="/orders/"][action*="/cancel"]');
    cancelOrderForms.forEach(form => {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            if (!confirm('Are you sure you want to cancel this order?')) {
                return; // Stop if user cancels
            }

            try {
                const response = await fetch(form.action, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                if (response.ok) {
                    alert('Order successfully cancelled');
                    location.reload(); // Reload page to show latest status
                } else {
                    const errorData = await response.json();
                    alert(errorData.error || 'Failed to cancel order');
                }
            } catch (error) {
                alert('An error occurred while cancelling the order');
                console.error('Error:', error);
            }
        });
    });
    
    // Handle Toggle History Button Clicks
    const toggleButtons = document.querySelectorAll('.toggle-history-btn');

    toggleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetListId = this.getAttribute('data-target');
            const targetBody = document.getElementById(targetListId);

            if (targetBody) {
                // Find hidden items within this specific table body
                const hiddenItems = targetBody.querySelectorAll('tr.history-item.hidden');
                const isShowingAll = hiddenItems.length === 0; // Check if currently showing all (no hidden items)

                if (isShowingAll) {
                    // Hide items beyond the initial limit (3 or 4)
                    const allItems = targetBody.querySelectorAll('tr.history-item');
                    const limit = targetListId.includes('fund') ? 4 : 3; // 4 for fund, 3 for transaction
                    allItems.forEach((item, index) => {
                        if (index >= limit) {
                            item.classList.add('hidden');
                        }
                    });
                    this.textContent = 'Show All';
                } else {
                    // Show all hidden items
                    hiddenItems.forEach(item => {
                        item.classList.remove('hidden');
                    });
                    this.textContent = 'Show Less';
                }
            }
        });
    });
    
    // Highlight current navigation menu item (moved to navigation.js potentially)
    // const currentPath = window.location.pathname;
    // const navLinks = document.querySelectorAll('nav a');
    // navLinks.forEach(link => {
    //     if (link.getAttribute('href') === currentPath) {
    //         link.classList.add('active');
    //     }
    // });
});