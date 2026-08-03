(function() {
    'use strict';

    // Auto-dismiss toast messages
    document.querySelectorAll('#mobile-toasts .mobile-toast').forEach(function(toast) {
        setTimeout(function() {
            toast.style.transition = 'opacity 0.3s, transform 0.3s';
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(-8px)';
            setTimeout(function() { toast.remove(); }, 320);
        }, 4000);
    });

    // Global toast helper (used by inline page scripts)
    window.showToast = function(message, type) {
        var container = document.getElementById('mobile-toasts');
        if (!container) {
            container = document.createElement('div');
            container.id = 'mobile-toasts';
            container.className = 'mobile-toasts';
            document.body.appendChild(container);
        }
        var toast = document.createElement('div');
        toast.className = 'mobile-toast toast-' + (type || 'info');
        var icon = type === 'success' ? 'fa-check-circle' : (type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle');
        toast.innerHTML = '<i class="fas ' + icon + '"></i><span>' + message + '</span>';
        container.appendChild(toast);
        setTimeout(function() {
            toast.style.transition = 'opacity 0.3s, transform 0.3s';
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(-8px)';
            setTimeout(function() { toast.remove(); }, 320);
        }, 3000);
    };

    // Prevent double-tap zoom on quick taps
    var lastTap = 0;
    document.addEventListener('touchend', function(e) {
        var now = Date.now();
        if (now - lastTap < 350 && e.target.closest('a,button')) {
            e.preventDefault();
        }
        lastTap = now;
    }, { passive: false });
})();
