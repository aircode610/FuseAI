import { useState, useEffect } from 'react';
import { Plus, Search, Bot } from 'lucide-react';
import { Button, Input, Select, Modal } from '../components/common';
import { AgentCard } from '../components/agents';
import { CreateAgentWizard } from '../components/wizard';
import { useAgents } from '../context/AgentContext';
import agentService from '../services/agentService';
import { mockAgents } from '../mocks/agents';
import { STATUS_OPTIONS } from '../constants';
import { filterBySearchQuery, pluralize } from '../utils';
import './Dashboard.css';

export function Dashboard() {
  const { agents, setAgents, addAgent, removeAgent, updateAgent, setLoading } = useAgents();
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [showCreateModal, setShowCreateModal] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    agentService.getAgents()
      .then((list) => {
        if (!cancelled) setAgents(Array.isArray(list) ? list : []);
      })
      .catch(() => {
        if (!cancelled) setAgents(mockAgents);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [setAgents, setLoading]);

  const filteredAgents = agents
    .filter(agent => filterStatus === 'all' || agent.status === filterStatus)
    .filter(agent => !searchQuery || filterBySearchQuery([agent], searchQuery, ['name', 'description']).length > 0);

  const handleStart = (id) => updateAgent({ id, status: 'running' });
  const handleStop = (id) => updateAgent({ id, status: 'stopped' });
  
  const handleRestart = (id) => {
    updateAgent({ id, status: 'restarting' });
    setTimeout(() => updateAgent({ id, status: 'running' }), 1500);
  };

  const handleDelete = (id) => {
    if (window.confirm('Delete this agent?')) removeAgent(id);
  };

  const handleCreateComplete = (newAgent) => {
    addAgent(newAgent);
    setShowCreateModal(false);
  };

  return (
    <div className="page dashboard fade-in">
      <div className="page__header">
        <div className="page__header-content">
          <h1 className="page__title">My Agents</h1>
          <p className="page__description">
            {agents.length} {pluralize(agents.length, 'agent')} deployed
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
          options={STATUS_OPTIONS}
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="dashboard__filter"
        />
      </div>

      {filteredAgents.length > 0 ? (
        <div className="dashboard__grid">
          {filteredAgents.map((agent, index) => (
            <div 
              key={agent.id}
              className="fade-in-scale"
              style={{ animationDelay: `${index * 0.1}s` }}
            >
            <AgentCard
              agent={agent}
              onStart={handleStart}
              onStop={handleStop}
              onRestart={handleRestart}
              onDelete={handleDelete}
            />
            </div>
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
