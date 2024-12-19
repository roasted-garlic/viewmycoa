
document.addEventListener('DOMContentLoaded', function() {
    const addAttributeBtn = document.getElementById('addAttribute');
    const attributesContainer = document.getElementById('attributesContainer');
    const templateForm = document.getElementById('templateForm');

    // Initialize delete handlers for existing attributes
    document.querySelectorAll('.remove-attribute').forEach(button => {
        initializeDeleteHandler(button);
    });

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
                        <input type="text" class="form-control" name="attr_value[]" placeholder="Default Value (Optional)">
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

    // Form submission handler
    if (templateForm) {
        templateForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            const attributes = {};
            
            // Get all attribute names and values
            const names = formData.getAll('attr_name[]');
            const values = formData.getAll('attr_value[]');
            
            // Create attributes object with optional values
            names.forEach((name, index) => {
                if (name) {
                    attributes[name] = values[index] || '';
                }
            });
            
            // Add attributes to form data
            formData.append('attributes', JSON.stringify(attributes));
            
            // Submit the form
            this.submit();
        });
    }
});
