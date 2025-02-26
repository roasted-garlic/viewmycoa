document.addEventListener('DOMContentLoaded', function() {
    const batchInput = document.getElementById('batchNumber');
    const enableBatchEdit = document.getElementById('enableBatchEdit');
    const generateBatchBtn = document.getElementById('generateBatch');
    const templateSelect = document.getElementById('template');
    const attributesContainer = document.getElementById('attributesContainer');
    const addAttributeBtn = document.getElementById('addAttribute');
    const productImage = document.getElementById('productImage');
    const labelImage = document.getElementById('labelImage');
    const coaPdf = document.getElementById('coaPdf');
    const productForm = document.getElementById('productForm');
    
    // Initialize delete buttons for existing attributes
    initializeAttributeButtons();
    
    // Function to add event listeners to all attribute delete buttons
    function initializeAttributeButtons() {
        // Remove any existing event listeners to prevent duplicates
        document.querySelectorAll('.remove-attribute').forEach(button => {
            // Clone and replace the button to remove all event listeners
            const newButton = button.cloneNode(true);
            button.parentNode.replaceChild(newButton, button);
            
            // Add fresh event listener
            newButton.addEventListener('click', function() {
                const attributeGroup = this.closest('.attribute-group');
                if (attributeGroup) {
                    attributeGroup.remove();
                }
            });
        });
    }
    
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

    // Function to generate batch number
    async function generateBatchNumber() {
        try {
            const response = await fetch('/api/generate_batch', {
                method: 'POST'
            });
            const data = await response.json();
            if (batchInput) {
                batchInput.value = data.batch_number;
            }
        } catch (error) {
            console.error('Error generating batch number:', error);
        }
    }

    // Function to add attribute field
    function addAttributeField(name = '', value = '') {
        const attributeDiv = document.createElement('div');
        attributeDiv.className = 'attribute-group mb-2';
        attributeDiv.innerHTML = `
            <div class="row">
                <div class="col">
                    <input type="text" class="form-control" name="attr_name[]" value="${name}" placeholder="Name" required>
                </div>
                <div class="col">
                    <input type="text" class="form-control" name="attr_value[]" value="${value}" placeholder="Value" required>
                </div>
                <div class="col-auto">
                    <button type="button" class="btn btn-danger remove-attribute">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;

        attributesContainer.appendChild(attributeDiv);
        
        // Initialize the new button
        initializeAttributeButtons();
    }

    // Create preview containers if they don't exist
    function ensurePreviewContainer(input, previewId) {
        if (!input) return null;
        const cardBody = input.closest('.card-body');
        if (!cardBody) return null;
        
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
        if (container) {
            const existingImg = productImage.closest('.card-body').querySelector('img.img-thumbnail');
            if (existingImg) {
                container.appendChild(existingImg);
            }
        }
    }

    if (labelImage) {
        const container = ensurePreviewContainer(labelImage, 'labelImagePreview');
        if (container) {
            const existingImg = labelImage.closest('.card-body').querySelector('img.img-thumbnail');
            if (existingImg) {
                container.appendChild(existingImg);
            }
        }
    }

    // Function to handle image preview
    function handleImagePreview(input, previewSelector) {
        const file = input.files[0];
        const previewContainer = input.closest('.card-body')?.querySelector(previewSelector);
        if (!previewContainer) return;
        
        const previewImg = previewContainer.querySelector('img');

        if (file) {
            if (!previewImg) {
                const img = document.createElement('img');
                img.className = 'img-thumbnail mb-3';
                img.style.maxHeight = '200px';
                previewContainer.appendChild(img);
            }

            const reader = new FileReader();
            reader.onload = function(e) {
                const img = previewContainer.querySelector('img');
                if (img) {
                    img.src = e.target.result;
                    img.classList.remove('d-none');
                    previewContainer.classList.remove('d-none');
                }
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
                if (!previewContainer) return;
                
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

    // Handle attribute addition
    if (addAttributeBtn) {
        addAttributeBtn.addEventListener('click', function() {
            addAttributeField();
        });
    }

    // Handle COA deletion
    const confirmCoaDelete = document.getElementById('confirmCoaDelete');
    if (confirmCoaDelete) {
        confirmCoaDelete.addEventListener('click', async function() {
            const deleteBtn = document.querySelector('.delete-coa');
            if (!deleteBtn) return;
            
            const productId = deleteBtn.dataset.productId;
            if (!productId) return;

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
    }

    // Ensure form properly collects all attributes when submitting
    if (productForm) {
        productForm.addEventListener('submit', function() {
            // No need to add a hidden field - the server can process the attr_name[] and attr_value[] 
            // arrays directly, which is already how the form is set up
        });
    }
});