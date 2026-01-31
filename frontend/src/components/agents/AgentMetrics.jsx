/**
 * AgentMetrics Component
 * Metrics tab for agent detail page
 */

import { useState } from 'react';
import { Download } from 'lucide-react';
import { Card, CardHeader, CardBody, Button, Select } from '../common';
import './AgentMetrics.css';

export function AgentMetrics({ metrics, loading }) {
  const [timeRange, setTimeRange] = useState('7d');

  const timeOptions = [
    { value: '24h', label: 'Last 24 Hours' },
    { value: '7d', label: 'Last 7 Days' },
    { value: '30d', label: 'Last 30 Days' },
    { value: '90d', label: 'Last 90 Days' },
  ];

  // Mock chart data - in production, this would come from the API
  const chartData = metrics?.requestsOverTime || [
    { day: 'Mon', value: 12 },
    { day: 'Tue', value: 19 },
    { day: 'Wed', value: 15 },
    { day: 'Thu', value: 22 },
    { day: 'Fri', value: 30 },
    { day: 'Sat', value: 18 },
    { day: 'Sun', value: 25 },
  ];

  const maxValue = Math.max(...chartData.map(d => d.value));

  return (
    <div className="agent-metrics">
      <div className="agent-metrics__header">
        <Select
          options={timeOptions}
          value={timeRange}
          onChange={(e) => setTimeRange(e.target.value)}
        />
        <Button variant="outline" icon={Download}>
          Export CSV
        </Button>
      </div>

      {/* Requests Chart */}
      <Card padding="none">
        <CardHeader>
          <h3>Requests Over Time</h3>
        </CardHeader>
        <CardBody>
          <div className="metrics-chart">
            <div className="metrics-chart__bars">
              {chartData.map((item, index) => (
                <div key={index} className="metrics-chart__bar-container">
                  <div 
                    className="metrics-chart__bar"
                    style={{ height: `${(item.value / maxValue) * 100}%` }}
                  >
                    <span className="metrics-chart__value">{item.value}</span>
                  </div>
                  <span className="metrics-chart__label">{item.day}</span>
                </div>
              ))}
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Success Rate */}
      <Card padding="none">
        <CardHeader>
          <h3>Success vs Failures</h3>
        </CardHeader>
        <CardBody>
          <div className="metrics-progress">
            <div className="metrics-progress__bar">
              <div 
                className="metrics-progress__fill metrics-progress__fill--success"
                style={{ width: `${(metrics?.successRate || 0.95) * 100}%` }}
              />
            </div>
            <div className="metrics-progress__labels">
              <span className="metrics-progress__label metrics-progress__label--success">
                {((metrics?.successRate || 0.95) * 100).toFixed(1)}% Success
              </span>
              <span className="metrics-progress__label metrics-progress__label--error">
                {((1 - (metrics?.successRate || 0.95)) * 100).toFixed(1)}% Failed
              </span>
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Response Time Distribution */}
      <Card padding="none">
        <CardHeader>
          <h3>Response Time Distribution</h3>
        </CardHeader>
        <CardBody>
          <div className="metrics-stats">
            <div className="metrics-stat">
              <span className="metrics-stat__label">Min</span>
              <span className="metrics-stat__value">{metrics?.minResponseTime || 240}ms</span>
            </div>
            <div className="metrics-stat">
              <span className="metrics-stat__label">Avg</span>
              <span className="metrics-stat__value">{metrics?.avgResponseTime || 340}ms</span>
            </div>
            <div className="metrics-stat">
              <span className="metrics-stat__label">Max</span>
              <span className="metrics-stat__value">{metrics?.maxResponseTime || 1200}ms</span>
            </div>
            <div className="metrics-stat">
              <span className="metrics-stat__label">P95</span>
              <span className="metrics-stat__value">{metrics?.p95ResponseTime || 580}ms</span>
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Resource Usage */}
      <Card padding="none">
        <CardHeader>
          <h3>Resource Usage</h3>
        </CardHeader>
        <CardBody>
          <div className="metrics-resources">
            <div className="metrics-resource">
              <span className="metrics-resource__label">Total Zapier API calls</span>
              <span className="metrics-resource__value">{metrics?.zapierCalls || 315}</span>
            </div>
            <div className="metrics-resource">
              <span className="metrics-resource__label">Total web searches</span>
              <span className="metrics-resource__value">{metrics?.webSearches || 12}</span>
            </div>
            <div className="metrics-resource">
              <span className="metrics-resource__label">Total tokens used</span>
              <span className="metrics-resource__value">{(metrics?.tokensUsed || 45230).toLocaleString()}</span>
            </div>
            <div className="metrics-resource">
              <span className="metrics-resource__label">Estimated cost</span>
              <span className="metrics-resource__value">${(metrics?.estimatedCost || 2.34).toFixed(2)}</span>
            </div>
          </div>
        </CardBody>
      </Card>
    </div>
  );
}

export default AgentMetrics;
