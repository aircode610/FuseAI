/**
 * Badge Component
 * Status indicators and labels
 */

import './Badge.css';

export function Badge({ 
  children, 
  variant = 'default',
  size = 'md',
  dot = false,
  className = '',
  ...props 
}) {
  const classes = [
    'badge',
    `badge--${variant}`,
    `badge--${size}`,
    dot && 'badge--dot',
    className,
  ].filter(Boolean).join(' ');

  return (
    <span className={classes} {...props}>
      {dot && <span className="badge__dot" />}
      {children}
    </span>
  );
}

export function StatusBadge({ status }) {
  const statusConfig = {
    running: { variant: 'success', label: 'Running', dot: true },
    stopped: { variant: 'default', label: 'Stopped', dot: true },
    error: { variant: 'error', label: 'Error', dot: true },
    restarting: { variant: 'warning', label: 'Restarting', dot: true },
    deploying: { variant: 'info', label: 'Deploying', dot: true },
  };

  const config = statusConfig[status] || statusConfig.stopped;

  return (
    <Badge variant={config.variant} dot={config.dot}>
      {config.label}
    </Badge>
  );
}

export default Badge;
