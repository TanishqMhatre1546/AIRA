import "@testing-library/jest-dom";

const storage = new Map();
const mockLocalStorage = {
  getItem: (key) => (storage.has(key) ? storage.get(key) : null),
  setItem: (key, val) => storage.set(key, String(val)),
  removeItem: (key) => storage.delete(key),
  clear: () => storage.clear(),
  get length() {
    return storage.size;
  },
  key: (i) => Array.from(storage.keys())[i] || null,
};

Object.defineProperty(globalThis, "localStorage", {
  value: mockLocalStorage,
  configurable: true,
  writable: true,
});

if (typeof window !== "undefined") {
  Object.defineProperty(window, "localStorage", {
    value: mockLocalStorage,
    configurable: true,
    writable: true,
  });
  if (window.HTMLElement) {
    window.HTMLElement.prototype.scrollIntoView = function () {};
  }
}
