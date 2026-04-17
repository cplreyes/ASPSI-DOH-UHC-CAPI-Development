import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.tsx';
import './index.css';
import { registerSW } from 'virtual:pwa-register';

// Prompt-style SW registration. Full update UX lands in M11.
registerSW({
  onNeedRefresh() {
    console.info('[PWA] New content available. Reload to update.');
  },
  onOfflineReady() {
    console.info('[PWA] Ready to work offline.');
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
