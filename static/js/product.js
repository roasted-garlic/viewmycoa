
document.addEventListener('DOMContentLoaded', async function() {
    // COA Delete functionality
    const coaDeleteModal = new bootstrap.Modal(document.getElementById('coaDeleteModal'));
    const confirmCoaDelete = document.getElementById('confirmCoaDelete');
    let productIdToDeleteCoa = null;

    document.querySelectorAll('.delete-coa').forEach(button => {
        button.addEventListener('click', function() {
            productIdToDeleteCoa = this.dataset.productId;
        });
    });

    confirmCoaDelete.addEventListener('click', async function() {
        if (productIdToDeleteCoa) {
            try {
                const response = await fetch(`/api/delete_coa/${productIdToDeleteCoa}`, {
                    method: 'DELETE'
                });
                if (response.ok) {
                    // Reload the page to reflect changes
                    window.location.reload();
                } else {
                    alert('Error deleting COA');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Error deleting COA');
            }
            coaDeleteModal.hide();
        }
    });
    const batchInput = document.getElementById('batchNumber');
    const generateBatchBtn = document.getElementById('generateBatch');
    const addAttributeBtn = document.getElementById('addAttribute');
    const attributesContainer = document.getElementById('attributesContainer');
    const templateSelect = document.getElementById('template');
    const enableBatchEdit = document.getElementById('enableBatchEdit');
    const batchNumberInput = document.getElementById('batchNumber');

    // Auto generate batch number on page load for create page
    if (batchInput) {
        if (!batchInput.value) {
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
        if (enableBatchEdit) {
            enableBatchEdit.addEventListener('change', function() {
                batchNumberInput.readOnly = !this.checked;
                if (generateBatchBtn) {
                    generateBatchBtn.disabled = this.checked;
                }
            });
        }
    }

    function handleImagePreview(inputId, previewId) {
        const input = document.getElementById(inputId);
        const preview = document.getElementById(previewId);
        
        if (input && preview) {
            input.addEventListener('change', function(e) {
                if (this.files && this.files[0]) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        const previewImg = preview.querySelector('img');
                        previewImg.src = e.target.result;
                        preview.classList.remove('d-none');
                    }
                    reader.readAsDataURL(this.files[0]);
                }
            });
        }
    }

    handleImagePreview('productImage', 'productImagePreview');
    handleImagePreview('labelImage', 'labelImagePreview');

    function initializeDeleteHandler(button) {
        button.addEventListener('click', function() {
            const attributeGroup = button.closest('.attribute-group');
            if (attributeGroup) {
                attributeGroup.remove();
            }
        });
    }

    document.querySelectorAll('.remove-attribute').forEach(button => {
        initializeDeleteHandler(button);
    });

    if (enableBatchEdit) {
        enableBatchEdit.addEventListener('change', function() {
            batchNumberInput.readOnly = !this.checked;
            generateBatchBtn.disabled = this.checked;
        });
    }

    if (generateBatchBtn) {
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
                    document.getElementById('batchNumber').value = data.batch_number;
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Error generating batch number');
            }
        });
    }

    if (addAttributeBtn && attributesContainer) {
        addAttributeBtn.addEventListener('click', function() {
            const attributeGroup = document.createElement('div');
            attributeGroup.className = 'attribute-group mb-2';
            
            attributeGroup.innerHTML = `
                <div class="row">
                    <div class="col">
                        <input type="text" class="form-control attr-name" name="attr_name[]" placeholder="Attribute Name" required>
                    </div>
                    <div class="col">
                        <input type="text" class="form-control" name="attr_value[]" placeholder="Attribute Value" required>
                    </div>
                    <div class="col-auto">
                        <button type="button" class="btn btn-danger remove-attribute">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `;
            
            const attrNameInput = attributeGroup.querySelector('.attr-name');
            attrNameInput.addEventListener('input', function(e) {
                this.value = this.value.toLowerCase();
            });
            
            attributesContainer.appendChild(attributeGroup);
            initializeDeleteHandler(attributeGroup.querySelector('.remove-attribute'));
            attrNameInput.focus();
        });
    }

    if (templateSelect && attributesContainer) {
        templateSelect.addEventListener('change', async function() {
            const templateId = this.value;
            if (!templateId) {
                attributesContainer.innerHTML = '';
                return;
            }
            
            try {
                const response = await fetch(`/api/template/${templateId}`);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const template = await response.json();
                attributesContainer.innerHTML = '';
                
                if (template && template.attributes) {
                    let attributes;
                    try {
                        attributes = typeof template.attributes === 'string' 
                            ? JSON.parse(template.attributes) 
                            : template.attributes;
                    } catch (e) {
                        console.error('Error parsing attributes:', e);
                        attributes = template.attributes;
                    }
                    
                    if (attributes && typeof attributes === 'object') {
                        Object.entries(attributes).forEach(([name, value]) => {
                            const attributeGroup = document.createElement('div');
                            attributeGroup.className = 'attribute-group mb-2';
                            
                            attributeGroup.innerHTML = `
                                <div class="row">
                                    <div class="col">
                                        <input type="text" class="form-control attr-name" name="attr_name[]" value="${name.replace(/"/g, '&quot;')}" required>
                                    </div>
                                    <div class="col">
                                        <input type="text" class="form-control" name="attr_value[]" value="${(value || '').replace(/"/g, '&quot;')}" required>
                                    </div>
                                    <div class="col-auto">
                                        <button type="button" class="btn btn-danger remove-attribute">
                                            <i class="fas fa-trash"></i>
                                        </button>
                                    </div>
                                </div>
                            `;
                            
                            attributesContainer.appendChild(attributeGroup);
                            initializeDeleteHandler(attributeGroup.querySelector('.remove-attribute'));
                        });
                    }
                }
            } catch (error) {
                console.error('Error loading template:', error);
                alert('Failed to load template attributes');
            }
        });
    }
});
