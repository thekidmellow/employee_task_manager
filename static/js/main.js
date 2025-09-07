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

    /**
     * Main application object
     */
    const TaskManager = {
        // Configuration
        config: {
            alertTimeout: 5000,
            debounceDelay: 500,
            animationDuration: 300
        },

        // Cache DOM elements
        elements: {},

        /**
         * Initialize the application
         */
        init: function() {
            this.cacheElements();
            this.bindEvents();
            this.initializeComponents();
            this.enhanceAccessibility();
            
            console.log('Task Manager initialized successfully');
        },

        /**
         * Cache frequently used DOM elements
         */
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

        /**
         * Bind event listeners
         */
        bindEvents: function() {
            // Auto-dismiss alerts
            this.initAlertSystem();

            // Status update forms
            this.initStatusUpdates();

            // Username availability checker
            this.initUsernameChecker();

            // Form validation
            this.initFormValidation();

            // Dashboard auto-refresh
            this.initDashboardRefresh();

            // Global keyboard shortcuts
            this.initKeyboardShortcuts();

            // Window events
            window.addEventListener('beforeunload', this.handleBeforeUnload.bind(this));
            window.addEventListener('online', this.handleOnline.bind(this));
            window.addEventListener('offline', this.handleOffline.bind(this));
        },

        /**
         * Initialize components
         */
        initializeComponents: function() {
            this.initTooltips();
            this.initPopovers();
            this.initProgressBars();
            this.initCardAnimations();
        },

        /**
         * Alert system initialization
         */
        initAlertSystem: function() {
            this.elements.alerts.forEach(alert => {
                setTimeout(() => {
                    if (alert && alert.parentNode) {
                        this.dismissAlert(alert);
                    }
                }, this.config.alertTimeout);
            });
        },

        /**
         * Dismiss alert with animation
         */
        dismissAlert: function(alert) {
            alert.classList.remove('show');
            setTimeout(() => {
                if (alert.parentNode) {
                    alert.remove();
                }
            }, this.config.animationDuration);
        },

        /**
         * Status update system
         */
        initStatusUpdates: function() {
            this.elements.statusForms.forEach(form => {
                form.addEventListener('submit', (e) => {
                    e.preventDefault();
                    this.updateTaskStatus(form);
                });
            });
        },

        /**
         * Update task status via AJAX
         */
        updateTaskStatus: function(form) {
            const formData = new FormData(form);
            const submitBtn = form.querySelector('button[type="submit"]');
            
            // Show loading state
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Updating...';
            submitBtn.disabled = true;

            // Get CSRF token
            const csrfToken = this.getCSRFToken();
            if (!csrfToken) {
                this.showNotification('Security token missing. Please refresh the page.', 'error');
                this.restoreButton(submitBtn, originalText);
                return;
            }

            // Make request
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

        /**
         * Handle successful status update
         */
        handleStatusUpdateSuccess: function(form, data) {
            const taskCard = form.closest('.task-card');
            if (taskCard && data.status_display && data.status_color) {
                const statusBadge = taskCard.querySelector('.status-badge');
                if (statusBadge) {
                    statusBadge.textContent = data.status_display;
                    statusBadge.className = `badge bg-${data.status_color} status-badge`;
                }

                // Update progress bar if present
                const progressBar = taskCard.querySelector('.progress-bar');
                if (progressBar && data.progress_percentage !== undefined) {
                    progressBar.style.width = `${data.progress_percentage}%`;
                    progressBar.setAttribute('aria-valuenow', data.progress_percentage);
                }
            }
        },

        /**
         * Username availability checker
         */
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

        /**
         * Check username availability
         */
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

        /**
         * Form validation system
         */
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

        /**
         * Validate form
         */
        validateForm: function(form) {
            let isValid = true;
            const requiredFields = form.querySelectorAll('[required]');

            // Clear previous errors
            form.querySelectorAll('.is-invalid').forEach(field => {
                field.classList.remove('is-invalid');
            });
            form.querySelectorAll('.invalid-feedback').forEach(feedback => {
                if (!feedback.hasAttribute('data-server-error')) {
                    feedback.remove();
                }
            });

            // Validate required fields
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    this.showFieldError(field, 'This field is required');
                    isValid = false;
                }
            });

            // Email validation
            const emailFields = form.querySelectorAll('input[type="email"]');
            emailFields.forEach(field => {
                if (field.value && !this.isValidEmail(field.value)) {
                    this.showFieldError(field, 'Please enter a valid email address');
                    isValid = false;
                }
            });

            // Password matching
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

        /**
         * Show field error
         */
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

        /**
         * Dashboard refresh system
         */
        initDashboardRefresh: function() {
            if (this.elements.dashboardStats) {
                this.refreshDashboardStats();
                setInterval(() => {
                    this.refreshDashboardStats();
                }, 30000); // Refresh every 30 seconds
            }
        },

        /**
         * Refresh dashboard statistics
         */
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

        /**
         * Update statistics display
         */
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

        /**
         * Animate number change
         */
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

        /**
         * Initialize keyboard shortcuts
         */
        initKeyboardShortcuts: function() {
            document.addEventListener('keydown', (e) => {
                // Ctrl/Cmd + K for search
                if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                    e.preventDefault();
                    const searchField = document.querySelector('input[type="search"], input[name="search"]');
                    if (searchField) {
                        searchField.focus();
                    }
                }

                // Escape to close modals/dropdowns
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

        /**
         * Initialize tooltips
         */
        initTooltips: function() {
            const tooltipElements = document.querySelectorAll('[data-bs-toggle="tooltip"]');
            if (tooltipElements.length && window.bootstrap) {
                tooltipElements.forEach(element => {
                    new bootstrap.Tooltip(element);
                });
            }
        },

        /**
         * Initialize popovers
         */
        initPopovers: function() {
            const popoverElements = document.querySelectorAll('[data-bs-toggle="popover"]');
            if (popoverElements.length && window.bootstrap) {
                popoverElements.forEach(element => {
                    new bootstrap.Popover(element);
                });
            }
        },

        /**
         * Initialize progress bars
         */
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

        /**
         * Initialize card animations
         */
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

        /**
         * Enhance accessibility
         */
        enhanceAccessibility: function() {
            // Add skip links
            this.addSkipLinks();

            // Enhance form labels
            this.enhanceFormLabels();

            // Add ARIA attributes
            this.addAriaAttributes();

            // Focus management
            this.initFocusManagement();
        },

        /**
         * Add skip links for keyboard navigation
         */
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

        /**
         * Enhance form labels
         */
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

        /**
         * Add ARIA attributes
         */
        addAriaAttributes: function() {
            // Add role attributes to navigation
            const navElements = document.querySelectorAll('nav:not([role])');
            navElements.forEach(nav => {
                nav.setAttribute('role', 'navigation');
            });

            // Add landmark roles
            const main = document.querySelector('main:not([role])');
            if (main) {
                main.setAttribute('role', 'main');
            }

            const footer = document.querySelector('footer:not([role])');
            if (footer) {
                footer.setAttribute('role', 'contentinfo');
            }
        },

        /**
         * Initialize focus management
         */
        initFocusManagement: function() {
            // Focus first error field on form submission
            document.addEventListener('invalid', (e) => {
                e.target.focus();
            }, true);

            // Announce page changes for screen readers
            this.announcePageChanges();
        },

        /**
         * Announce page changes for screen readers
         */
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

        /**
         * Handle window beforeunload
         */
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

        /**
         * Handle online event
         */
        handleOnline: function() {
            this.showNotification('Connection restored', 'success');
        },

        /**
         * Handle offline event
         */
        handleOffline: function() {
            this.showNotification('Connection lost. Some features may not work.', 'warning');
        },

        /**
         * Show notification
         */
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

                // Auto-dismiss
                setTimeout(() => {
                    this.dismissAlert(alertDiv);
                }, this.config.alertTimeout);
            }
        },

        /**
         * Utility functions
         */
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

        /**
         * Debounce function
         */
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

        /**
         * Throttle function
         */
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

    /**
     * Initialize when DOM is ready
     */
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => TaskManager.init());
    } else {
        TaskManager.init();
    }

    /**
     * Expose public API
     */
    window.TaskManager = {
        showNotification: TaskManager.showNotification.bind(TaskManager),
        updateTaskStatus: TaskManager.updateTaskStatus.bind(TaskManager),
        validateForm: TaskManager.validateForm.bind(TaskManager)
    };

    /**
     * Legacy function support for backwards compatibility
     */
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