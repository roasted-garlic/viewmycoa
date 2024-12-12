document.addEventListener('DOMContentLoaded', function() {
    const addAttributeBtn = document.getElementById('addAttribute');
    const attributesContainer = document.getElementById('attributesContainer');

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
});
