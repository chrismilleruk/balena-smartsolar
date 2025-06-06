// Check connectivity on page load
document.addEventListener('DOMContentLoaded', function() {
    checkAllConnections();
    
    // Set up refresh button
    const refreshBtn = document.getElementById('refresh-btn');
    refreshBtn.addEventListener('click', checkAllConnections);
    
    // Auto-check every 30 seconds
    setInterval(checkAllConnections, 30000);
});

function checkAllConnections() {
    const refreshBtn = document.getElementById('refresh-btn');
    refreshBtn.disabled = true;
    refreshBtn.textContent = 'Checking...';
    
    // Reset all status indicators
    document.querySelectorAll('.status-dot').forEach(dot => {
        dot.className = 'status-dot';
    });
    document.querySelectorAll('.status-text').forEach(text => {
        text.textContent = 'Checking...';
    });
    
    fetch('/api/check-connectivity')
        .then(response => response.json())
        .then(data => {
            // Update each service status
            Object.entries(data.results).forEach(([serviceName, result]) => {
                updateServiceStatus(serviceName, result.accessible);
            });
            
            // Update last check time
            const lastCheckTime = new Date().toLocaleTimeString();
            document.getElementById('last-check-time').textContent = lastCheckTime;
            
            refreshBtn.disabled = false;
            refreshBtn.textContent = 'Check All Connections';
        })
        .catch(error => {
            console.error('Error checking connectivity:', error);
            refreshBtn.disabled = false;
            refreshBtn.textContent = 'Check All Connections';
            
            // Mark all as unknown
            document.querySelectorAll('.status-text').forEach(text => {
                text.textContent = 'Error';
            });
        });
}

function updateServiceStatus(serviceName, isAccessible) {
    const serviceCard = document.querySelector(`[data-service="${serviceName}"]`);
    if (!serviceCard) return;
    
    const statusDot = serviceCard.querySelector('.status-dot');
    const statusText = serviceCard.querySelector('.status-text');
    
    if (isAccessible) {
        statusDot.className = 'status-dot online';
        statusText.textContent = 'Online';
        statusText.style.color = '#28a745';
    } else {
        statusDot.className = 'status-dot offline';
        statusText.textContent = 'Offline';
        statusText.style.color = '#dc3545';
    }
} 