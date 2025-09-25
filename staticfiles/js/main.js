document.addEventListener('DOMContentLoaded', function() {
    
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            if (alert && alert.parentNode) {
                alert.classList.remove('show');
                setTimeout(() => alert.remove(), 150);
            }
        }, 5000);
    });
    
    const statusForms = document.querySelectorAll('.status-update-form');
    statusForms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            updateTaskStatus(form);
        });
    });
    
    const usernameField = document.getElementById('id_username');
    if (usernameField) {
        let debounceTimer;
        usernameField.addEventListener('input', function() {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => checkUsernameAvailability(this.value), 500);
        });
    }
    
    const forms = document.querySelectorAll('form[data-validate="true"]');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            if (!validateForm(form)) {
                e.preventDefault();
            }
        });
    });
    
    const dashboardStats = document.getElementById('dashboard-stats');
    if (dashboardStats) {
        refreshDashboardStats();
        setInterval(refreshDashboardStats, 30000);
    }
});

function updateTaskStatus(form) {
    const formData = new FormData(form);
    const submitBtn = form.querySelector('button[type="submit"]');
    
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
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    });
}

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

function validateForm(form) {
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');
    
    requiredFields.forEach(function(field) {
        if (!field.value.trim()) {
            showFieldError(field, 'This field is required');
            isValid = false;
        } else {
            clearFieldError(field);
        }
    });
    
    return isValid;
}

function showFieldError(field, message) {
    clearFieldError(field);
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback d-block';
    errorDiv.textContent = message;
    field.parentNode.appendChild(errorDiv);
    field.classList.add('is-invalid');
}

// Clear field error
function clearFieldError(field) {
    const existingError = field.parentNode.querySelector('.invalid-feedback');
    if (existingError) {
        existingError.remove();
    }
    field.classList.remove('is-invalid');
}

function refreshDashboardStats() {
    fetch('/tasks/api/stats/')
    .then(response => response.json())
    .then(data => {
        updateStatsDisplay(data);
    })
    .catch(error => {
        console.error('Error refreshing stats:', error);
    });
}

function updateStatsDisplay(data) {
    const stats = data.status_stats;
    
    const statElements = {
        'total-tasks': stats.total,
        'pending-tasks': stats.pending,
        'in-progress-tasks': stats.in_progress,
        'completed-tasks': stats.completed,
        'overdue-tasks': stats.overdue
    };
    
    Object.entries(statElements).forEach(([elementId, value]) => {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
        }
    });
}

function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        <i class="bi bi-${type === 'success' ? 'check-circle' : 'info-circle'}"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.messages-container') || 
                    document.querySelector('main');
    
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.classList.remove('show');
                setTimeout(() => alertDiv.remove(), 150);
            }
        }, 5000);
    }
}
