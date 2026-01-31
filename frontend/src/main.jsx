/**
 * FuseAI - AI Agent Generator
 * Application Entry Point
 */

import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './index.css';

// Apply saved theme immediately to prevent flash
const savedTheme = localStorage.getItem('fuseai-theme') || 'light';
document.documentElement.setAttribute('data-theme', savedTheme);

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>
);
