import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AgentProvider } from './context/AgentContext';
import { ToastProvider } from './context/ToastContext';
import { Layout } from './components/layout';
import { Dashboard, AgentDetail, Settings, Documentation } from './pages';
import { ToastContainer } from './components/common';
import { useToast } from './context/ToastContext';

function AppContent() {
  const { toasts, dismissToast } = useToast();

  return (
    <>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="agents/:id" element={<AgentDetail />} />
            <Route path="settings" element={<Settings />} />
            <Route path="docs" element={<Documentation />} />
          </Route>
        </Routes>
      </BrowserRouter>
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </>
  );
}

function App() {
  return (
    <ToastProvider>
      <AgentProvider>
        <AppContent />
      </AgentProvider>
    </ToastProvider>
  );
}

export default App;
