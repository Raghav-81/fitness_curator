/**
 * Enhanced UI Components - JavaScript
 * Toast notifications, modals, and animations
 */

// ============================================
// TOAST NOTIFICATION SYSTEM
// ============================================
class ToastManager {
    constructor() {
        this.container = this.createContainer();
        document.body.appendChild(this.container);
    }
    
    createContainer() {
        const container = document.createElement('div');
        container.className = 'toast-container';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 12px;
        `;
        return container;
    }
    
    show(message, type = 'info', duration = 4000) {
        const toast = this.createToast(message, type);
        this.container.appendChild(toast);
        
        // Animate in
        setTimeout(() => toast.classList.add('show'), 10);
        
        // Auto remove
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, duration);
        
        return toast;
    }
    
    createToast(message, type) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        const icons = {
            success: 'fa-check-circle',
            error: 'fa-times-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };
        
        const colors = {
            success: '#10b981',
            error: '#dc2626',
            warning: '#f59e0b',
            info: '#3b82f6'
        };
        
        toast.innerHTML = `
            <div class="toast-icon" style="background: ${colors[type]};">
                <i class="fas ${icons[type]}"></i>
            </div>
            <div class="toast-content">
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        toast.style.cssText = `
            background: white;
            border-radius: 12px;
            padding: 16px 20px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
            display: flex;
            align-items: center;
            gap: 12px;
            min-width: 320px;
            border-left: 4px solid ${colors[type]};
            transform: translateX(400px);
            opacity: 0;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        `;
        
        // Close button style
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.style.cssText = `
            background: none;
            border: none;
            color: #999;
            cursor: pointer;
            font-size: 16px;
            padding: 4px;
            transition: color 0.2s;
        `;
        closeBtn.onmouseover = () => closeBtn.style.color = '#333';
        closeBtn.onmouseout = () => closeBtn.style.color = '#999';
        
        // Show animation
        toast.classList.add('show');
        setTimeout(() => {
            toast.style.transform = 'translateX(0)';
            toast.style.opacity = '1';
        }, 10);
        
        return toast;
    }
    
    success(message, duration) {
        return this.show(message, 'success', duration);
    }
    
    error(message, duration) {
        return this.show(message, 'error', duration);
    }
    
    warning(message, duration) {
        return this.show(message, 'warning', duration);
    }
    
    info(message, duration) {
        return this.show(message, 'info', duration);
    }
}

// Global toast instance
window.toast = new ToastManager();

// Legacy support
window.showToast = (message, type = 'info') => {
    window.toast.show(message, type);
};

// ============================================
// MODAL SYSTEM
// ============================================
class ModalManager {
    show(content, options = {}) {
        const modal = this.createModal(content, options);
        document.body.appendChild(modal);
        
        setTimeout(() => modal.classList.add('active'), 10);
        
        return modal;
    }
    
    createModal(content, options) {
        const modal = document.createElement('div');
        modal.className = 'modal-modern';
        
        modal.innerHTML = `
            <div class="modal-content-modern">
                ${options.title ? `<h2 style="margin-bottom: 20px; color: #333;">${options.title}</h2>` : ''}
                <div class="modal-body">${content}</div>
                ${options.showClose !== false ? '<button class="modal-close-btn"><i class="fas fa-times"></i></button>' : ''}
            </div>
        `;
        
        // Close button
        const closeBtn = modal.querySelector('.modal-close-btn');
        if (closeBtn) {
            closeBtn.style.cssText = `
                position: absolute;
                top: 20px;
                right: 20px;
                background: #f3f4f6;
                border: none;
                width: 36px;
                height: 36px;
                border-radius: 50%;
                cursor: pointer;
                color: #666;
                font-size: 16px;
                transition: all 0.2s;
            `;
            closeBtn.onmouseover = () => {
                closeBtn.style.background = '#ff6b35';
                closeBtn.style.color = 'white';
            };
            closeBtn.onmouseout = () => {
                closeBtn.style.background = '#f3f4f6';
                closeBtn.style.color = '#666';
            };
            closeBtn.onclick = () => this.close(modal);
        }
        
        // Click outside to close
        modal.onclick = (e) => {
            if (e.target === modal) this.close(modal);
        };
        
        return modal;
    }
    
    close(modal) {
        modal.classList.remove('active');
        setTimeout(() => modal.remove(), 300);
    }
}

window.modal = new ModalManager();

// ============================================
// LOADING ANIMATIONS
// ============================================
function showLoading(element, type = 'spinner') {
    const loaders = {
        spinner: '<div class="loading-spinner"></div>',
        pulse: '<div class="pulse-loader"><div class="pulse-dot"></div><div class="pulse-dot"></div><div class="pulse-dot"></div></div>',
        skeleton: '<div class="skeleton" style="height: 200px; width: 100%;"></div>'
    };
    
    if (typeof element === 'string') {
        element = document.querySelector(element);
    }
    
    if (element) {
        element.innerHTML = `<div style="display: flex; justify-content: center; align-items: center; padding: 40px;">${loaders[type]}</div>`;
    }
}

// ============================================
// SCROLL ANIMATIONS
// ============================================
class ScrollAnimator {
    constructor() {
        this.init();
    }
    
    init() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate__animated', 'animate__fadeInUp');
                }
            });
        }, {
            threshold: 0.1
        });
        
        document.querySelectorAll('[data-animate]').forEach(el => {
            observer.observe(el);
        });
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    new ScrollAnimator();
});

// ============================================
// PARTICLE SYSTEM
// ============================================
function createParticles(container) {
    const particleCount = 15;
    
    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.cssText = `
            position: absolute;
            width: ${Math.random() * 4 + 2}px;
            height: ${Math.random() * 4 + 2}px;
            background: ${Math.random() > 0.5 ? '#ff6b35' : '#fbbf24'};
            border-radius: 50%;
            left: ${Math.random() * 100}%;
            animation: float ${Math.random() * 10 + 15}s infinite;
            animation-delay: ${Math.random() * 5}s;
            opacity: ${Math.random() * 0.3 + 0.2};
        `;
        container.appendChild(particle);
    }
}

// ============================================
// COUNTER ANIMATION
// ============================================
function animateCounter(element, target, duration = 2000) {
    const start = 0;
    const increment = target / (duration / 16);
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            current = target;
            clearInterval(timer);
        }
        element.textContent = Math.floor(current);
    }, 16);
}

// ============================================
// PROGRESS BAR ANIMATION
// ============================================
function animateProgress(element, percentage, duration = 1000) {
    element.style.transition = `width ${duration}ms cubic-bezier(0.4, 0, 0.2, 1)`;
    setTimeout(() => {
        element.style.width = `${percentage}%`;
    }, 10);
}

// ============================================
// UTILITY FUNCTIONS
// ============================================

// Smooth scroll to element
function smoothScrollTo(element, offset = 0) {
    const targetPosition = element.getBoundingClientRect().top + window.pageYOffset - offset;
    window.scrollTo({
        top: targetPosition,
        behavior: 'smooth'
    });
}

// Copy to clipboard with toast
function copyToClipboard(text, successMessage = 'Copied to clipboard!') {
    navigator.clipboard.writeText(text).then(() => {
        window.toast.success(successMessage);
    }).catch(() => {
        window.toast.error('Failed to copy');
    });
}

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ============================================
// EXPORT FOR GLOBAL USE
// ============================================
window.EnhancedUI = {
    toast: window.toast,
    modal: window.modal,
    showLoading,
    createParticles,
    animateCounter,
    animateProgress,
    smoothScrollTo,
    copyToClipboard,
    debounce
};
