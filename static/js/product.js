document.addEventListener('DOMContentLoaded', function() {
    const generateBatchBtn = document.getElementById('generateBatch');
    const addAttributeBtn = document.getElementById('addAttribute');
    const attributesContainer = document.getElementById('attributesContainer');

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

        // Generate initial batch number
        generateBatchBtn.click();
    }

    // Add attribute fields
    if (addAttributeBtn) {
        addAttributeBtn.addEventListener('click', function() {
            const attributeGroup = document.createElement('div');
            attributeGroup.className = 'attribute-group mb-2';
            
            attributeGroup.innerHTML = `
                <div class="row">
                    <div class="col">
                        <input type="text" class="form-control" name="attr_name[]" placeholder="Attribute Name" required>
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
            
            attributesContainer.appendChild(attributeGroup);
            
            // Add remove button handler
            attributeGroup.querySelector('.remove-attribute').addEventListener('click', function() {
                attributeGroup.remove();
            });
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
