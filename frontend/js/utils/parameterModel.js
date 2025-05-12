export class Parameter {
    constructor({
        id,
        label,
        type = 'number', // 'number', 'select', 'bool'
        defaultValue = null,
        min = null,
        max = null,
        step = null,
        options = null, // for select
        constraints = null // for advanced use
    }) {
        this.id = id;
        this.label = label;
        this.type = type;
        this.defaultValue = defaultValue;
        this.min = min;
        this.max = max;
        this.step = step;
        this.options = options;
        this.constraints = constraints;
    }
} 