document.addEventListener('DOMContentLoaded', function() {
    
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            if (alert && alert.parentNode) {
                alert.classList.remove('show');
                setTimeout(() => alert.remove(), 150);
            }
        }, 5000);
    });
    
    // Task status quick update via AJAX
    const statusForms = document.querySelectorAll('.status-update-form');
    statusForms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            updateTaskStatus(form);
        });
    });
    
    // Username availability checker
    const usernameField = document.getElementById('id_username');
    if (usernameField) {
        let debounceTimer;
        usernameField.addEventListener('input', function() {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => checkUsernameAvailability(this.value), 500);
        });
    }
    
    // Form validation enhancements
    const forms = document.querySelectorAll('form[data-validate="true"]');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            if (!validateForm(form)) {
                e.preventDefault();
            }
        });
    });
    
    // Dashboard statistics refresh
    const dashboardStats = document.getElementById('dashboard-stats');
    if (dashboardStats) {
        refreshDashboardStats();
        setInterval(refreshDashboardStats, 30000); // Refresh every 30 seconds
    }
});
