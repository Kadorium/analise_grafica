// Debug script for checking the upload and process button
document.addEventListener('DOMContentLoaded', function() {
    console.log('Debug script loaded');
    
    // Check if the button exists
    const uploadProcessBtn = document.getElementById('upload-process-btn');
    console.log('Upload & Process button:', uploadProcessBtn);
    
    if (uploadProcessBtn) {
        console.log('Upload & Process button found, adding test event listener');
        uploadProcessBtn.addEventListener('click', function(e) {
            console.log('Upload & Process button clicked');
            // Don't prevent default to see if the original handler works
        });
    } else {
        console.error('Upload & Process button not found!');
    }
    
    // Check if the form exists
    const uploadForm = document.getElementById('upload-form');
    console.log('Upload form:', uploadForm);
    
    if (uploadForm) {
        console.log('Upload form found, adding test event listener');
        uploadForm.addEventListener('submit', function(e) {
            console.log('Form submit event triggered');
            // Don't prevent default to see if the original handler works
        });
    } else {
        console.error('Upload form not found!');
    }
}); 