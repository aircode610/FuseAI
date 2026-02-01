import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import { getThemeFromStorage, setThemeInStorage } from './utils';
import './index.css';

setThemeInStorage(getThemeFromStorage());

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>
);
