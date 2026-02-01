/**
 * Application Constants
 */

export const STATUS = {
  RUNNING: 'running',
  STOPPED: 'stopped',
  ERROR: 'error',
  RESTARTING: 'restarting',
};

export const TRIGGER_TYPES = {
  WEBHOOK: 'webhook',
  SCHEDULED: 'scheduled',
  MANUAL: 'manual',
};

export const STATUS_OPTIONS = [
  { value: 'all', label: 'All Status' },
  { value: STATUS.RUNNING, label: 'Running' },
  { value: STATUS.STOPPED, label: 'Stopped' },
  { value: STATUS.ERROR, label: 'Error' },
];

export const THEME = {
  LIGHT: 'light',
  DARK: 'dark',
};

export const ROUTES = {
  HOME: '/',
  AGENT_DETAIL: '/agents/:id',
  SETTINGS: '/settings',
  DOCS: '/docs',
};
