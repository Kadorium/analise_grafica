// frontend/js/utils/ui.js

// Error handling
export function showError(message) {
    const errorModal = new bootstrap.Modal(document.getElementById('error-modal'));
    const errorMessage = document.getElementById('error-message');
    errorMessage.textContent = message;
    errorModal.show();
}

// Loading indicator
export function showLoading(elementOrMessage) {
    const spinnerHtml = `
        <div class="spinner-container">
            <div class="spinner-border text-primary spinner" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    `;
    
    // Check if a string message was passed instead of a DOM element
    if (typeof elementOrMessage === 'string') {
        // Create or get a loading container
        let loadingContainer = document.getElementById('global-loading-container');
        if (!loadingContainer) {
            loadingContainer = document.createElement('div');
            loadingContainer.id = 'global-loading-container';
            loadingContainer.className = 'alert alert-info d-flex align-items-center';
            document.body.appendChild(loadingContainer);
        }
        
        // Update the loading container with spinner and message
        loadingContainer.innerHTML = `
            <div class="spinner-border spinner-border-sm me-2" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <div>${elementOrMessage}</div>
        `;
        loadingContainer.style.display = 'flex';
    } else if (elementOrMessage && typeof elementOrMessage === 'object') {
        // It's a DOM element, set its innerHTML
        elementOrMessage.innerHTML = spinnerHtml;
    } else {
        console.error('showLoading requires either a DOM element or a message string');
    }
}

// Hide loading indicator
export function hideLoading(element) {
    if (element && typeof element === 'object') {
        // If a DOM element was passed
        element.innerHTML = '';
    } else {
        // If no element or a string was passed, hide the global loading container
        const loadingContainer = document.getElementById('global-loading-container');
        if (loadingContainer) {
            loadingContainer.style.display = 'none';
        }
    }
}

// Global loader
export function showGlobalLoader(message = 'Loading...') {
    let loaderEl = document.createElement('div');
    loaderEl.id = 'global-loader';
    loaderEl.className = 'global-loader position-fixed top-0 start-0 w-100 h-100 d-flex justify-content-center align-items-center bg-dark bg-opacity-50';
    loaderEl.style.zIndex = '9999';
    loaderEl.innerHTML = `
        <div class="bg-white p-3 rounded">
            <div class="d-flex align-items-center">
                <div class="spinner-border text-primary me-3"></div>
                <span>${message}</span>
            </div>
        </div>
    `;
    document.body.appendChild(loaderEl);
}

export function hideGlobalLoader() {
    const loader = document.getElementById('global-loader');
    if (loader) {
        loader.remove();
    }
}

// Success message
export function showSuccessMessage(message) {
    const successDiv = document.createElement('div');
    successDiv.className = 'alert alert-success alert-dismissible fade show mt-3';
    successDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Find a good place to show the message
    const currentSection = document.querySelector('.content-section.active');
    if (currentSection) {
        currentSection.appendChild(successDiv);
        
        // Remove the message after 5 seconds
        setTimeout(() => {
            successDiv.remove();
        }, 5000);
    }
}

// Notification
export function showNotification(message, type = 'info') {
    // Create a Bootstrap alert
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add to the current active section
    const currentSection = document.querySelector('.content-section.active');
    if (currentSection) {
        currentSection.prepend(alertDiv);
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }
}

// Tab navigation
export function activateTab(tabElement) {
    // Get the target section ID from the tab's href or data-bs-target attribute
    const targetId = tabElement.getAttribute('href') || tabElement.dataset.bsTarget;
    if (!targetId) return;
    
    // Remove the leading # to get the actual ID
    const sectionId = targetId.replace('#', '');
    
    // Find the section element
    const sectionElement = document.getElementById(sectionId);
    if (!sectionElement) return;
    
    // Get the section title (can be customized based on your needs)
    const title = tabElement.textContent.trim();
    
    // DOM elements for all tabs and sections
    const tabs = document.querySelectorAll('.nav-link');
    const sections = document.querySelectorAll('.content-section');
    
    // Deactivate all tabs and hide all sections
    tabs.forEach(t => t.classList.remove('active'));
    sections.forEach(s => s.classList.remove('active'));
    
    // Activate the selected tab and show the corresponding section
    tabElement.classList.add('active');
    sectionElement.classList.add('active');
    
    // Update page title if available
    const pageTitle = document.getElementById('page-title');
    if (pageTitle) pageTitle.textContent = title;
    
    // Save the active tab to session storage to persist across page reloads
    sessionStorage.setItem('activeTab', tabElement.id);
}

// Update progress bar
export function updateProgressBar(percentage) {
    const loader = document.querySelector('.global-loader');
    if (!loader) return;
    
    const progressBar = loader.querySelector('.progress-bar');
    if (!progressBar) return;
    
    // Update the progress bar width and text
    progressBar.style.width = `${percentage}%`;
    progressBar.setAttribute('aria-valuenow', percentage);
    progressBar.textContent = `${percentage}%`;
    
    // Change color based on progress
    if (percentage < 30) {
        progressBar.classList.remove('bg-success', 'bg-warning');
        progressBar.classList.add('bg-primary');
    } else if (percentage < 70) {
        progressBar.classList.remove('bg-primary', 'bg-success');
        progressBar.classList.add('bg-warning');
    } else {
        progressBar.classList.remove('bg-primary', 'bg-warning');
        progressBar.classList.add('bg-success');
    }
}
