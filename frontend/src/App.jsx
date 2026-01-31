import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AgentProvider } from './context/AgentContext';
import { Layout } from './components/layout';
import { Dashboard, AgentDetail, Settings, Documentation } from './pages';

function App() {
  return (
    <AgentProvider>
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
    </AgentProvider>
  );
}

export default App;
