// Main JavaScript for ALL-in-One Email Portal

// Utility function to show toast notifications
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999;';
        document.body.appendChild(container);
    }
    
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} alert-dismissible fade show`;
    toast.role = 'alert';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.getElementById('toastContainer').appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 5000);
}

// Format date/time
function formatDateTime(dateString) {
    if (!dateString) return '--';
    const date = new Date(dateString);
    return date.toLocaleString();
}

// Format duration
function formatDuration(startTime) {
    if (!startTime) return '--:--';
    const start = new Date(startTime);
    const now = new Date();
    const diff = Math.floor((now - start) / 1000);
    
    const hours = Math.floor(diff / 3600);
    const minutes = Math.floor((diff % 3600) / 60);
    const seconds = diff % 60;
    
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

// Auto-refresh functionality
let refreshInterval = null;

function startAutoRefresh(callback, interval = 5000) {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
    refreshInterval = setInterval(callback, interval);
}

function stopAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
    }
}

// Export for use in other scripts
window.appUtils = {
    showToast,
    formatDateTime,
    formatDuration,
    startAutoRefresh,
    stopAutoRefresh
};

// Initialize Socket.IO connection
try {
    if (typeof io !== 'undefined') {
        window.socket = io({
            transports: ['websocket', 'polling'],
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionAttempts: 5
        });
        
        socket.on('connect', function() {
            console.log('✅ Socket.IO connected');
        });
        
        socket.on('disconnect', function() {
            console.log('⚠️ Socket.IO disconnected');
        });
        
        socket.on('connect_error', function(error) {
            console.error('❌ Socket.IO connection error:', error);
        });
    } else {
        console.warn('Socket.IO library not loaded');
    }
} catch (error) {
    console.error('Error initializing Socket.IO:', error);
}

console.log('ALL-in-One Email Portal loaded successfully');
