/**
 * Main JavaScript file for PDF Q&A application
 */

// Helper function to format dates
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

// Helper function to show notifications
function showNotification(message, type = 'info') {
    // Create alert element
    const alertElement = document.createElement('div');
    alertElement.className = `alert alert-${type} alert-dismissible fade show`;
    alertElement.setAttribute('role', 'alert');
    
    alertElement.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Find container for alerts
    const container = document.querySelector('.container');
    
    // Insert at the top of the container
    container.insertBefore(alertElement, container.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alertElement && alertElement.parentNode) {
            const bsAlert = new bootstrap.Alert(alertElement);
            bsAlert.close();
        }
    }, 5000);
}

// Helper function to handle errors
function handleError(error, message = 'An error occurred') {
    console.error('Error:', error);
    showNotification(`${message}: ${error.message || 'Unknown error'}`, 'danger');
}

// Initialize Bootstrap tooltips
document.addEventListener('DOMContentLoaded', function() {
    // Initialize any Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Add any global event listeners here
    document.querySelectorAll('a').forEach(link => {
        // Prevent navigation on disabled links
        if (link.classList.contains('disabled')) {
            link.addEventListener('click', function(e) {
                e.preventDefault();
            });
        }
    });
});
