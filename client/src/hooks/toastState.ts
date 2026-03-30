// Global toast state management
// Extracted to separate file to avoid Fast Refresh issues

export type ToastType = 'info' | 'success' | 'warning' | 'error';

export interface ToastAction {
  label: string;
  onClick: () => void;
}

export interface Toast {
  id: string;
  message: string;
  type: ToastType;
  duration?: number;
  action?: ToastAction;
}

let toastListeners: ((toasts: Toast[]) => void)[] = [];
let toasts: Toast[] = [];

function notifyListeners() {
  toastListeners.forEach((listener) => listener([...toasts]));
}

export function addToast(
  message: string,
  type: ToastType = 'info',
  duration?: number,
  action?: ToastAction
): string {
  const toast: Toast = {
    id: `${Date.now()}-${Math.random()}`,
    message,
    type,
    duration,
    action,
  };
  toasts = [...toasts, toast]; // Create new array reference
  notifyListeners();
  return toast.id;
}

export function removeToast(id: string) {
  toasts = toasts.filter((t) => t.id !== id);
  notifyListeners();
}

export function getToasts() {
  return [...toasts];
}

export function subscribeToToasts(listener: (toasts: Toast[]) => void) {
  toastListeners.push(listener);
  return () => {
    toastListeners = toastListeners.filter((l) => l !== listener);
  };
}

// Helper functions for common toast types
export const toast = {
  info: (message: string, duration?: number, action?: ToastAction) => addToast(message, 'info', duration, action),
  success: (message: string, duration?: number, action?: ToastAction) => addToast(message, 'success', duration, action),
  warning: (message: string, duration?: number, action?: ToastAction) => addToast(message, 'warning', duration, action),
  error: (message: string, duration?: number, action?: ToastAction) => addToast(message, 'error', duration, action),
};
