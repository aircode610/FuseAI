/**
 * AgentDetail Page
 * Detailed view of a single agent
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, Play, Square, RotateCw, Settings, LayoutDashboard, FileText, BarChart2, Code, Webhook } from 'lucide-react';
import { Button, Card, Tabs, TabPanel, Modal, ModalFooter, Input, Select } from '../components/common';
import { StatusBadge } from '../components/common/Badge';
import { AgentOverview, AgentLogs, AgentMetrics, AgentAPI, AgentCode } from '../components/agents';
import { useAgents } from '../context/AgentContext';
import agentService from '../services/agentService';
import './AgentDetail.css';

export function AgentDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { agents, addAgent, updateAgent, removeAgent, setError } = useAgents();
  const [activeTab, setActiveTab] = useState('overview');
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [agentFromApi, setAgentFromApi] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [logs, setLogs] = useState([]);
  const [logsLoading, setLogsLoading] = useState(false);

  const agent = agents.find(a => a.id === id) || agentFromApi;

  const fetchMetrics = () => {
    if (!id) return;
    agentService.getAgentMetrics(id).then(setMetrics).catch(() => setMetrics(null));
  };
  const fetchLogs = () => {
    if (!id) return;
    setLogsLoading(true);
    agentService.getAgentLogs(id).then((data) => {
      setLogs(Array.isArray(data) ? data : []);
    }).catch(() => setLogs([])).finally(() => setLogsLoading(false));
  };

  useEffect(() => {
    if (!id) return;
    agentService.getAgent(id)
      .then((data) => {
        setAgentFromApi(data);
        addAgent(data); // idempotent: add or no-op if already in list
      })
      .catch(() => setAgentFromApi(null));
  }, [id, addAgent]);

  useEffect(() => {
    if (!id) return;
    fetchMetrics();
    fetchLogs();
  }, [id]);

  // If agent not found, show error
  if (!agent) {
    return (
      <div className="page agent-detail">
        <div className="empty-state">
          <h3 className="empty-state__title">Agent not found</h3>
          <p className="empty-state__description">
            The agent you're looking for doesn't exist or has been deleted.
          </p>
          <Button onClick={() => navigate('/')}>
            Back to Dashboard
          </Button>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'logs', label: 'Logs', icon: FileText, badge: logs.length },
    { id: 'metrics', label: 'Metrics', icon: BarChart2 },
    { id: 'api', label: 'API', icon: Webhook },
    { id: 'code', label: 'Code', icon: Code },
  ];

  const handleStart = async () => {
    try {
      await agentService.deployAgent(agent.id);
      updateAgent({ id: agent.id, status: 'deploying' });
      setTimeout(() => agentService.getAgent(agent.id).then(updateAgent).catch(() => {}), 2000);
    } catch {
      updateAgent({ id: agent.id, status: 'stopped' });
    }
  };

  const handleStop = async () => {
    try {
      await agentService.stopAgent(agent.id);
      updateAgent({ id: agent.id, status: 'stopped' });
    } catch {
      updateAgent({ id: agent.id, status: 'stopped' });
    }
  };

  const handleRestart = async () => {
    updateAgent({ id: agent.id, status: 'restarting' });
    try {
      await agentService.stopAgent(agent.id);
      await agentService.deployAgent(agent.id);
      setTimeout(() => agentService.getAgent(agent.id).then(updateAgent).catch(() => {}), 2000);
    } catch {
      updateAgent({ id: agent.id, status: 'stopped' });
    }
  };

  return (
    <div className="page agent-detail">
      {/* Breadcrumb */}
      <div className="agent-detail__breadcrumb">
        <Link to="/" className="agent-detail__back">
          <ArrowLeft size={16} />
          Back to Dashboard
        </Link>
      </div>

      {/* Header */}
      <div className="agent-detail__header">
        <div className="agent-detail__header-left">
          <div className="agent-detail__title-row">
            <h1 className="agent-detail__title">{agent.name}</h1>
            <StatusBadge status={agent.status} />
          </div>
          <p className="agent-detail__description">
            API • {agent.services?.length ? agent.services.join(' → ') : 'On-demand'}
          </p>
        </div>
        <div className="agent-detail__header-actions">
          {agent.status === 'running' ? (
            <Button variant="outline" icon={Square} onClick={handleStop}>
              Stop
            </Button>
          ) : (
            <Button variant="outline" icon={Play} onClick={handleStart}>
              Start
            </Button>
          )}
          <Button variant="outline" icon={RotateCw} onClick={handleRestart}>
            Restart
          </Button>
          <Button variant="ghost" icon={Settings} onClick={() => setShowSettingsModal(true)}>
            Settings
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <Card padding="none" className="agent-detail__card">
        <Tabs 
          tabs={tabs} 
          activeTab={activeTab} 
          onChange={setActiveTab} 
        />

        <TabPanel isActive={activeTab === 'overview'}>
          <AgentOverview 
            agent={agent} 
            metrics={metrics} 
            recentLogs={logs.slice(0, 5).map((log) => ({
              type: log.level === 'error' ? 'error' : 'success',
              time: log.timestamp || '',
              message: log.message || '',
            }))} 
          />
        </TabPanel>

        <TabPanel isActive={activeTab === 'logs'}>
          <AgentLogs 
            logs={logs} 
            loading={logsLoading}
            onRefresh={fetchLogs} 
          />
        </TabPanel>

        <TabPanel isActive={activeTab === 'metrics'}>
          <AgentMetrics metrics={metrics} loading={!metrics} />
        </TabPanel>

        <TabPanel isActive={activeTab === 'api'}>
          <AgentAPI 
            agent={agent} 
            onRequestComplete={() => { fetchMetrics(); fetchLogs(); }} 
          />
        </TabPanel>

        <TabPanel isActive={activeTab === 'code'}>
          <AgentCode agent={agent} />
        </TabPanel>
      </Card>

      {/* Settings Modal */}
      <Modal
        isOpen={showSettingsModal}
        onClose={() => setShowSettingsModal(false)}
        title="Agent Settings"
        size="md"
      >
        <div className="settings-form">
          <Input
            label="Agent Name"
            defaultValue={agent.name}
          />
          <Input
            label="Description"
            defaultValue={agent.description}
          />
          
          <div className="settings-section">
            <h4>Services</h4>
            <p className="settings-hint">
              Source: {agent.services?.[0]} • Target: {agent.services?.[1]}
            </p>
            <Button variant="outline" size="sm">Reconnect Services</Button>
          </div>

          <div className="settings-section">
            <h4>Features</h4>
            <label className="settings-checkbox">
              <input type="checkbox" defaultChecked />
              <span>Enable error search & solutions</span>
            </label>
            <label className="settings-checkbox">
              <input type="checkbox" defaultChecked />
              <span>Retry on failure</span>
            </label>
            <label className="settings-checkbox">
              <input type="checkbox" />
              <span>Rate limiting</span>
            </label>
          </div>

          <div className="settings-section settings-section--danger">
            <h4>Danger Zone</h4>
            <Button 
              variant="danger" 
              size="sm" 
              onClick={async () => {
                if (!window.confirm('Delete this agent? This will remove the agent, its code, metrics, and logs permanently.')) return;
                try {
                  await agentService.deleteAgent(agent.id);
                  removeAgent(agent.id);
                  setShowSettingsModal(false);
                  navigate('/');
                } catch (err) {
                  setError(err?.message || err?.data?.detail || 'Failed to delete agent');
                }
              }}
            >
              Delete Agent
            </Button>
          </div>
        </div>
        <ModalFooter>
          <Button variant="ghost" onClick={() => setShowSettingsModal(false)}>
            Cancel
          </Button>
          <Button onClick={() => setShowSettingsModal(false)}>
            Save Changes
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  );
}

export default AgentDetail;
