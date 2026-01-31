/**
 * Dashboard Page
 * Main page showing all agents
 */

import { useState, useEffect } from 'react';
import { Plus, Search, Filter, Bot } from 'lucide-react';
import { Button, Input, Select, Modal } from '../components/common';
import { AgentCard } from '../components/agents';
import { CreateAgentWizard } from '../components/wizard';
import { useAgents } from '../context/AgentContext';
import './Dashboard.css';

// Mock data for demonstration
const mockAgents = [
  {
    id: 'agent_001',
    name: 'Trello Done Notifier',
    description: 'Notifies Slack when Trello cards move to Done',
    status: 'running',
    triggerType: 'webhook',
    services: ['Trello', 'Slack'],
    metrics: {
      totalRequests: 47,
      successful: 45,
      failed: 2,
      successRate: 0.957,
      avgResponseTime: 340,
    },
  },
  {
    id: 'agent_002',
    name: 'Daily Asana Digest',
    description: 'Sends daily task summaries to Slack',
    status: 'running',
    triggerType: 'scheduled',
    services: ['Asana', 'Slack'],
    schedule: '0 9 * * *',
    metrics: {
      totalRequests: 30,
      successful: 30,
      failed: 0,
      successRate: 1,
      avgResponseTime: 520,
    },
  },
  {
    id: 'agent_003',
    name: 'GitHub Issue Tracker',
    description: 'Creates Discord notifications for GitHub issues',
    status: 'error',
    triggerType: 'webhook',
    services: ['GitHub', 'Discord'],
    metrics: {
      totalRequests: 15,
      successful: 10,
      failed: 5,
      successRate: 0.667,
      avgResponseTime: 890,
    },
  },
];

export function Dashboard() {
  const { agents, setAgents, addAgent, removeAgent, updateAgent } = useAgents();
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Load mock data on mount
  useEffect(() => {
    if (agents.length === 0) {
      setAgents(mockAgents);
    }
  }, [agents.length, setAgents]);

  const statusOptions = [
    { value: 'all', label: 'All Status' },
    { value: 'running', label: 'Running' },
    { value: 'stopped', label: 'Stopped' },
    { value: 'error', label: 'Error' },
  ];

  const filteredAgents = agents.filter(agent => {
    const matchesSearch = agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          agent.description?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = filterStatus === 'all' || agent.status === filterStatus;
    return matchesSearch && matchesStatus;
  });

  const handleStart = (id) => {
    updateAgent({ id, status: 'running' });
  };

  const handleStop = (id) => {
    updateAgent({ id, status: 'stopped' });
  };

  const handleRestart = (id) => {
    updateAgent({ id, status: 'restarting' });
    setTimeout(() => {
      updateAgent({ id, status: 'running' });
    }, 1500);
  };

  const handleDelete = (id) => {
    if (window.confirm('Are you sure you want to delete this agent?')) {
      removeAgent(id);
    }
  };

  const handleSettings = (id) => {
    // Navigate to agent settings or open settings modal
    console.log('Settings for agent:', id);
  };

  const handleCreateComplete = (newAgent) => {
    addAgent(newAgent);
    setShowCreateModal(false);
  };

  return (
    <div className="page dashboard">
      <div className="page__header">
        <div className="page__header-content">
          <h1 className="page__title">My Agents</h1>
          <p className="page__description">
            {agents.length} agent{agents.length !== 1 ? 's' : ''} deployed
          </p>
        </div>
        <div className="page__actions">
          <Button icon={Plus} onClick={() => setShowCreateModal(true)}>
            Create Agent
          </Button>
        </div>
      </div>

      <div className="dashboard__filters">
        <Input
          icon={Search}
          placeholder="Search agents..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="dashboard__search"
        />
        <Select
          options={statusOptions}
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="dashboard__filter"
        />
      </div>

      {filteredAgents.length > 0 ? (
        <div className="dashboard__grid">
          {filteredAgents.map(agent => (
            <AgentCard
              key={agent.id}
              agent={agent}
              onStart={handleStart}
              onStop={handleStop}
              onRestart={handleRestart}
              onDelete={handleDelete}
              onSettings={handleSettings}
            />
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <div className="empty-state__icon">
            <Bot size={32} />
          </div>
          <h3 className="empty-state__title">
            {searchQuery || filterStatus !== 'all' ? 'No agents found' : 'No agents yet'}
          </h3>
          <p className="empty-state__description">
            {searchQuery || filterStatus !== 'all'
              ? 'Try adjusting your search or filter criteria'
              : 'Create your first agent to automate workflows between your favorite services'}
          </p>
          {!searchQuery && filterStatus === 'all' && (
            <Button icon={Plus} onClick={() => setShowCreateModal(true)}>
              Create Your First Agent
            </Button>
          )}
        </div>
      )}

      {/* Create Agent Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create New Agent"
        size="lg"
      >
        <CreateAgentWizard
          onComplete={handleCreateComplete}
          onCancel={() => setShowCreateModal(false)}
        />
      </Modal>
    </div>
  );
}

export default Dashboard;
