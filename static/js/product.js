
document.addEventListener('DOMContentLoaded', async function() {
    const batchInput = document.getElementById('batchNumber');
    const enableBatchEdit = document.getElementById('enableBatchEdit');
    const generateBatchBtn = document.getElementById('generateBatch');
    const templateSelect = document.getElementById('template');
    const attributesContainer = document.getElementById('attributesContainer');
    const addAttributeBtn = document.getElementById('addAttribute');

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

    // Enable batch edit functionality
    if (enableBatchEdit && batchNumberInput && generateBatchBtn) {
        enableBatchEdit.addEventListener('change', function() {
            batchInput.readOnly = !this.checked;
            generateBatchBtn.disabled = this.checked;
        });
    }

    // Generate batch button functionality
    if (generateBatchBtn && batchInput) {
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
                    batchInput.value = data.batch_number;
                }
            } catch (error) {
                console.error('Error generating batch number:', error);
            }
        });
    }

    // Template dropdown functionality
    if (templateSelect) {
        templateSelect.addEventListener('change', async function() {
            const templateId = this.value;
            if (templateId) {
                try {
                    const response = await fetch(`/api/template/${templateId}`);
                    if (response.ok) {
                        const template = await response.json();
                        const attributes = template.attributes || {};
                        attributesContainer.innerHTML = '';
                        
                        Object.entries(attributes).forEach(([name, value]) => {
                            addAttributeField(name, value);
                        });
                    }
                } catch (error) {
                    console.error('Error fetching template:', error);
                }
            } else {
                attributesContainer.innerHTML = '';
            }
        });
    }

    // Add attribute button functionality
    if (addAttributeBtn && attributesContainer) {
        addAttributeBtn.addEventListener('click', function() {
            addAttributeField();
        });
    }

    // Function to add attribute fields
    function addAttributeField(name = '', value = '') {
        const attributeGroup = document.createElement('div');
        attributeGroup.className = 'attribute-group mb-2';
        
        attributeGroup.innerHTML = `
            <div class="row">
                <div class="col">
                    <input type="text" class="form-control attr-name" name="attr_name[]" value="${name}" placeholder="Attribute Name" required>
                </div>
                <div class="col">
                    <input type="text" class="form-control" name="attr_value[]" value="${value}" placeholder="Value">
                </div>
                <div class="col-auto">
                    <button type="button" class="btn btn-danger remove-attribute">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;

        // Add event listener for lowercase conversion
        const attrNameInput = attributeGroup.querySelector('.attr-name');
        attrNameInput.addEventListener('input', function() {
            this.value = this.value.toLowerCase();
        });

        // Add event listener for remove button
        const removeBtn = attributeGroup.querySelector('.remove-attribute');
        removeBtn.addEventListener('click', function() {
            attributeGroup.remove();
        });
        
        attributesContainer.appendChild(attributeGroup);
    }
});
