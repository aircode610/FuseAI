/**
 * Mock Agent Data
 * For demonstration purposes until backend is connected
 */

export const mockAgents = [
  {
    id: 'agent_001',
    name: 'Trello Done Notifier',
    description: 'Notifies Slack when Trello cards move to Done',
    status: 'running',
    triggerType: 'on_demand',
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
    triggerType: 'on_demand',
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
    triggerType: 'on_demand',
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
