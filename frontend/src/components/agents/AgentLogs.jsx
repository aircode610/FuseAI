/**
 * AgentLogs Component
 * Logs tab for agent detail page
 */

import { useState } from 'react';
import { RefreshCw, ChevronDown, ChevronUp, AlertCircle, CheckCircle, Info, Search } from 'lucide-react';
import { Button, Select, Input } from '../common';
import './AgentLogs.css';

export function AgentLogs({ logs = [], loading, onRefresh }) {
  const [filter, setFilter] = useState('all');
  const [timeRange, setTimeRange] = useState('24h');
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedLogs, setExpandedLogs] = useState({});

  const filterOptions = [
    { value: 'all', label: 'All Levels' },
    { value: 'info', label: 'Info' },
    { value: 'success', label: 'Success' },
    { value: 'error', label: 'Errors' },
    { value: 'warning', label: 'Warnings' },
  ];

  const timeOptions = [
    { value: '1h', label: 'Last Hour' },
    { value: '24h', label: 'Last 24 Hours' },
    { value: '7d', label: 'Last 7 Days' },
    { value: '30d', label: 'Last 30 Days' },
  ];

  const toggleExpand = (logId) => {
    setExpandedLogs(prev => ({
      ...prev,
      [logId]: !prev[logId],
    }));
  };

  const filteredLogs = logs.filter(log => {
    if (filter !== 'all' && log.level !== filter) return false;
    if (searchQuery && !log.message.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  const getLogIcon = (level) => {
    switch (level) {
      case 'success':
        return <CheckCircle size={16} />;
      case 'error':
        return <AlertCircle size={16} />;
      case 'warning':
        return <AlertCircle size={16} />;
      default:
        return <Info size={16} />;
    }
  };

  return (
    <div className="agent-logs">
      <div className="agent-logs__header">
        <div className="agent-logs__filters">
          <Select
            options={filterOptions}
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="agent-logs__filter"
          />
          <Select
            options={timeOptions}
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="agent-logs__filter"
          />
          <Input
            icon={Search}
            placeholder="Search logs..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="agent-logs__search"
          />
        </div>
        <Button 
          variant="outline" 
          icon={RefreshCw} 
          onClick={onRefresh}
          loading={loading}
        >
          Refresh
        </Button>
      </div>

      <div className="agent-logs__list">
        {filteredLogs.length > 0 ? (
          filteredLogs.map((log) => (
            <div 
              key={log.id} 
              className={`log-entry log-entry--${log.level}`}
            >
              <div className="log-entry__main" onClick={() => toggleExpand(log.id)}>
                <span className={`log-entry__icon log-entry__icon--${log.level}`}>
                  {getLogIcon(log.level)}
                </span>
                <span className="log-entry__time">{log.timestamp}</span>
                <span className="log-entry__level">{log.level.toUpperCase()}</span>
                <span className="log-entry__message">{log.message}</span>
                <button className="log-entry__expand">
                  {expandedLogs[log.id] ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </button>
              </div>
              
              {expandedLogs[log.id] && log.details && (
                <div className="log-entry__details">
                  <pre>{JSON.stringify(log.details, null, 2)}</pre>
                  
                  {log.solutions && log.solutions.length > 0 && (
                    <div className="log-entry__solutions">
                      <h4>Possible Solutions</h4>
                      <ul>
                        {log.solutions.map((solution, idx) => (
                          <li key={idx}>{solution}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))
        ) : (
          <div className="agent-logs__empty">
            <p>No logs found matching your criteria</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default AgentLogs;
