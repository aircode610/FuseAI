/**
 * Forge - AI Agent Generator
 * Main Application Component
 */

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AgentProvider } from './context/AgentContext';
import { Layout } from './components/layout';
import { Dashboard, AgentDetail, Templates } from './pages';

function App() {
  return (
    <AgentProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="agents/:id" element={<AgentDetail />} />
            <Route path="templates" element={<Templates />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AgentProvider>
  );
}

export default App;
