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

// Mock log data
const mockLogs = [
  { id: 1, level: 'success', timestamp: '2:34 PM', message: 'Card "Fix login bug" posted to #dev-team', details: { card_id: 'card_123', channel: '#dev-team' } },
  { id: 2, level: 'success', timestamp: '1:22 PM', message: 'Card "Update docs" posted to #dev-team', details: { card_id: 'card_124', channel: '#dev-team' } },
  { id: 3, level: 'error', timestamp: '12:45 PM', message: 'Slack rate limit exceeded (429)', details: { error: 'Rate limit exceeded', status: 429 }, solutions: ['Implement exponential backoff', 'Reduce message frequency', 'Use Slack bulk API'] },
  { id: 4, level: 'success', timestamp: '11:30 AM', message: 'Card "Deploy v2.0" posted to #dev-team', details: { card_id: 'card_125', channel: '#dev-team' } },
  { id: 5, level: 'info', timestamp: '10:15 AM', message: 'Agent started successfully', details: { pid: 12345 } },
];

// Mock metrics data  
const mockMetrics = {
  totalRequests: 47,
  successful: 45,
  failed: 2,
  successRate: 0.957,
  avgResponseTime: 340,
  minResponseTime: 240,
  maxResponseTime: 1200,
  p95ResponseTime: 580,
  zapierCalls: 315,
  webSearches: 12,
  tokensUsed: 45230,
  estimatedCost: 2.34,
  requestsOverTime: [
    { day: 'Mon', value: 12 },
    { day: 'Tue', value: 19 },
    { day: 'Wed', value: 15 },
    { day: 'Thu', value: 22 },
    { day: 'Fri', value: 30 },
    { day: 'Sat', value: 18 },
    { day: 'Sun', value: 25 },
  ],
};

// Mock recent logs for overview
const mockRecentLogs = [
  { type: 'success', time: '2:34 PM', message: 'Card "Fix login bug" → #dev-team' },
  { type: 'success', time: '1:22 PM', message: 'Card "Update docs" → #dev-team' },
  { type: 'error', time: '12:45 PM', message: 'ERROR: Slack rate limit exceeded' },
  { type: 'success', time: '11:30 AM', message: 'Card "Deploy v2.0" → #dev-team' },
  { type: 'success', time: '10:15 AM', message: 'Card "Review PR #234" → #dev-team' },
];

export function AgentDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { agents, addAgent, updateAgent } = useAgents();
  const [activeTab, setActiveTab] = useState('overview');
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [agentFromApi, setAgentFromApi] = useState(null);

  const agent = agents.find(a => a.id === id) || agentFromApi;

  useEffect(() => {
    if (!id) return;
    agentService.getAgent(id)
      .then((data) => {
        setAgentFromApi(data);
        addAgent(data); // idempotent: add or no-op if already in list
      })
      .catch(() => setAgentFromApi(null));
  }, [id, addAgent]);

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
    { id: 'logs', label: 'Logs', icon: FileText, badge: mockLogs.length },
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
            {agent.triggerType} • {agent.services?.join(' → ')}
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
            metrics={mockMetrics} 
            recentLogs={mockRecentLogs} 
          />
        </TabPanel>

        <TabPanel isActive={activeTab === 'logs'}>
          <AgentLogs 
            logs={mockLogs} 
            onRefresh={() => console.log('Refresh logs')} 
          />
        </TabPanel>

        <TabPanel isActive={activeTab === 'metrics'}>
          <AgentMetrics metrics={mockMetrics} />
        </TabPanel>

        <TabPanel isActive={activeTab === 'api'}>
          <AgentAPI agent={agent} />
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
            <Button variant="danger" size="sm">Delete Agent</Button>
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
