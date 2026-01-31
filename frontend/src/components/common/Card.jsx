/**
 * Card Component
 * Container with optional header and footer
 */

import './Card.css';

export function Card({ 
  children, 
  className = '',
  padding = 'md',
  hoverable = false,
  clickable = false,
  ...props 
}) {
  const classes = [
    'card',
    `card--padding-${padding}`,
    hoverable && 'card--hoverable',
    clickable && 'card--clickable',
    className,
  ].filter(Boolean).join(' ');

  return (
    <div className={classes} {...props}>
      {children}
    </div>
  );
}

export function CardHeader({ children, className = '', actions }) {
  return (
    <div className={`card__header ${className}`}>
      <div className="card__header-content">{children}</div>
      {actions && <div className="card__header-actions">{actions}</div>}
    </div>
  );
}

export function CardBody({ children, className = '' }) {
  return (
    <div className={`card__body ${className}`}>
      {children}
    </div>
  );
}

export function CardFooter({ children, className = '' }) {
  return (
    <div className={`card__footer ${className}`}>
      {children}
    </div>
  );
}

export default Card;
