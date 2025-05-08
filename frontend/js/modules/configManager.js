// frontend/js/modules/configManager.js

// Import dependencies
import { fetchCurrentConfig as fetchAppConfig, saveConfig as saveAppConfig } from '../utils/api.js';
import { showError, showLoading, showSuccessMessage, showGlobalLoader, hideGlobalLoader } from '../utils/ui.js';
import { appState } from '../utils/state.js';

// DOM references
const configForm = document.getElementById('config-form');
const configContainer = document.getElementById('config-container');
const resetConfigBtn = document.getElementById('reset-config-btn');

// Fetch current config
export async function fetchCurrentConfig() {
    try {
        // Only try to show loading if the container exists
        if (configContainer) {
            showLoading(configContainer);
        } else {
            console.warn('Config container element not found in the DOM');
        }
        
        // Fetch config
        const response = await fetchAppConfig();
        
        if (response.config) {
            // Store in state
            appState.setAppConfig(response.config);
            
            // Build form
            buildConfigForm(response.config);
            
            return response.config;
        } else {
            throw new Error('No configuration available');
        }
    } catch (error) {
        showError(error.message || 'Failed to fetch configuration');
        console.error('Error fetching config:', error);
        return null;
    }
}

// Build config form
function buildConfigForm(config) {
    if (!configContainer || !config) return;
    
    // Clear existing form
    configContainer.innerHTML = '';
    
    // Create form sections
    Object.entries(config).forEach(([sectionName, sectionConfig]) => {
        const sectionCard = document.createElement('div');
        sectionCard.className = 'card mb-4';
        
        // Create card header
        const cardHeader = document.createElement('div');
        cardHeader.className = 'card-header bg-light';
        cardHeader.innerHTML = `<h5 class="mb-0">${formatSectionName(sectionName)}</h5>`;
        
        // Create card body
        const cardBody = document.createElement('div');
        cardBody.className = 'card-body';
        
        // Add config fields
        Object.entries(sectionConfig).forEach(([fieldName, fieldValue]) => {
            const formGroup = createConfigField(sectionName, fieldName, fieldValue);
            cardBody.appendChild(formGroup);
        });
        
        // Assemble card
        sectionCard.appendChild(cardHeader);
        sectionCard.appendChild(cardBody);
        configContainer.appendChild(sectionCard);
    });
}

// Create config field
function createConfigField(sectionName, fieldName, fieldValue) {
    const formGroup = document.createElement('div');
    formGroup.className = 'mb-3';
    
    // Create label
    const label = document.createElement('label');
    label.className = 'form-label';
    label.textContent = formatFieldName(fieldName);
    
    // Create input element based on type
    let input;
    const fieldId = `config-${sectionName}-${fieldName}`;
    const fieldPath = `${sectionName}.${fieldName}`;
    
    if (typeof fieldValue === 'boolean') {
        // Boolean - checkbox
        const checkboxDiv = document.createElement('div');
        checkboxDiv.className = 'form-check';
        
        input = document.createElement('input');
        input.type = 'checkbox';
        input.className = 'form-check-input';
        input.id = fieldId;
        input.name = fieldPath;
        input.checked = fieldValue;
        
        label.className = 'form-check-label';
        
        checkboxDiv.appendChild(input);
        checkboxDiv.appendChild(label);
        
        return checkboxDiv;
    } else if (typeof fieldValue === 'number') {
        // Number - number input
        input = document.createElement('input');
        input.type = 'number';
        input.className = 'form-control';
        input.id = fieldId;
        input.name = fieldPath;
        input.value = fieldValue;
        
        // Add step attribute for decimal numbers
        if (fieldValue % 1 !== 0) {
            input.step = '0.01';
        }
    } else if (Array.isArray(fieldValue)) {
        // Array - select multiple
        input = document.createElement('select');
        input.className = 'form-select';
        input.id = fieldId;
        input.name = fieldPath;
        input.multiple = true;
        
        // Add options
        fieldValue.forEach(option => {
            const optionEl = document.createElement('option');
            optionEl.value = option;
            optionEl.textContent = option;
            optionEl.selected = true;
            input.appendChild(optionEl);
        });
        
        // Helper text
        const helpText = document.createElement('div');
        helpText.className = 'form-text';
        helpText.textContent = 'Hold Ctrl/Cmd to select multiple options';
        formGroup.appendChild(helpText);
    } else {
        // String or other - text input
        input = document.createElement('input');
        input.type = 'text';
        input.className = 'form-control';
        input.id = fieldId;
        input.name = fieldPath;
        input.value = fieldValue || '';
    }
    
    // Regular input group
    formGroup.appendChild(label);
    formGroup.appendChild(input);
    
    return formGroup;
}

// Format section name
function formatSectionName(name) {
    return name.split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

// Format field name
function formatFieldName(name) {
    return name.split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

// Save config
async function saveConfig(config) {
    try {
        showGlobalLoader('Saving configuration...');
        
        // Save config
        const response = await saveAppConfig(config);
        
        if (response.success) {
            showSuccessMessage('Configuration saved successfully');
            
            // Update state
            appState.setAppConfig(config);
            
            return true;
        } else {
            throw new Error(response.error || 'Error saving configuration');
        }
    } catch (error) {
        showError(error.message || 'Failed to save configuration');
        return false;
    } finally {
        hideGlobalLoader();
    }
}

// Reset config
async function resetConfig() {
    if (!confirm('Are you sure you want to reset to default configuration? This action cannot be undone.')) {
        return false;
    }
    
    try {
        showGlobalLoader('Resetting configuration...');
        
        // Use a direct fetch with DELETE method to reset config
        const response = await fetch('/api/current-config', {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || `Error: ${response.status}`);
        }
        
        const resultData = await response.json();
        
        if (resultData.success) {
            showSuccessMessage('Configuration reset to defaults');
            
            // Fetch new config
            await fetchCurrentConfig();
            
            return true;
        } else {
            throw new Error(resultData.error || 'Error resetting configuration');
        }
    } catch (error) {
        showError(error.message || 'Failed to reset configuration');
        return false;
    } finally {
        hideGlobalLoader();
    }
}

// Extract config from form
function extractConfigFromForm(form) {
    const formData = new FormData(form);
    const config = {};
    
    // Process form data
    for (const [fieldPath, value] of formData.entries()) {
        // Split path into section and field
        const [section, field] = fieldPath.split('.');
        
        // Initialize section if needed
        if (!config[section]) {
            config[section] = {};
        }
        
        // Convert value based on input type
        const input = form.querySelector(`[name="${fieldPath}"]`);
        let processedValue = value;
        
        if (input.type === 'checkbox') {
            // Boolean checkbox
            processedValue = input.checked;
        } else if (input.type === 'number') {
            // Number input
            processedValue = parseFloat(value);
        } else if (input.multiple) {
            // Multi-select
            processedValue = Array.from(input.selectedOptions).map(opt => opt.value);
        }
        
        // Add to config
        config[section][field] = processedValue;
    }
    
    return config;
}

// Initialize config manager
export function initializeConfigManager() {
    // Check if the config container exists before initializing
    if (!configContainer) {
        console.warn('Config container element not found, skipping config initialization');
        return;
    }

    // Fetch initial config
    fetchCurrentConfig();
    
    // Add form submit handler
    if (configForm) {
        configForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            // Extract config from form
            const config = extractConfigFromForm(configForm);
            
            // Save config
            await saveConfig(config);
        });
    }
    
    // Add reset button handler
    if (resetConfigBtn) {
        resetConfigBtn.addEventListener('click', async () => {
            await resetConfig();
        });
    }
}
