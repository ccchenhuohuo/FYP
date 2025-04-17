/**
 * Admin Users Management JavaScript
 * Handles search, sorting, and row click functionality for the user table
 */

/**
 * Search functionality for users table
 * Filters the user table based on ID, username and email
 */
function searchUsers() {
    const input = document.getElementById("userSearchInput");
    const filter = input.value.toUpperCase();
    const table = document.getElementById("userTable");
    if (!table) return; // Exit if table not found
    const rows = table.getElementsByTagName("tr");
    
    for (let i = 1; i < rows.length; i++) { // Start from 1 to skip header row
        let visible = false;
        const cells = rows[i].getElementsByTagName("td");
        
        // Search in relevant columns (ID, Username, Email - indices 0, 1, 2)
        for (let j = 0; j < 3; j++) { 
            if (cells[j]) {
                const text = cells[j].textContent || cells[j].innerText;
                if (text.toUpperCase().indexOf(filter) > -1) {
                    visible = true;
                    break;
                }
            }
        }
        
        rows[i].style.display = visible ? "" : "none";
    }
}

/**
 * Sort table rows by selected column
 * @param {number} columnIndex - The index of the column to sort
 */
function sortTable(columnIndex) {
    const table = document.getElementById("userTable");
    if (!table) return;
    const tbody = table.tBodies[0];
    if (!tbody) return;
    const rows = Array.from(tbody.rows);
    let switching = true;
    let dir = "asc";
    let switchcount = 0;
    let shouldSwitch = false;
    
    // Get current sort direction from header icon
    const header = table.tHead.rows[0].cells[columnIndex];
    const icon = header.querySelector("i");
    
    if (icon.classList.contains("fa-sort-up")) {
        dir = "desc";
        icon.classList.remove("fa-sort-up");
        icon.classList.add("fa-sort-down");
    } else {
        icon.classList.remove("fa-sort-down");
        icon.classList.add("fa-sort-up");
    }
    
    // Reset other headers
    const headers = table.tHead.rows[0].cells;
    for (let i = 0; i < headers.length; i++) {
        if (i !== columnIndex) {
            const otherIcon = headers[i].querySelector("i");
            if (otherIcon && otherIcon.classList.contains('fa-sort')) {
                 otherIcon.classList.remove("fa-sort-up", "fa-sort-down");
                 otherIcon.classList.add("fa-sort");
            }
        }
    }
    
    rows.sort((a, b) => {
        const x = a.cells[columnIndex].innerText.toLowerCase();
        const y = b.cells[columnIndex].innerText.toLowerCase();
        if (dir === "asc") {
            return x.localeCompare(y);
        } else {
            return y.localeCompare(x);
        }
    });
    
    // Re-append rows in sorted order
    rows.forEach(row => tbody.appendChild(row));
}

/**
 * Adds click event listeners to table rows for navigation
 */
function initializeRowClick() {
    const table = document.getElementById("userTable");
    if (!table) return;
    const rows = table.querySelectorAll("tbody tr.clickable-row");
    rows.forEach(row => {
        row.addEventListener('click', function() {
            const href = this.dataset.href;
            if (href) {
                window.location.href = href;
            }
        });
    });
}

// Initialize functions when the DOM is fully loaded
document.addEventListener("DOMContentLoaded", function() {
    // Initial sort by username (column 1) in ascending order
    const userNameHeader = document.querySelector(".user-table th:nth-child(2)");
    if (userNameHeader) {
        const icon = userNameHeader.querySelector("i");
        if (icon) {
            icon.classList.remove("fa-sort");
            icon.classList.add("fa-sort-up");
            sortTable(1); // Sort by username initially
        }
    }

    // Add click listeners to rows
    initializeRowClick();
}); 