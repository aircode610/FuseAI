import { CheckCircle, XCircle, AlertCircle, X } from 'lucide-react';
import './Toast.css';

const ICONS = {
  success: CheckCircle,
  error: XCircle,
  info: AlertCircle,
};

export function Toast({ id, type = 'success', message, onDismiss }) {
  const Icon = ICONS[type] || ICONS.info;

  return (
    <div className={`toast toast--${type}`} onClick={() => onDismiss(id)}>
      <div className="toast__icon">
        <Icon size={20} />
      </div>
      <p className="toast__message">{message}</p>
      <button className="toast__close" onClick={() => onDismiss(id)}>
        <X size={16} />
      </button>
    </div>
  );
}

export function ToastContainer({ toasts, onDismiss }) {
  return (
    <div className="toast-container">
      {toasts.map((toast) => (
        <Toast key={toast.id} {...toast} onDismiss={onDismiss} />
      ))}
    </div>
  );
}

export default Toast;
