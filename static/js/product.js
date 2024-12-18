document.addEventListener('DOMContentLoaded', function() {
    // Delete COA handler
    document.querySelectorAll('.delete-coa').forEach(button => {
        button.addEventListener('click', async function() {
            if (confirm('Are you sure you want to delete this COA?')) {
                const productId = this.dataset.productId;
                try {
                    const response = await fetch(`/api/delete_coa/${productId}`, {
                        method: 'DELETE'
                    });
                    if (response.ok) {
                        location.reload();
                    } else {
                        alert('Failed to delete COA');
                    }
                } catch (error) {
                    console.error('Error:', error);
                    alert('Error deleting COA');
                }
            }
        });
    });
    const generateBatchBtn = document.getElementById('generateBatch');
    const addAttributeBtn = document.getElementById('addAttribute');
    const attributesContainer = document.getElementById('attributesContainer');
    const templateSelect = document.getElementById('template');

    // Initialize delete handlers for existing attributes
    document.querySelectorAll('.remove-attribute').forEach(button => {
        initializeDeleteHandler(button);
    });

    // Generate batch number
    if (generateBatchBtn) {
        generateBatchBtn.addEventListener('click', async function() {
            try {
                const response = await fetch('/api/generate_batch', {
                    method: 'POST'
                });
                const data = await response.json();
                document.getElementById('batchNumber').value = data.batch_number;
            } catch (error) {
                console.error('Error generating batch number:', error);
            }
        });

        // Only generate initial batch number on create page (when batch number is empty)
        if (!document.getElementById('batchNumber').value) {
            generateBatchBtn.click();
        }
    // Handle template selection
    if (templateSelect) {
        templateSelect.addEventListener('change', async function() {
            const templateId = this.value;
            if (templateId) {
                try {
                    const response = await fetch(`/api/template/${templateId}`);
                    if (response.ok) {
                        const template = await response.json();
                        // Clear existing attributes
                        attributesContainer.innerHTML = '';
                        // Add template attributes
                        Object.keys(template.attributes).forEach(attrName => {
                            const attributeGroup = document.createElement('div');
                            attributeGroup.className = 'attribute-group mb-2';
                            
                            attributeGroup.innerHTML = `
                                <div class="row">
                                    <div class="col">
                                        <input type="text" class="form-control attr-name" name="attr_name[]" value="${attrName}" required>
                                    </div>
                                    <div class="col">
                                        <input type="text" class="form-control" name="attr_value[]" value="" required>
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
                } catch (error) {
                    console.error('Error loading template:', error);
                }
            } else {
                // Clear attributes if no template selected
                attributesContainer.innerHTML = '';
            }
        });
    }
    }

    // Add attribute fields
    if (addAttributeBtn) {
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
            
            // Add event listener for lowercase conversion
            const attrNameInput = attributeGroup.querySelector('.attr-name');
            attrNameInput.addEventListener('input', function(e) {
                this.value = this.value.toLowerCase();
            });
            
            attributesContainer.appendChild(attributeGroup);
            
            // Focus on the new attribute name input
            attributeGroup.querySelector('.attr-name').focus();
            
            // Initialize delete handler for the new attribute group
            initializeDeleteHandler(attributeGroup.querySelector('.remove-attribute'));
        });
    }

    // Helper function to initialize delete button handler
    function initializeDeleteHandler(button) {
        button.addEventListener('click', function() {
            this.closest('.attribute-group').remove();
        });
    }

    // File preview
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                if (file.size > 5 * 1024 * 1024) { // 5MB limit
                    alert('File size should not exceed 5MB');
                    e.target.value = '';
                    return;
                }

                const previewContainer = input.parentElement;
                const existingPreview = previewContainer.querySelector('.preview-element');
                if (existingPreview) {
                    existingPreview.remove();
                }

                if (file.type === 'application/pdf') {
                    const pdfPreview = document.createElement('div');
                    pdfPreview.className = 'preview-element text-center p-3 bg-secondary rounded mt-2';
                    pdfPreview.innerHTML = `
                        <i class="fas fa-file-pdf fa-3x text-white"></i>
                        <div class="mt-2 text-white">${file.name}</div>
                    `;
                    previewContainer.appendChild(pdfPreview);
                } else if (file.type.startsWith('image/')) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        const preview = document.createElement('img');
                        preview.src = e.target.result;
                        preview.className = 'preview-element img-thumbnail mt-2';
                        preview.style.maxHeight = '200px';
                        previewContainer.appendChild(preview);
                    };
                    reader.readAsDataURL(file);
                }
            }
        });
    });
});