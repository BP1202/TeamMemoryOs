import React from 'react';
import ReactDOM from 'react-dom/client';
import { RootProvider } from '@providers/RootProvider';
import { AppRouter } from '@app/router';
import '@styles/globals.css';

const root = document.getElementById('root');

if (!root) {
  throw new Error('Root element #root not found. Check index.html.');
}

ReactDOM.createRoot(root).render(
  <React.StrictMode>
    <RootProvider>
      <AppRouter />
    </RootProvider>
  </React.StrictMode>,
);
