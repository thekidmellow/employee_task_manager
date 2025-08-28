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

// AJAX task status update function
function updateTaskStatus(form) {
    const formData = new FormData(form);
    const submitBtn = form.querySelector('button[type="submit"]');
    
    // Show loading state
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="spinner-border spinner-border-sm"></i> Updating...';
    submitBtn.disabled = true;
    
    fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update UI with new status
            const statusBadge = form.closest('.task-card').querySelector('.status-badge');
            if (statusBadge) {
                statusBadge.textContent = data.status_display;
                statusBadge.className = `badge bg-${data.status_color} status-badge`;
            }
            showNotification('Task status updated successfully!', 'success');
        } else {
            showNotification(data.error || 'Error updating task status', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Network error occurred', 'error');
    })
    .finally(() => {
        // Restore button state
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    });
}

// Username availability checker
function checkUsernameAvailability(username) {
    if (username.length < 3) return;
    
    const indicator = document.getElementById('username-availability');
    if (!indicator) return;
    
    fetch(`/accounts/api/check-username/?username=${encodeURIComponent(username)}`)
    .then(response => response.json())
    .then(data => {
        indicator.innerHTML = `
            <small class="text-${data.available ? 'success' : 'danger'}">
                <i class="bi bi-${data.available ? 'check-circle' : 'x-circle'}"></i>
                ${data.message}
            </small>
        `;
    })
    .catch(error => {
        console.error('Error checking username:', error);
    });
}
