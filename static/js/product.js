
document.addEventListener('DOMContentLoaded', async function() {
    const batchInput = document.getElementById('batchNumber');
    const enableBatchEdit = document.getElementById('enableBatchEdit');
    const generateBatchBtn = document.getElementById('generateBatch');
    const batchNumberInput = document.getElementById('batchNumber');

    // Auto generate batch number on page load for create page
    if (batchInput && !batchInput.value) {
        try {
            const response = await fetch('/api/generate_batch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            if (response.ok) {
                const data = await response.json();
                batchInput.value = data.batch_number;
            }
        } catch (error) {
            console.error('Error generating batch number:', error);
        }
    }

    // Enable batch edit functionality for both create and edit pages
    if (enableBatchEdit && batchNumberInput && generateBatchBtn) {
        enableBatchEdit.addEventListener('change', function() {
            batchNumberInput.readOnly = !this.checked;
            generateBatchBtn.disabled = this.checked;
        });
    }

    // Add generate batch button functionality
    if (generateBatchBtn && batchNumberInput) {
        generateBatchBtn.addEventListener('click', async function() {
            try {
                const response = await fetch('/api/generate_batch', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                if (response.ok) {
                    const data = await response.json();
                    batchNumberInput.value = data.batch_number;
                }
            } catch (error) {
                console.error('Error generating batch number:', error);
            }
        });
    }
});
