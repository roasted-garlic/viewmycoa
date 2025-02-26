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

    // Generate initial batch number if empty
    if (batchInput && batchInput.value === '') {
        generateBatchNumber();
    }

    // Batch number generation
    if (generateBatchBtn) {
        generateBatchBtn.addEventListener('click', generateBatchNumber);
    }

    if (enableBatchEdit) {
        enableBatchEdit.addEventListener('change', function() {
            batchInput.readOnly = !this.checked;
        });
    }

    // Template handling
    if (templateSelect) {
        templateSelect.addEventListener('change', async function() {
            const templateId = this.value;
            if (templateId) {
                const response = await fetch(`/api/template/${templateId}`);
                const template = await response.json();

                // Clear existing attributes
                attributesContainer.innerHTML = '';

                // Add template attributes
                Object.entries(template.attributes).forEach(([name, value]) => {
                    addAttributeField(name, value);
                });
            }
        });
    }

    // Function to generate batch number
    async function generateBatchNumber() {
        const response = await fetch('/api/generate_batch', {
            method: 'POST'
        });
        const data = await response.json();
        if (batchInput) {
            batchInput.value = data.batch_number;
        }
    }

    // Function to add attribute field
    function addAttributeField(name = '', value = '') {
        const attributeDiv = document.createElement('div');
        attributeDiv.className = 'row mb-2';
        attributeDiv.innerHTML = `
            <div class="col-5">
                <input type="text" class="form-control" name="attr_name[]" value="${name}" placeholder="Name">
            </div>
            <div class="col-5">
                <input type="text" class="form-control" name="attr_value[]" value="${value}" placeholder="Value">
            </div>
            <div class="col-2">
                <button type="button" class="btn btn-danger remove-attribute">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `;

        attributeDiv.querySelector('.remove-attribute').addEventListener('click', function() {
            attributeDiv.remove();
        });

        attributesContainer.appendChild(attributeDiv);
    }

    // Create preview containers if they don't exist
    function ensurePreviewContainer(input, previewId) {
        const cardBody = input.closest('.card-body');
        let previewContainer = cardBody.querySelector(`#${previewId}`);
        if (!previewContainer) {
            previewContainer = document.createElement('div');
            previewContainer.id = previewId;
            input.insertAdjacentElement('beforebegin', previewContainer);
        }
        return previewContainer;
    }

    // Initialize preview containers
    if (productImage) {
        const container = ensurePreviewContainer(productImage, 'productImagePreview');
        const existingImg = productImage.closest('.card-body').querySelector('img.img-thumbnail');
        if (existingImg) {
            container.appendChild(existingImg);
        }
    }

    if (labelImage) {
        const container = ensurePreviewContainer(labelImage, 'labelImagePreview');
        const existingImg = labelImage.closest('.card-body').querySelector('img.img-thumbnail');
        if (existingImg) {
            container.appendChild(existingImg);
        }
    }

    // Function to handle image preview
    function handleImagePreview(input, previewSelector) {
        const file = input.files[0];
        const previewContainer = input.closest('.card-body').querySelector(previewSelector);
        const previewImg = previewContainer?.querySelector('img');

        if (file && previewContainer) {
            if (!previewImg) {
                const img = document.createElement('img');
                img.className = 'img-thumbnail mb-3';
                img.style.maxHeight = '200px';
                previewContainer.appendChild(img);
            }

            const reader = new FileReader();
            reader.onload = function(e) {
                const img = previewContainer.querySelector('img');
                img.src = e.target.result;
                img.classList.remove('d-none');
                previewContainer.classList.remove('d-none');
            }
            reader.readAsDataURL(file);
        }
    }

    // Handle product image preview
    if (productImage) {
        productImage.addEventListener('change', function() {
            handleImagePreview(this, '#productImagePreview');
        });
    }

    // Handle label image preview
    if (labelImage) {
        labelImage.addEventListener('change', function() {
            handleImagePreview(this, '#labelImagePreview');
        });
    }

    // Handle COA file preview
    if (coaPdf) {
        coaPdf.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const fileType = file.type;
                const previewContainer = this.closest('.card-body');
                const existingPreview = previewContainer.querySelector('.preview-container');

                if (existingPreview) {
                    existingPreview.remove();
                }

                const previewDiv = document.createElement('div');
                previewDiv.className = 'preview-container mb-3';

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
                    previewDiv.innerHTML = `
                        <div class="text-center p-3 bg-secondary rounded">
                            <i class="fas fa-file-pdf fa-3x text-white"></i>
                            <div class="mt-2 text-white">PDF Document</div>
                        </div>`;
                }

                previewContainer.insertBefore(previewDiv, this);
            }
        });
    }

    // Handle batch number functionality
    if (generateBatchBtn) {
        generateBatchBtn.addEventListener('click', async function() {
            try {
                const response = await fetch('/api/generate_batch');
                const data = await response.json();
                if (batchInput) {
                    batchInput.value = data.batch_number;
                }
            } catch (error) {
                console.error('Error generating batch number:', error);
            }
        });
    }

    if (enableBatchEdit) {
        enableBatchEdit.addEventListener('change', function() {
            if (batchInput) {
                batchInput.readOnly = !this.checked;
            }
        });
    }

    // Handle template selection
    if (templateSelect) {
        templateSelect.addEventListener('change', async function() {
            const templateId = this.value;
            if (templateId) {
                try {
                    const response = await fetch(`/api/template/${templateId}`);
                    const data = await response.json();
                    if (data.attributes) {
                        const attributes = JSON.parse(data.attributes);
                        attributesContainer.innerHTML = '';
                        Object.entries(attributes).forEach(([name, value]) => {
                            addAttributeField(name, value);
                        });
                    }
                } catch (error) {
                    console.error('Error fetching template:', error);
                }
            }
        });
    }

    // Handle attribute addition
    if (addAttributeBtn) {
        addAttributeBtn.addEventListener('click', function() {
            addAttributeField();
        });
    }

    function addAttributeField(name = '', value = '') {
        const attributeGroup = document.createElement('div');
        attributeGroup.className = 'attribute-group mb-2';
        attributeGroup.innerHTML = `
            <div class="row">
                <div class="col">
                    <input type="text" class="form-control" name="attr_name[]" value="${name}" required>
                </div>
                <div class="col">
                    <input type="text" class="form-control" name="attr_value[]" value="${value}" required>
                </div>
                <div class="col-auto">
                    <button type="button" class="btn btn-danger remove-attribute">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>`;

        attributeGroup.querySelector('.remove-attribute').addEventListener('click', function() {
            attributeGroup.remove();
            // Automatically submit the form to save changes
            document.getElementById('productForm').submit();
        });

        attributesContainer.appendChild(attributeGroup);
    }

    // Handle COA deletion
    document.getElementById('confirmCoaDelete')?.addEventListener('click', async function() {
        const deleteBtn = document.querySelector('.delete-coa');
        const productId = deleteBtn.dataset.productId;

        try {
            const response = await fetch(`/api/delete_coa/${productId}`, {
                method: 'DELETE'
            });
            if (response.ok) {
                window.location.reload();
            }
        } catch (error) {
            console.error('Error:', error);
        }
    });
});