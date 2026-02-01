/**
 * Button Component
 * Reusable button with variants
 */

import './Button.css';

export function Button({ 
  children, 
  variant = 'primary', 
  size = 'md',
  icon: Icon,
  iconPosition = 'left',
  loading = false,
  disabled = false,
  fullWidth = false,
  className = '',
  ...props 
}) {
  const classes = [
    'btn',
    `btn--${variant}`,
    `btn--${size}`,
    fullWidth && 'btn--full-width',
    loading && 'btn--loading',
    Icon && !children && 'btn--icon-only',
    className,
  ].filter(Boolean).join(' ');

  return (
    <button 
      className={classes} 
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <span className="btn__spinner" />
      ) : (
        <>
          {Icon && iconPosition === 'left' && <Icon className="btn__icon" size={size === 'sm' ? 14 : 16} />}
          {children && <span className="btn__text">{children}</span>}
          {Icon && iconPosition === 'right' && <Icon className="btn__icon" size={size === 'sm' ? 14 : 16} />}
        </>
      )}
    </button>
  );
}

export default Button;
