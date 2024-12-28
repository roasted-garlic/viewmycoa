document.addEventListener('DOMContentLoaded', async function() {
    const batchInput = document.getElementById('batchNumber');
    const enableBatchEdit = document.getElementById('enableBatchEdit');
    const generateBatchBtn = document.getElementById('generateBatch');
    const templateSelect = document.getElementById('template');
    const attributesContainer = document.getElementById('attributesContainer');
    const addAttributeBtn = document.getElementById('addAttribute');
    const productImage = document.getElementById('productImage');
    const labelImage = document.getElementById('labelImage');
    const coaPdf = document.getElementById('coaPdf');

    // Handle product image preview
    if (productImage) {
        productImage.addEventListener('change', function(e) {
            const file = e.target.files[0];
            const previewImg = productImage.closest('.card-body').querySelector('#productImagePreview img');
            if (file && previewImg) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    previewImg.src = e.target.result;
                    previewImg.classList.remove('d-none');
                }
                reader.readAsDataURL(file);
            } else if (previewImg) {
                previewImg.classList.add('d-none');
            }
        });
    }

    // Handle label image preview
    if (labelImage) {
        labelImage.addEventListener('change', function(e) {
            const file = e.target.files[0];
            const previewImg = labelImage.closest('.card-body').querySelector('#labelImagePreview img');
            if (file && previewImg) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    previewImg.src = e.target.result;
                    previewImg.classList.remove('d-none');
                }
                reader.readAsDataURL(file);
            } else if (previewImg) {
                previewImg.classList.add('d-none');
            }
        });
    }

    // Handle COA file preview
    if (coaPdf) {
        coaPdf.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const fileType = file.type;
                const coaPreviewContainer = document.querySelector('.card-body');

                // Remove existing preview
                const existingPreview = coaPreviewContainer.querySelector('.mb-3');
                if (existingPreview) {
                    existingPreview.remove();
                }

                // Create preview element
                const previewDiv = document.createElement('div');
                previewDiv.className = 'mb-3';

                if (fileType.startsWith('image/')) {
                    const img = document.createElement('img');
                    img.className = 'img-thumbnail mt-2';
                    img.style.maxHeight = '200px';
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        img.src = e.target.result;
                    }
                    reader.readAsDataURL(file);
                    previewDiv.appendChild(img);
                } else {
                    // PDF preview placeholder
                    previewDiv.innerHTML = `
                        <div class="text-center p-3 bg-secondary rounded">
                            <i class="fas fa-file-pdf fa-3x text-white"></i>
                            <div class="mt-2 text-white">PDF Document</div>
                        </div>`;
                }

                // Insert preview before the file input
                coaPreviewContainer.insertBefore(previewDiv, coaPdf);
            }
        });
    }

    // COA Delete functionality
    document.getElementById('confirmCoaDelete')?.addEventListener('click', async function() {
        const deleteBtn = document.querySelector('.delete-coa');
        const productId = deleteBtn.dataset.productId;

        try {
            const response = await fetch(`/api/delete_coa/${productId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                window.location.reload();
            } else {
                console.error('Failed to delete COA');
            }
        } catch (error) {
            console.error('Error:', error);
        }
    });

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
    if (enableBatchEdit && batchInput && generateBatchBtn) {
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
            if (templateId && attributesContainer) {
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
            } else if (attributesContainer) {
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
        if (!attributesContainer) return;

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
        if (attrNameInput) {
            attrNameInput.addEventListener('input', function() {
                this.value = this.value.toLowerCase();
            });
        }

        // Add event listener for remove button
        const removeBtn = attributeGroup.querySelector('.remove-attribute');
        if (removeBtn) {
            removeBtn.addEventListener('click', function() {
                attributeGroup.remove();
            });
        }

        attributesContainer.appendChild(attributeGroup);
    }

    const syncButton = document.getElementById('syncToSquareButton'); 
    const resultsDiv = document.getElementById('syncResults'); 
    if (syncButton && resultsDiv) {
        syncButton.addEventListener('click', async () => {
            syncButton.disabled = true;
            syncButton.innerHTML = '<i class="fas fa-sync fa-spin"></i> Syncing...';
            try {
                const response = await fetch('/api/sync_to_square');
                const data = await response.json();
                if (response.ok) {
                    resultsDiv.innerHTML = `<div class="alert alert-success">Successfully synced to Square!</div>`;
                } else {
                    let errorHtml = `<div class="alert alert-danger">${data.error}</div>`;
                    if (data.needs_setup) {
                        errorHtml += `
                            <div class="text-center mt-3">
                                <a href="/vmc-admin/settings" class="btn btn-primary">
                                    <i class="fas fa-cog"></i> Go to Settings
                                </a>
                            </div>`;
                    }
                    resultsDiv.innerHTML = errorHtml;
                }
            } catch (error) {
                resultsDiv.innerHTML = `<div class="alert alert-danger">An unexpected error occurred.</div>`;
                console.error('Error syncing to Square:', error);
            } finally {
                syncButton.innerHTML = '<i class="fas fa-sync"></i> Sync to Square';
                syncButton.disabled = false;
            }
        });
    }
});