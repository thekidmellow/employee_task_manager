/**
 * Employee Task Manager - Main JavaScript Module
 * 
 * This module provides core JavaScript functionality for the Employee Task Manager
 * including AJAX operations, form enhancements, real-time updates, and accessibility features.
 * 
 * @author Employee Task Manager Team
 * @version 2.0.0
 */

(function(window, document) {
    'use strict';

    const TaskManager = {
        config: {
            alertTimeout: 5000,
            debounceDelay: 500,
            animationDuration: 300
        },

        elements: {},

        init: function() {
            this.cacheElements();
            this.bindEvents();
            this.initializeComponents();
            this.enhanceAccessibility();
            
            console.log('Task Manager initialized successfully');
        },

        cacheElements: function() {
            this.elements = {
                alerts: document.querySelectorAll('.alert:not(.alert-permanent)'),
                forms: document.querySelectorAll('form'),
                statusForms: document.querySelectorAll('.status-update-form'),
                usernameField: document.getElementById('id_username'),
                dashboardStats: document.getElementById('dashboard-stats'),
                messagesContainer: document.querySelector('.messages-container')
            };
        },

        bindEvents: function() {
            this.initAlertSystem();

            this.initStatusUpdates();

            this.initUsernameChecker();

            this.initFormValidation();

            this.initDashboardRefresh();

            this.initKeyboardShortcuts();

            window.addEventListener('beforeunload', this.handleBeforeUnload.bind(this));
            window.addEventListener('online', this.handleOnline.bind(this));
            window.addEventListener('offline', this.handleOffline.bind(this));
        },

        initializeComponents: function() {
            this.initTooltips();
            this.initPopovers();
            this.initProgressBars();
            this.initCardAnimations();
        },

        initAlertSystem: function() {
            this.elements.alerts.forEach(alert => {
                setTimeout(() => {
                    if (alert && alert.parentNode) {
                        this.dismissAlert(alert);
                    }
                }, this.config.alertTimeout);
            });
        },

        dismissAlert: function(alert) {
            alert.classList.remove('show');
            setTimeout(() => {
                if (alert.parentNode) {
                    alert.remove();
                }
            }, this.config.animationDuration);
        },

        initStatusUpdates: function() {
            this.elements.statusForms.forEach(form => {
                form.addEventListener('submit', (e) => {
                    e.preventDefault();
                    this.updateTaskStatus(form);
                });
            });
        },

        updateTaskStatus: function(form) {
            const formData = new FormData(form);
            const submitBtn = form.querySelector('button[type="submit"]');
            
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Updating...';
            submitBtn.disabled = true;

            const csrfToken = this.getCSRFToken();
            if (!csrfToken) {
                this.showNotification('Security token missing. Please refresh the page.', 'error');
                this.restoreButton(submitBtn, originalText);
                return;
            }

            fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrfToken
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    this.handleStatusUpdateSuccess(form, data);
                    this.showNotification('Task status updated successfully!', 'success');
                } else {
                    throw new Error(data.message || 'Update failed');
                }
            })
            .catch(error => {
                console.error('Status update error:', error);
                this.showNotification(`Error: ${error.message}`, 'error');
            })
            .finally(() => {
                this.restoreButton(submitBtn, originalText);
            });
        },

        handleStatusUpdateSuccess: function(form, data) {
            const taskCard = form.closest('.task-card');
            if (taskCard && data.status_display && data.status_color) {
                const statusBadge = taskCard.querySelector('.status-badge');
                if (statusBadge) {
                    statusBadge.textContent = data.status_display;
                    statusBadge.className = `badge bg-${data.status_color} status-badge`;
                }

                const progressBar = taskCard.querySelector('.progress-bar');
                if (progressBar && data.progress_percentage !== undefined) {
                    progressBar.style.width = `${data.progress_percentage}%`;
                    progressBar.setAttribute('aria-valuenow', data.progress_percentage);
                }
            }
        },

        initUsernameChecker: function() {
            if (!this.elements.usernameField) return;

            let debounceTimer;
            this.elements.usernameField.addEventListener('input', (e) => {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => {
                    this.checkUsernameAvailability(e.target.value);
                }, this.config.debounceDelay);
            });
        },

        checkUsernameAvailability: function(username) {
            if (username.length < 3) return;

            const indicator = document.getElementById('username-availability');
            if (!indicator) return;

            indicator.innerHTML = '<small class="text-muted">Checking...</small>';

            fetch(`/accounts/api/check-username/?username=${encodeURIComponent(username)}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network error');
                    }
                    return response.json();
                })
                .then(data => {
                    const iconClass = data.available ? 'check-circle' : 'x-circle';
                    const textClass = data.available ? 'success' : 'danger';
                    
                    indicator.innerHTML = `
                        <small class="text-${textClass}">
                            <i class="bi bi-${iconClass}" aria-hidden="true"></i>
                            ${data.message}
                        </small>
                    `;
                })
                .catch(error => {
                    console.error('Username check error:', error);
                    indicator.innerHTML = '<small class="text-warning">Unable to check availability</small>';
                });
        },

        initFormValidation: function() {
            const validationForms = document.querySelectorAll('form[data-validate="true"]');
            
            validationForms.forEach(form => {
                form.addEventListener('submit', (e) => {
                    if (!this.validateForm(form)) {
                        e.preventDefault();
                    }
                });
            });
        },

        validateForm: function(form) {
            let isValid = true;
            const requiredFields = form.querySelectorAll('[required]');

            form.querySelectorAll('.is-invalid').forEach(field => {
                field.classList.remove('is-invalid');
            });
            form.querySelectorAll('.invalid-feedback').forEach(feedback => {
                if (!feedback.hasAttribute('data-server-error')) {
                    feedback.remove();
                }
            });

            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    this.showFieldError(field, 'This field is required');
                    isValid = false;
                }
            });

            const emailFields = form.querySelectorAll('input[type="email"]');
            emailFields.forEach(field => {
                if (field.value && !this.isValidEmail(field.value)) {
                    this.showFieldError(field, 'Please enter a valid email address');
                    isValid = false;
                }
            });

            const passwordFields = form.querySelectorAll('input[type="password"]');
            if (passwordFields.length === 2) {
                const [password1, password2] = passwordFields;
                if (password1.value !== password2.value) {
                    this.showFieldError(password2, 'Passwords do not match');
                    isValid = false;
                }
            }

            return isValid;
        },

        showFieldError: function(field, message) {
            field.classList.add('is-invalid');
            
            let errorElement = field.parentNode.querySelector('.invalid-feedback');
            if (!errorElement) {
                errorElement = document.createElement('div');
                errorElement.className = 'invalid-feedback d-block';
                field.parentNode.appendChild(errorElement);
            }
            
            errorElement.textContent = message;
        },

        initDashboardRefresh: function() {
            if (this.elements.dashboardStats) {
                this.refreshDashboardStats();
                setInterval(() => {
                    this.refreshDashboardStats();
                }, 30000);
            }
        },

        refreshDashboardStats: function() {
            fetch('/tasks/api/stats/')
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network error');
                    }
                    return response.json();
                })
                .then(data => {
                    this.updateStatsDisplay(data);
                })
                .catch(error => {
                    console.error('Dashboard refresh error:', error);
                });
        },

        updateStatsDisplay: function(data) {
            const stats = data.status_stats || {};
            
            const statElements = {
                'total-tasks': stats.total,
                'pending-tasks': stats.pending,
                'in-progress-tasks': stats.in_progress,
                'completed-tasks': stats.completed,
                'overdue-tasks': stats.overdue
            };

            Object.entries(statElements).forEach(([elementId, value]) => {
                const element = document.getElementById(elementId);
                if (element && value !== undefined) {
                    this.animateNumber(element, parseInt(element.textContent) || 0, value);
                }
            });
        },

        animateNumber: function(element, start, end) {
            const duration = 1000;
            const stepTime = 50;
            const steps = duration / stepTime;
            const stepSize = (end - start) / steps;
            let current = start;

            const timer = setInterval(() => {
                current += stepSize;
                element.textContent = Math.round(current);

                if ((stepSize > 0 && current >= end) || (stepSize < 0 && current <= end)) {
                    clearInterval(timer);
                    element.textContent = end;
                }
            }, stepTime);
        },

        initKeyboardShortcuts: function() {
            document.addEventListener('keydown', (e) => {

                if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                    e.preventDefault();
                    const searchField = document.querySelector('input[type="search"], input[name="search"]');
                    if (searchField) {
                        searchField.focus();
                    }
                }

                if (e.key === 'Escape') {
                    const openDropdowns = document.querySelectorAll('.dropdown-menu.show');
                    openDropdowns.forEach(dropdown => {
                        const toggle = dropdown.previousElementSibling;
                        if (toggle && toggle.click) {
                            toggle.click();
                        }
                    });
                }
            });
        },

        initTooltips: function() {
            const tooltipElements = document.querySelectorAll('[data-bs-toggle="tooltip"]');
            if (tooltipElements.length && window.bootstrap) {
                tooltipElements.forEach(element => {
                    new bootstrap.Tooltip(element);
                });
            }
        },

        initPopovers: function() {
            const popoverElements = document.querySelectorAll('[data-bs-toggle="popover"]');
            if (popoverElements.length && window.bootstrap) {
                popoverElements.forEach(element => {
                    new bootstrap.Popover(element);
                });
            }
        },

        initProgressBars: function() {
            const progressBars = document.querySelectorAll('.progress-bar');
            
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const progressBar = entry.target;
                        const targetWidth = progressBar.getAttribute('aria-valuenow') + '%';
                        
                        setTimeout(() => {
                            progressBar.style.width = targetWidth;
                        }, 100);
                    }
                });
            });

            progressBars.forEach(bar => {
                bar.style.width = '0%';
                observer.observe(bar);
            });
        },

        initCardAnimations: function() {
            const cards = document.querySelectorAll('.card');
            
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.style.opacity = '1';
                        entry.target.style.transform = 'translateY(0)';
                    }
                });
            }, { threshold: 0.1 });

            cards.forEach(card => {
                card.style.opacity = '0';
                card.style.transform = 'translateY(20px)';
                card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
                observer.observe(card);
            });
        },

        enhanceAccessibility: function() {

            this.addSkipLinks();

            this.enhanceFormLabels();

            this.addAriaAttributes();

            this.initFocusManagement();
        },

        addSkipLinks: function() {
            const skipLink = document.querySelector('a[href="#main-content"]');
            if (!skipLink) {
                const link = document.createElement('a');
                link.href = '#main-content';
                link.className = 'visually-hidden-focusable';
                link.textContent = 'Skip to main content';
                document.body.insertBefore(link, document.body.firstChild);
            }
        },

        enhanceFormLabels: function() {
            const inputs = document.querySelectorAll('input, select, textarea');
            
            inputs.forEach(input => {
                if (!input.getAttribute('aria-label') && !input.getAttribute('aria-labelledby')) {
                    const label = document.querySelector(`label[for="${input.id}"]`);
                    if (label) {
                        input.setAttribute('aria-labelledby', label.id || `label-${input.id}`);
                        if (!label.id) {
                            label.id = `label-${input.id}`;
                        }
                    }
                }
            });
        },

        addAriaAttributes: function() {
            const navElements = document.querySelectorAll('nav:not([role])');
            navElements.forEach(nav => {
                nav.setAttribute('role', 'navigation');
            });

            const main = document.querySelector('main:not([role])');
            if (main) {
                main.setAttribute('role', 'main');
            }

            const footer = document.querySelector('footer:not([role])');
            if (footer) {
                footer.setAttribute('role', 'contentinfo');
            }
        },

        initFocusManagement: function() {
            document.addEventListener('invalid', (e) => {
                e.target.focus();
            }, true);

            this.announcePageChanges();
        },

        announcePageChanges: function() {
            const pageTitle = document.title;
            const announcer = document.createElement('div');
            announcer.setAttribute('aria-live', 'polite');
            announcer.setAttribute('aria-atomic', 'true');
            announcer.className = 'visually-hidden';
            announcer.textContent = `Page loaded: ${pageTitle}`;
            document.body.appendChild(announcer);

            setTimeout(() => {
                announcer.remove();
            }, 1000);
        },

        handleBeforeUnload: function(e) {
            const forms = document.querySelectorAll('form');
            const hasUnsavedChanges = Array.from(forms).some(form => {
                return form.hasAttribute('data-changed');
            });

            if (hasUnsavedChanges) {
                e.preventDefault();
                e.returnValue = '';
            }
        },

        handleOnline: function() {
            this.showNotification('Connection restored', 'success');
        },

        handleOffline: function() {
            this.showNotification('Connection lost. Some features may not work.', 'warning');
        },

        showNotification: function(message, type = 'info') {
            const iconMap = {
                'success': 'check-circle',
                'error': 'exclamation-triangle',
                'warning': 'exclamation-triangle',
                'info': 'info-circle'
            };

            const alertDiv = document.createElement('div');
            alertDiv.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
            alertDiv.setAttribute('role', 'alert');
            alertDiv.innerHTML = `
                <i class="bi bi-${iconMap[type] || iconMap.info}" aria-hidden="true"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;

            const container = this.elements.messagesContainer || 
                            document.querySelector('main .container') || 
                            document.querySelector('main');

            if (container) {
                container.insertBefore(alertDiv, container.firstChild);

                setTimeout(() => {
                    this.dismissAlert(alertDiv);
                }, this.config.alertTimeout);
            }
        },

        getCSRFToken: function() {
            return document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                   document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        },

        isValidEmail: function(email) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return emailRegex.test(email);
        },

        restoreButton: function(button, originalText) {
            button.innerHTML = originalText;
            button.disabled = false;
        },

        debounce: function(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },

        throttle: function(func, limit) {
            let inThrottle;
            return function() {
                const args = arguments;
                const context = this;
                if (!inThrottle) {
                    func.apply(context, args);
                    inThrottle = true;
                    setTimeout(() => inThrottle = false, limit);
                }
            };
        }
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => TaskManager.init());
    } else {
        TaskManager.init();
    }

    window.TaskManager = {
        showNotification: TaskManager.showNotification.bind(TaskManager),
        updateTaskStatus: TaskManager.updateTaskStatus.bind(TaskManager),
        validateForm: TaskManager.validateForm.bind(TaskManager)
    };

    window.updateTaskStatus = function(form) {
        TaskManager.updateTaskStatus(form);
    };

    window.checkUsernameAvailability = function(username) {
        TaskManager.checkUsernameAvailability(username);
    };

    window.showNotification = function(message, type) {
        TaskManager.showNotification(message, type);
    };

})(window, document);