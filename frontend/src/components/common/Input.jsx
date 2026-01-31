/**
 * Input Component
 * Form inputs with labels and validation
 */

import './Input.css';

export function Input({ 
  label,
  error,
  hint,
  icon: Icon,
  className = '',
  ...props 
}) {
  return (
    <div className={`input-group ${error ? 'input-group--error' : ''} ${className}`}>
      {label && (
        <label className="input-group__label">
          {label}
          {props.required && <span className="input-group__required">*</span>}
        </label>
      )}
      <div className="input-group__wrapper">
        {Icon && <Icon className="input-group__icon" size={18} />}
        <input 
          className={`input-group__input ${Icon ? 'input-group__input--with-icon' : ''}`}
          {...props} 
        />
      </div>
      {hint && !error && <span className="input-group__hint">{hint}</span>}
      {error && <span className="input-group__error">{error}</span>}
    </div>
  );
}

export function Textarea({ 
  label,
  error,
  hint,
  className = '',
  rows = 4,
  ...props 
}) {
  return (
    <div className={`input-group ${error ? 'input-group--error' : ''} ${className}`}>
      {label && (
        <label className="input-group__label">
          {label}
          {props.required && <span className="input-group__required">*</span>}
        </label>
      )}
      <textarea 
        className="input-group__textarea"
        rows={rows}
        {...props} 
      />
      {hint && !error && <span className="input-group__hint">{hint}</span>}
      {error && <span className="input-group__error">{error}</span>}
    </div>
  );
}

export function Select({ 
  label,
  error,
  hint,
  options = [],
  placeholder,
  className = '',
  ...props 
}) {
  return (
    <div className={`input-group ${error ? 'input-group--error' : ''} ${className}`}>
      {label && (
        <label className="input-group__label">
          {label}
          {props.required && <span className="input-group__required">*</span>}
        </label>
      )}
      <select className="input-group__select" {...props}>
        {placeholder && <option value="">{placeholder}</option>}
        {options.map(option => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {hint && !error && <span className="input-group__hint">{hint}</span>}
      {error && <span className="input-group__error">{error}</span>}
    </div>
  );
}

export default Input;
