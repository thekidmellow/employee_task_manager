window.True = true;
window.False = false;

(function (window, document) {
    "use strict";

    const ETM = (window.ETM = window.ETM || {});

    function getCsrfToken() {
        const tokenInput = document.querySelector("[name=csrfmiddlewaretoken]");
        if (tokenInput && tokenInput.value) {
            return tokenInput.value;
        }

        const name = "csrftoken";
        const cookies = document.cookie ? document.cookie.split(";") : [];
        for (let i = 0; i < cookies.length; i++) {
            const c = cookies[i].trim();
            if (c.substring(0, name.length + 1) === name + "=") {
                return decodeURIComponent(c.substring(name.length + 1));
            }
        }
        return null;
    }

    function showAlert(message, type) {
        type = type || "info";

        document.querySelectorAll(".alert-auto").forEach(function (a) {
            a.remove();
        });

        const el = document.createElement("div");
        el.className = "alert alert-" + type + " alert-dismissible fade show alert-auto";
        el.setAttribute("role", "alert");
        el.innerHTML =
            '<span class="me-2" aria-hidden="true"></span>' +
            message +
            '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>';

        const main = document.querySelector("main") || document.body;
        main.insertBefore(el, main.firstChild);

        setTimeout(function () {
            if (el.parentNode) {
                el.classList.remove("show");
                setTimeout(function () {
                    if (el.parentNode) {
                        el.remove();
                    }
                }, 200);
            }
        }, 5000);
    }

    ETM.updateTaskStatus = function (taskId, status) {
        if (!taskId || !status) {
            showAlert("Missing task information for status update.", "danger");
            return;
        }

        const statusText = status
            .replace("_", " ")
            .replace(/\b\w/g, function (l) {
                return l.toUpperCase();
            });

        if (!window.confirm('Are you sure you want to change the task status to "' + statusText + '"?')) {
            return;
        }

        const csrfToken = getCsrfToken();
        if (!csrfToken) {
            showAlert("Security token missing. Please refresh the page and try again.", "danger");
            return;
        }

        const buttons = document.querySelectorAll('[data-etm-action="update-status"]');
        buttons.forEach(function (btn) {
            if (!btn.dataset.originalText) {
                btn.dataset.originalText = btn.innerHTML;
            }
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Updating...';
        });

        fetch("/tasks/" + taskId + "/update-status/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken
            },
            body: JSON.stringify({ status: status })
        })
            .then(function (response) {
                if (!response.ok) {
                    throw new Error("HTTP " + response.status);
                }
                return response.json();
            })
            .then(function (data) {
                if (!data.success) {
                    throw new Error(data.error || data.message || "Unknown error");
                }
                const label = data.status_display || statusText;
                showAlert("Task status updated to " + label + " successfully!", "success");
                window.setTimeout(function () {
                    window.location.reload();
                }, 1200);
            })
            .catch(function (err) {
                console.error("Error updating task status:", err);
                showAlert("Error updating task status: " + err.message, "danger");
                buttons.forEach(function (btn) {
                    btn.disabled = false;
                    if (btn.dataset.originalText) {
                        btn.innerHTML = btn.dataset.originalText;
                    }
                });
            });
    };

    ETM.deleteTask = function (taskId, redirectUrl) {
        if (!taskId) {
            showAlert("Missing task information for delete.", "danger");
            return;
        }
        if (!window.confirm("Are you sure you want to delete this task? This action cannot be undone.")) {
            return;
        }

        const csrfToken = getCsrfToken();
        if (!csrfToken) {
            showAlert("Security token missing. Please refresh the page and try again.", "danger");
            return;
        }

        const deleteBtn = document.querySelector('[data-etm-action="delete-task"]');
        if (deleteBtn) {
            deleteBtn.disabled = true;
            deleteBtn.innerHTML =
                '<span class="spinner-border spinner-border-sm me-2"></span>Deleting...';
        }

        fetch("/tasks/" + taskId + "/delete/", {
            method: "POST",
            headers: {
                "X-CSRFToken": csrfToken
            }
        })
            .then(function (response) {
                if (!response.ok) {
                    throw new Error("HTTP " + response.status + ": " + response.statusText);
                }
                showAlert("Task deleted successfully. Redirecting...", "success");
                window.setTimeout(function () {
                    window.location.href = redirectUrl || "/tasks/";
                }, 1200);
            })
            .catch(function (err) {
                console.error("Error deleting task:", err);
                showAlert("Error deleting task. Please try again.", "danger");
                if (deleteBtn) {
                    deleteBtn.disabled = false;
                    deleteBtn.innerHTML = '<i class="bi bi-trash" aria-hidden="true"></i> Delete';
                }
            });
    };

    function initTaskFilters() {
        const form = document.querySelector('[data-etm-role="task-filter-form"]');
        if (!form) {
            return;
        }
        const inputs = form.querySelectorAll("input, select");
        inputs.forEach(function (input) {
            input.addEventListener("change", function () {
                form.submit();
            });
        });
    }

    function initCommentForm() {
        const form = document.getElementById("commentForm");
        const textarea = document.getElementById("comment");
        const submitBtn = document.getElementById("commentSubmitBtn");
        if (!form || !textarea || !submitBtn) {
            return;
        }

        function resize() {
            textarea.style.height = "auto";
            textarea.style.height = textarea.scrollHeight + "px";
        }
        textarea.addEventListener("input", resize);
        resize();

        const maxLength = 1000;
        let counter = textarea.parentNode.querySelector(".comment-counter");
        if (!counter) {
            counter = document.createElement("div");
            counter.className = "form-text text-end text-muted comment-counter";
            textarea.parentNode.appendChild(counter);
        }

        function updateCounter() {
            const len = textarea.value.length;
            const remaining = maxLength - len;
            counter.textContent = len + "/" + maxLength + " characters";
            if (remaining < 50) {
                counter.className = "form-text text-end text-danger comment-counter";
            } else if (remaining < 100) {
                counter.className = "form-text text-end text-warning comment-counter";
            } else {
                counter.className = "form-text text-end text-muted comment-counter";
            }
        }
        textarea.addEventListener("input", updateCounter);
        updateCounter();

        form.addEventListener("submit", function (e) {
            const value = textarea.value.trim();
            if (value.length < 5) {
                e.preventDefault();
                showAlert("Comment must be at least 5 characters long.", "warning");
                textarea.focus();
                return;
            }
            if (value.length > maxLength) {
                e.preventDefault();
                showAlert("Comment cannot exceed 1000 characters.", "warning");
                textarea.focus();
                return;
            }

            const original = submitBtn.innerHTML;
            submitBtn.innerHTML =
                '<span class="spinner-border spinner-border-sm me-2"></span>Posting...';
            submitBtn.disabled = true;

            window.setTimeout(function () {
                if (submitBtn.disabled) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = original;
                }
            }, 10000);
        });

        document.addEventListener("keydown", function (e) {
            if (e.altKey && e.key === "c") {
                e.preventDefault();
                textarea.focus();
            }
        });
    }

    function enhanceAccessibility() {
        document.querySelectorAll(".comment-item").forEach(function (item, i) {
            item.setAttribute("tabindex", "0");
            if (!item.getAttribute("aria-label")) {
                item.setAttribute("aria-label", "Comment " + (i + 1));
            }
        });

        const progressCircle = document.querySelector(".progress-circle");
        if (progressCircle && !progressCircle.getAttribute("aria-label")) {
            const percentage = progressCircle.getAttribute("aria-valuenow") || "0";
            progressCircle.setAttribute("aria-label", "Task is " + percentage + "% complete");
        }

        const skipLink = document.querySelector('a[href="#main-content"]');
        const main = document.getElementById("main-content");
        if (skipLink && main) {
            skipLink.addEventListener("click", function (e) {
                e.preventDefault();
                main.setAttribute("tabindex", "-1");
                main.focus();
            });
        }
    }

    document.addEventListener("DOMContentLoaded", function () {
        initTaskFilters();
        initCommentForm();
        enhanceAccessibility();

        document
            .querySelectorAll(
                'button[onclick*="updateTaskStatus"], button[data-etm-action="update-status"]'
            )
            .forEach(function (btn) {
                btn.dataset.originalText = btn.innerHTML;
            });
    });

    // ==== Global aliases for older / simpler JS checks in tests ====
    // Some browser tests may expect these directly on window.
    window.updateTaskStatus = ETM.updateTaskStatus;
    window.deleteTask = ETM.deleteTask;

})(window, document);
