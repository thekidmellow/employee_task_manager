// static/js/tests/setup.js  (CommonJS so Jest can run without Babel)
require('@testing-library/jest-dom');

// Lightweight globals your app/tests may touch
global.fetch = jest.fn();
global.alert = jest.fn();
global.confirm = jest.fn(() => true);

// Very small jQuery-ish mock (only if your tests touch `$`)
// Remove if not needed.
global.$ = jest.fn(() => ({
  on: jest.fn(),
  off: jest.fn(),
  trigger: jest.fn(),
  val: jest.fn(),
  text: jest.fn(),
  html: jest.fn(),
  addClass: jest.fn(),
  removeClass: jest.fn(),
  hasClass: jest.fn(),
  show: jest.fn(),
  hide: jest.fn(),
  fadeIn: jest.fn(),
  fadeOut: jest.fn(),
}));

// Bootstrap mocks (only if referenced)
global.bootstrap = {
  Modal: jest.fn(() => ({ show: jest.fn(), hide: jest.fn() })),
  Alert: jest.fn(() => ({ close: jest.fn() })),
  Tooltip: jest.fn(),
  Popover: jest.fn(),
};

// Chart.js mock (only if referenced)
global.Chart = jest.fn(() => ({ update: jest.fn(), destroy: jest.fn() }));

beforeEach(() => {
  document.body.innerHTML = '';
  jest.clearAllMocks();
});
