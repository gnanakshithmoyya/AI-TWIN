import { StrictMode } from 'react';
// Force light mode by removing dark class and preventing it from being added
document.documentElement.classList.remove('dark');

// Override the system preference detection
const forceLightMode = () => {
  // Always set dark mode to false regardless of localStorage or system preference
  document.documentElement.classList.toggle('dark', false // Force to false instead of checking localStorage or system preference
  );
};
const addBrokenImageHandler = () => {
  document.addEventListener('error', function (e) {
    if (e.target instanceof HTMLImageElement) {
      const img = e.target;
      if (!img.dataset.fallbackApplied) {
        img.dataset.fallbackApplied = 'true';

        // Create a simple fallback SVG icon as data URL
        const fallbackSvg = `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%239ca3af' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect width='18' height='18' x='3' y='3' rx='2' ry='2'/%3E%3Ccircle cx='9' cy='9' r='2'/%3E%3Cpath d='m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21'/%3E%3C/svg%3E`;
        img.src = fallbackSvg;
        img.classList.add('broken-image-fallback');
        if (!img.alt || img.alt.trim() === '') {
          img.alt = 'Image not available';
        }
      }
    }
  }, true);
};

// Run immediately
forceLightMode();
addBrokenImageHandler();

// Also run when the DOM is loaded to ensure it applies
document.addEventListener('DOMContentLoaded', forceLightMode);

// Override system preference changes
const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
mediaQuery.addEventListener('change', forceLightMode);
import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App.tsx';
createRoot(document.getElementById('root')!).render(<StrictMode>
    <App />
  </StrictMode>);