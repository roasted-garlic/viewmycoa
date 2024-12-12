document.addEventListener('DOMContentLoaded', function() {
// Template handling
document.addEventListener('DOMContentLoaded', function() {
    const templateSelect = document.getElementById('template');
    if (templateSelect) {
        templateSelect.addEventListener('change', async function() {
            const templateId = this.value;
            if (templateId) {
                try {
                    const response = await fetch(`/api/template/${templateId}`);
                    if (response.ok) {
                        const template = await response.json();
                        // Clear existing attributes
                        const attributesContainer = document.getElementById('attributesContainer');
                        attributesContainer.innerHTML = '';
                        
                        // Add template attributes
                        Object.entries(template.attributes).forEach(([name, value]) => {
                            const attrBtn = document.getElementById('addAttribute');
                            attrBtn.click(); // Create new attribute group
                            
                            // Fill in the last added group
                            const groups = document.querySelectorAll('.attribute-group');
                            const lastGroup = groups[groups.length - 1];
                            lastGroup.querySelector('[name="attr_name[]"]').value = name;
                            lastGroup.querySelector('[name="attr_value[]"]').value = value;
                        });
                    }
                } catch (error) {
                    console.error('Error loading template:', error);
                    showNotification('Error loading template', 'danger');
                }
            }
        });
    }
});

    const generateBatchBtn = document.getElementById('generateBatch');
    const addAttributeBtn = document.getElementById('addAttribute');
    const attributesContainer = document.getElementById('attributesContainer');

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

    // Image preview
    const imageInputs = document.querySelectorAll('input[type="file"]');
    imageInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                if (file.size > 5 * 1024 * 1024) { // 5MB limit
                    alert('File size should not exceed 5MB');
                    e.target.value = '';
                    return;
                }

                const reader = new FileReader();
                reader.onload = function(e) {
                    const preview = document.createElement('img');
                    preview.src = e.target.result;
                    preview.className = 'img-thumbnail mt-2';
                    preview.style.maxHeight = '200px';
                    
                    const previewContainer = input.parentElement;
                    const existingPreview = previewContainer.querySelector('img');
                    if (existingPreview) {
                        existingPreview.remove();
                    }
                    previewContainer.appendChild(preview);
                };
                reader.readAsDataURL(file);
            }
        });
    });
});