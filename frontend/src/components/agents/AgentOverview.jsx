/**
 * AgentOverview Component
 * Overview tab for agent detail page
 */

import { CheckCircle, XCircle, Clock, Zap, Link as LinkIcon, Copy, ExternalLink } from 'lucide-react';
import { Card, CardHeader, CardBody, Button } from '../common';
import './AgentOverview.css';

export function AgentOverview({ agent, metrics, recentLogs }) {
  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="agent-overview">
      {/* Quick Stats */}
      <div className="agent-overview__stats">
        <Card className="stat-card">
          <div className="stat-card__icon stat-card__icon--primary">
            <Zap size={20} />
          </div>
          <div className="stat-card__content">
            <span className="stat-card__value">{metrics?.totalRequests || 0}</span>
            <span className="stat-card__label">Total Requests</span>
          </div>
        </Card>

        <Card className="stat-card">
          <div className="stat-card__icon stat-card__icon--success">
            <CheckCircle size={20} />
          </div>
          <div className="stat-card__content">
            <span className="stat-card__value">
              {metrics?.successRate ? `${(metrics.successRate * 100).toFixed(1)}%` : '0%'}
            </span>
            <span className="stat-card__label">Success Rate</span>
          </div>
        </Card>

        <Card className="stat-card">
          <div className="stat-card__icon stat-card__icon--warning">
            <Clock size={20} />
          </div>
          <div className="stat-card__content">
            <span className="stat-card__value">{metrics?.avgResponseTime || 0}ms</span>
            <span className="stat-card__label">Avg Response</span>
          </div>
        </Card>

        <Card className="stat-card">
          <div className="stat-card__icon stat-card__icon--error">
            <XCircle size={20} />
          </div>
          <div className="stat-card__content">
            <span className="stat-card__value">{metrics?.failed || 0}</span>
            <span className="stat-card__label">Errors</span>
          </div>
        </Card>
      </div>

      <div className="agent-overview__grid">
        {/* Recent Activity */}
        <Card padding="none">
          <CardHeader>
            <h3>Recent Activity</h3>
          </CardHeader>
          <CardBody>
            {recentLogs && recentLogs.length > 0 ? (
              <ul className="activity-list">
                {recentLogs.slice(0, 5).map((log, index) => (
                  <li key={index} className="activity-list__item">
                    <span className={`activity-list__icon activity-list__icon--${log.type}`}>
                      {log.type === 'success' ? <CheckCircle size={14} /> : <XCircle size={14} />}
                    </span>
                    <span className="activity-list__time">{log.time}</span>
                    <span className="activity-list__message">{log.message}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="activity-list__empty">No recent activity</p>
            )}
          </CardBody>
        </Card>

        {/* Configuration */}
        <Card padding="none">
          <CardHeader>
            <h3>Configuration</h3>
          </CardHeader>
          <CardBody>
            <div className="config-list">
              <div className="config-list__item">
                <span className="config-list__label">API Endpoint</span>
                <div className="config-list__value-row">
                  <code className="config-list__code">{agent?.apiUrl || 'Not deployed'}</code>
                  {agent?.apiUrl && (
                    <button 
                      className="config-list__copy"
                      onClick={() => copyToClipboard(agent.apiUrl)}
                      title="Copy URL"
                    >
                      <Copy size={14} />
                    </button>
                  )}
                </div>
              </div>

              <div className="config-list__item">
                <span className="config-list__label">Trigger Type</span>
                <span className="config-list__value">API (on-demand)</span>
              </div>

              {agent?.services && (
                <div className="config-list__item">
                  <span className="config-list__label">Services</span>
                  <span className="config-list__value">{agent.services.join(' → ')}</span>
                </div>
              )}

              {agent?.schedule && (
                <div className="config-list__item">
                  <span className="config-list__label">Schedule</span>
                  <span className="config-list__value">{agent.schedule}</span>
                </div>
              )}
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}

export default AgentOverview;
