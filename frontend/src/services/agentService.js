/**
 * Agent Service
 * Handles all agent-related API operations
 */

import api from './api';

export const agentService = {
  /**
   * Get all agents
   */
  async getAgents() {
    return api.get('/agents');
  },

  /**
   * Get a single agent by ID
   */
  async getAgent(agentId) {
    return api.get(`/agents/${agentId}`);
  },

  /**
   * Create a new agent
   */
  async createAgent(agentData) {
    return api.post('/agents', agentData);
  },

  /**
   * Analyze a prompt only (suggested name, services, endpoints). No create/deploy.
   */
  async analyzePrompt(prompt) {
    return api.post('/agents/analyze', { prompt });
  },

  /**
   * Get env variable names and descriptions for Settings (no values).
   */
  async getEnvSchema() {
    return api.get('/env-schema');
  },

  /**
   * Deploy an agent
   */
  async deployAgent(agentId, config) {
    return api.post(`/agents/${agentId}/deploy`, config);
  },

  /**
   * Update agent configuration
   */
  async updateAgent(agentId, updates) {
    return api.patch(`/agents/${agentId}`, updates);
  },

  /**
   * Delete an agent
   */
  async deleteAgent(agentId) {
    return api.delete(`/agents/${agentId}`);
  },

  /**
   * Start an agent
   */
  async startAgent(agentId) {
    return api.post(`/agents/${agentId}/start`);
  },

  /**
   * Stop an agent
   */
  async stopAgent(agentId) {
    return api.post(`/agents/${agentId}/stop`);
  },

  /**
   * Restart an agent
   */
  async restartAgent(agentId) {
    return api.post(`/agents/${agentId}/restart`);
  },

  /**
   * Get agent logs
   */
  async getAgentLogs(agentId, params = {}) {
    return api.get(`/agents/${agentId}/logs`, params);
  },

  /**
   * Get agent metrics
   */
  async getAgentMetrics(agentId, params = {}) {
    return api.get(`/agents/${agentId}/metrics`, params);
  },

  /**
   * Test / run agent endpoint (proxy through backend to deployed agent)
   * payload: { method, path, query?, body? }
   */
  async testEndpoint(agentId, payload) {
    return api.post(`/agents/${agentId}/test`, payload);
  },

  /**
   * Get agent code
   */
  async getAgentCode(agentId) {
    return api.get(`/agents/${agentId}/code`);
  },
};

export default agentService;
