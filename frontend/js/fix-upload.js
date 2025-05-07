// Simple fix script to handle the upload form
document.addEventListener('DOMContentLoaded', function() {
    console.log('Fix script loaded');
    
    // Wait a bit to ensure all the other scripts have loaded and run
    setTimeout(function() {
        // Get the elements we need
        const uploadForm = document.getElementById('upload-form');
        const csvFileInput = document.getElementById('csv-file');
        const uploadProcessBtn = document.getElementById('upload-process-btn');
        const dataInfo = document.getElementById('data-info');
        const dataPreview = document.getElementById('data-preview');
        
        console.log('Form:', uploadForm, 'Button:', uploadProcessBtn);
        
        // Check if form and button exist
        if (uploadForm && uploadProcessBtn) {
            console.log('Adding event listener to form');
            
            // Remove any existing event listeners (there might be multiple bindings)
            const newForm = uploadForm.cloneNode(true);
            uploadForm.parentNode.replaceChild(newForm, uploadForm);
            
            // Get the new button reference after cloning
            const newUploadProcessBtn = document.getElementById('upload-process-btn');
            
            // Add a new event listener to the form
            newForm.addEventListener('submit', async function(e) {
                e.preventDefault();
                console.log('Form submitted');
                
                const fileInput = document.getElementById('csv-file');
                if (!fileInput.files.length) {
                    alert('Please select a CSV file to upload.');
                    return;
                }
                
                try {
                    // Disable the button and show loading
                    newUploadProcessBtn.disabled = true;
                    newUploadProcessBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Uploading...';
                    
                    // Create form data and append the file
                    const formData = new FormData();
                    formData.append('file', fileInput.files[0]);
                    
                    // First upload the file
                    console.log('Uploading file...');
                    const uploadResponse = await fetch('/api/upload', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (!uploadResponse.ok) {
                        throw new Error('Upload failed: ' + uploadResponse.statusText);
                    }
                    
                    const uploadData = await uploadResponse.json();
                    console.log('Upload succeeded:', uploadData);
                    
                    // Then process the data
                    newUploadProcessBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
                    console.log('Processing data...');
                    
                    const processResponse = await fetch('/api/process-data', {
                        method: 'POST'
                    });
                    
                    if (!processResponse.ok) {
                        throw new Error('Processing failed: ' + processResponse.statusText);
                    }
                    
                    const processData = await processResponse.json();
                    console.log('Processing succeeded:', processData);
                    
                    // Show success message
                    const successMsg = document.createElement('div');
                    successMsg.className = 'alert alert-success mt-2';
                    successMsg.textContent = 'Data uploaded and processed successfully!';
                    dataInfo.appendChild(successMsg);
                    
                    // Set session storage
                    sessionStorage.setItem('dataUploaded', 'true');
                    sessionStorage.setItem('dataProcessed', 'true');
                    
                    // Reload the page to ensure all state is consistent
                    setTimeout(function() {
                        window.location.reload();
                    }, 1500);
                    
                } catch (error) {
                    console.error('Error:', error);
                    alert('Error: ' + error.message);
                } finally {
                    // Re-enable the button
                    newUploadProcessBtn.disabled = false;
                    newUploadProcessBtn.textContent = 'Upload & Process';
                }
            });
            
            console.log('Event listener added');
        } else {
            console.error('Form or button not found');
        }
    }, 500);
}); 