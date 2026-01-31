/**
 * AgentCard Component
 * Card displaying agent summary on dashboard
 */

import { Link } from 'react-router-dom';
import { Settings, BarChart2, Trash2, Play, Square, RotateCw } from 'lucide-react';
import { Card } from '../common';
import { StatusBadge } from '../common/Badge';
import './AgentCard.css';

export function AgentCard({ 
  agent, 
  onStart, 
  onStop, 
  onRestart, 
  onDelete,
  onSettings 
}) {
  const {
    id,
    name,
    description,
    status,
    triggerType,
    services,
    metrics,
  } = agent;

  const handleAction = (e, action) => {
    e.preventDefault();
    e.stopPropagation();
    action(id);
  };

  const getTriggerLabel = (type) => {
    const labels = {
      webhook: 'Webhook',
      scheduled: 'Scheduled',
      on_demand: 'On-Demand',
    };
    return labels[type] || type;
  };

  return (
    <Link to={`/agents/${id}`} className="agent-card-link">
      <Card className="agent-card" hoverable clickable padding="none">
        <div className="agent-card__content">
          <div className="agent-card__header">
            <div className="agent-card__title-row">
              <h3 className="agent-card__name">{name}</h3>
              <StatusBadge status={status} />
            </div>
            <p className="agent-card__description">
              {getTriggerLabel(triggerType)} • {services?.join(' → ')}
            </p>
          </div>

          {metrics && (
            <div className="agent-card__metrics">
              <div className="agent-card__progress-bar">
                <div 
                  className="agent-card__progress-fill"
                  style={{ width: `${metrics.successRate * 100}%` }}
                />
              </div>
              <p className="agent-card__stats">
                <span className="agent-card__stat agent-card__stat--success">
                  {metrics.successful} successful
                </span>
                <span className="agent-card__stat-divider">•</span>
                <span className="agent-card__stat agent-card__stat--error">
                  {metrics.failed} failed
                </span>
                <span className="agent-card__stat-divider">•</span>
                <span className="agent-card__stat">
                  Avg: {metrics.avgResponseTime}ms
                </span>
              </p>
            </div>
          )}

          <div className="agent-card__actions">
            {status === 'running' ? (
              <button 
                className="agent-card__action-btn" 
                onClick={(e) => handleAction(e, onStop)}
                title="Stop"
              >
                <Square size={16} />
              </button>
            ) : (
              <button 
                className="agent-card__action-btn" 
                onClick={(e) => handleAction(e, onStart)}
                title="Start"
              >
                <Play size={16} />
              </button>
            )}
            <button 
              className="agent-card__action-btn" 
              onClick={(e) => handleAction(e, onRestart)}
              title="Restart"
            >
              <RotateCw size={16} />
            </button>
            <button 
              className="agent-card__action-btn" 
              onClick={(e) => handleAction(e, onSettings)}
              title="Settings"
            >
              <Settings size={16} />
            </button>
            <button 
              className="agent-card__action-btn" 
              onClick={(e) => handleAction(e, onDelete)}
              title="Delete"
            >
              <Trash2 size={16} />
            </button>
          </div>
        </div>
      </Card>
    </Link>
  );
}

export default AgentCard;
