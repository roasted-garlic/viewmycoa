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
    
    // Make batch number input always uppercase
    if (batchInput) {
        batchInput.addEventListener('input', function() {
            this.value = this.value.toUpperCase();
        });
    }

    if (enableBatchEdit) {
        enableBatchEdit.addEventListener('change', function() {
            batchInput.readOnly = !this.checked;
        });
    }
    
    // Barcode generation and editing
    const generateBarcodeBtn = document.getElementById('generateBarcode');
    const barcodeInput = document.getElementById('barcode');
    const enableBarcodeEdit = document.getElementById('enableBarcodeEdit');
    
    function generateBarcode() {
        // Generate a UPC-A barcode (12 digits)
        // First 11 digits are random, last digit is a check digit
        let barcode = '';
        for (let i = 0; i < 11; i++) {
            barcode += Math.floor(Math.random() * 10).toString();
        }
        
        // Calculate check digit according to UPC-A algorithm
        // Sum the odd-positioned digits (1st, 3rd, 5th, etc) and multiply by 3
        // Sum the even-positioned digits (2nd, 4th, 6th, etc)
        // Add both sums and find the digit to add to make it a multiple of 10
        let oddSum = 0;
        let evenSum = 0;
        
        for (let i = 0; i < 11; i++) {
            if (i % 2 === 0) {
                oddSum += parseInt(barcode[i]);
            } else {
                evenSum += parseInt(barcode[i]);
            }
        }
        
        const totalSum = oddSum * 3 + evenSum;
        const checkDigit = (10 - (totalSum % 10)) % 10;
        
        barcode += checkDigit;
        
        barcodeInput.value = barcode;
    }
    
    // SKU generation and editing
    const generateSkuBtn = document.getElementById('generateSku');
    const skuInput = document.getElementById('sku');
    const enableSkuEdit = document.getElementById('enableSkuEdit');
    
    function generateSku() {
        // Generate a SKU (2 uppercase letters + 6 digits)
        const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
        let sku = '';
        
        // Add 2 random uppercase letters
        for (let i = 0; i < 2; i++) {
            sku += letters.charAt(Math.floor(Math.random() * letters.length));
        }
        
        // Add 6 random digits
        for (let i = 0; i < 6; i++) {
            sku += Math.floor(Math.random() * 10).toString();
        }
        
        skuInput.value = sku;
    }
    
    if (generateSkuBtn) {
        generateSkuBtn.addEventListener('click', generateSku);
        
        // Generate SKU on page load if the field is empty
        if (!skuInput.value) {
            generateSku();
        }
    }
    
    if (enableSkuEdit) {
        enableSkuEdit.addEventListener('change', function() {
            skuInput.readOnly = !this.checked;
        });
    }
    
    // Make SKU input always uppercase
    if (skuInput) {
        skuInput.addEventListener('input', function() {
            this.value = this.value.toUpperCase();
        });
    }
    
    if (generateBarcodeBtn) {
        generateBarcodeBtn.addEventListener('click', generateBarcode);
    }
    
    if (enableBarcodeEdit) {
        enableBarcodeEdit.addEventListener('change', function() {
            barcodeInput.readOnly = !this.checked;
        });
    }
    
    // Generate barcode if empty
    if (barcodeInput && barcodeInput.value === '') {
        generateBarcode();
    }

    // Template handling
    if (templateSelect) {
        templateSelect.addEventListener('change', async function() {
            const templateId = this.value;
            if (templateId) {
                try {
                    console.log(`Fetching template with ID: ${templateId}`);
                    const response = await fetch(`/api/template/${templateId}`);
                    const data = await response.json();
                    console.log('Template data received:', data);
                    
                    if (data.attributes) {
                        // The data.attributes should already be a JavaScript object
                        // No need to parse it again unless it's a string
                        let attributes = data.attributes;
                        if (typeof attributes === 'string') {
                            try {
                                attributes = JSON.parse(attributes);
                            } catch (e) {
                                console.error('Failed to parse attributes string:', e);
                                return;
                            }
                        }
                        
                        // Clear existing attributes
                        attributesContainer.innerHTML = '';
                        
                        // Add each attribute from the template
                        Object.entries(attributes).forEach(([name, value]) => {
                            addAttributeField(name, value);
                        });
                    } else {
                        console.warn('No attributes found in template data');
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