import { Parameter } from '../utils/parameterModel.js';

export class OptimizationParamTable {
    constructor(container, parameters) {
        this.container = container;
        this.parameters = parameters; // Array of Parameter objects
        this.state = {}; // { paramId: { optimize: bool, min, max, step, values, ... } }
        this.render();
    }

    render() {
        this.container.innerHTML = '';
        const table = document.createElement('table');
        table.className = 'table table-bordered table-sm';

        // Table header
        const thead = document.createElement('thead');
        thead.innerHTML = `
            <tr>
                <th>Optimize?</th>
                <th>Parameter</th>
                <th>Type</th>
                <th>Min</th>
                <th>Max</th>
                <th>Step</th>
                <th>Options</th>
                <th>Default</th>
            </tr>
        `;
        table.appendChild(thead);

        // Table body
        const tbody = document.createElement('tbody');
        this.parameters.forEach(param => {
            // Set default step value based on parameter type and min value
            let stepValue = '';
            if (param.type === 'number') {
                // For numbers, use the smaller of: 1, min value (if positive), or 0.1
                if (param.min !== null && param.min !== undefined && !isNaN(param.min)) {
                    if (param.min > 0 && param.min < 1) {
                        stepValue = 0.1; // Small step for decimal values
                    } else if (param.min > 0) {
                        stepValue = Math.min(1, param.min); // Smaller of 1 or min value
                    } else {
                        stepValue = 1; // Default to 1 for zero or negative min values
                    }
                } else {
                    stepValue = 1; // Default step if no min specified
                }
                
                // Use specified step value if it's valid
                if (param.step !== null && param.step !== undefined && !isNaN(param.step) && param.step > 0) {
                    stepValue = param.step;
                }
            }
            
            const row = document.createElement('tr');
            row.innerHTML = `
                <td class="text-center"><input type="checkbox" class="opt-checkbox" data-id="${param.id}"></td>
                <td>${param.label}</td>
                <td>${param.type}</td>
                <td><input type="number" class="form-control form-control-sm min-input" data-id="${param.id}" value="${param.min ?? ''}" ${param.type !== 'number' ? 'disabled' : ''}></td>
                <td><input type="number" class="form-control form-control-sm max-input" data-id="${param.id}" value="${param.max ?? ''}" ${param.type !== 'number' ? 'disabled' : ''}></td>
                <td><input type="number" class="form-control form-control-sm step-input" data-id="${param.id}" value="${stepValue}" min="0.000001" step="0.000001" ${param.type !== 'number' ? 'disabled' : ''}></td>
                <td>${param.type === 'select' && param.options ? param.options.map(opt => `<div class="form-check"><input type="checkbox" class="form-check-input opt-option" data-id="${param.id}" value="${opt.value}"><label class="form-check-label">${opt.label}</label></div>`).join('') : ''}</td>
                <td>${param.defaultValue ?? ''}</td>
            `;
            tbody.appendChild(row);
        });
        table.appendChild(tbody);

        // Create responsive wrapper
        const wrapper = document.createElement('div');
        wrapper.className = 'table-responsive';
        wrapper.appendChild(table);
        this.container.appendChild(wrapper);

        // Attach event listeners to update state
        this.attachListeners();
    }

    attachListeners() {
        // Checkbox for optimize
        this.container.querySelectorAll('.opt-checkbox').forEach(cb => {
            cb.addEventListener('change', () => this.updateState());
        });
        
        // Min/max/step inputs
        this.container.querySelectorAll('.min-input, .max-input').forEach(input => {
            input.addEventListener('input', () => this.updateState());
        });
        
        // Step input handling to prevent zero or negative values
        this.container.querySelectorAll('.step-input').forEach(input => {
            input.addEventListener('input', (e) => {
                const value = parseFloat(e.target.value);
                // Ensure step is never zero or negative
                if (isNaN(value) || value <= 0) {
                    e.target.value = 0.000001; // Set to very small positive number instead of zero
                }
                this.updateState();
            });
        });
        
        // Option checkboxes
        this.container.querySelectorAll('.opt-option').forEach(cb => {
            cb.addEventListener('change', () => this.updateState());
        });
    }

    updateState() {
        console.log('[DEBUG] updateState called');
        this.state = {};
        this.parameters.forEach(param => {
            console.log(`[DEBUG] Processing param: ${param.id}`); // Log param ID
            const checkboxEl = this.container.querySelector(`.opt-checkbox[data-id="${param.id}"]`);
            console.log(`[DEBUG] Checkbox for ${param.id}:`, checkboxEl ? checkboxEl.checked : 'Not found'); // Log checkbox status
            if (!checkboxEl || !checkboxEl.checked) return;
            
            if (param.type === 'number') {
                const minEl = this.container.querySelector(`.min-input[data-id="${param.id}"]`);
                const maxEl = this.container.querySelector(`.max-input[data-id="${param.id}"]`);
                const stepEl = this.container.querySelector(`.step-input[data-id="${param.id}"]`);
                
                let min = parseFloat(minEl.value);
                let max = parseFloat(maxEl.value);
                let step = parseFloat(stepEl.value);
                
                // Log values read for this param
                console.log(`[DEBUG] Values read for ${param.id}: min=${min}, max=${max}, step=${step}`);
                
                // Validate values
                if (isNaN(min) || isNaN(max) || isNaN(step)) {
                    console.warn(`Invalid min/max/step values for parameter ${param.id}`);
                    return;
                }
                
                // Ensure step is positive
                if (step <= 0) {
                    step = 0.000001;
                    stepEl.value = step;
                }
                
                this.state[param.id] = { min, max, step };
            } else if (param.type === 'select') {
                const selected = Array.from(this.container.querySelectorAll(`.opt-option[data-id="${param.id}"]:checked`)).map(cb => cb.value);
                this.state[param.id] = selected;
            } else if (param.type === 'bool') {
                this.state[param.id] = [true, false];
            }
        });
        console.log('[DEBUG] Final state object:', this.state); // Log final state object
    }

    // Returns param_ranges in the backend-expected format
    getParamRanges() {
        console.log('[DEBUG] getParamRanges called');
        const paramRanges = {};
        for (const [paramId, val] of Object.entries(this.state)) {
            console.log(`[DEBUG] Processing state entry: paramId=${paramId}, val=`, val); // Log state entry being processed
            if (Array.isArray(val) && val.length > 0) {
                paramRanges[paramId] = val;
            } else if (
                typeof val === 'object' &&
                val.min !== undefined && val.max !== undefined && val.step !== undefined &&
                !isNaN(val.min) && !isNaN(val.max) && !isNaN(val.step) && val.step > 0
            ) {
                const arr = [];
                for (let v = val.min; v <= val.max; v += val.step) {
                    arr.push(Number(v.toFixed(8)));
                }
                if (arr.length > 0) {
                    paramRanges[paramId] = arr;
                }
            } else if (val === true || val === false) {
                paramRanges[paramId] = [true, false];
            }
        }
        console.log('[DEBUG] Final paramRanges object:', paramRanges); // Log final paramRanges object
        return paramRanges;
    }
} 