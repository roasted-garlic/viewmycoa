// Common utility functions and event handlers

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // Initialize alerts with auto-dismiss
    document.querySelectorAll('.alert').forEach(function(alert) {
        // Add close button if not present
        if (!alert.querySelector('.btn-close')) {
            const closeButton = document.createElement('button');
            closeButton.className = 'btn-close';
            closeButton.setAttribute('data-bs-dismiss', 'alert');
            closeButton.setAttribute('aria-label', 'Close');
            alert.appendChild(closeButton);
        }
        
        // Auto dismiss after 3 seconds
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 3000);
    });
});

// Helper function to show toast notifications
function showNotification(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    const container = document.createElement('div');
    container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    container.appendChild(toast);
    document.body.appendChild(container);
    
    const bsToast = new bootstrap.Toast(toast, {
        delay: 3000
    });
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => {
        container.remove();
    });
}

document.getElementById('confirmDelete')?.addEventListener('click', async function() {
    const productId = document.getElementById('deleteProduct').dataset.productId;
    const confirmationMessage = document.querySelector('.confirmation-message');
    const resultsDiv = document.getElementById('syncResults');
    
    try {
        confirmationMessage.style.display = 'none';
        resultsDiv.innerHTML = '<div class="alert alert-info">Deleting product...</div>';
        
        const response = await fetch(`/api/delete_product/${productId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            resultsDiv.innerHTML = '<div class="alert alert-success">Product deleted successfully!</div>';
            setTimeout(() => {
                window.location.href = '/vmc-admin/products';
            }, 2000);
        } else {
            const data = await response.json();
            resultsDiv.innerHTML = `<div class="alert alert-danger">Error: ${data.error}</div>`;
            confirmationMessage.style.display = 'block';
        }
    } catch (error) {
        console.error('Error:', error);
        resultsDiv.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
        confirmationMessage.style.display = 'block';
    }
});

document.querySelectorAll('.sync-to-square').forEach(button => {
    button.addEventListener('click', async function() {
        if (this.hasAttribute('data-bs-toggle')) {
            return; // Let Bootstrap handle the modal
        }
    });
});