/**
 * Custom hooks for agent data management
 */

import { useState, useEffect, useCallback } from 'react';
import { useAgents } from '../context/AgentContext';
import agentService from '../services/agentService';

const useAsyncData = (fetcher, dependencies = []) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetch = useCallback(async (...args) => {
    if (!dependencies.every(Boolean)) return;
    
    setLoading(true);
    setError(null);
    try {
      const result = await fetcher(...args);
      setData(result);
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, dependencies);

  useEffect(() => { fetch(); }, [fetch]);

  return { data, loading, error, refetch: fetch };
};

export function useAgentData() {
  const { agents, setAgents, addAgent, updateAgent, removeAgent, loading, setLoading, setError, clearError } = useAgents();

  const fetchAgents = async () => {
    setLoading(true);
    clearError();
    try {
      const data = await agentService.getAgents();
      setAgents(data);
    } catch (err) {
      setError(err.message);
    }
  };

  const createAgent = async (agentData) => {
    setLoading(true);
    try {
      const newAgent = await agentService.createAgent(agentData);
      addAgent(newAgent);
      return newAgent;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const deleteAgent = async (agentId) => {
    setLoading(true);
    try {
      await agentService.deleteAgent(agentId);
      removeAgent(agentId);
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const agentAction = async (agentId, action, status) => {
    try {
      await action(agentId);
      updateAgent({ id: agentId, status });
    } catch (err) {
      setError(err.message);
      throw err;
    }
  };

  return {
    agents,
    loading,
    error,
    fetchAgents,
    createAgent,
    deleteAgent,
    startAgent: (id) => agentAction(id, agentService.startAgent, 'running'),
    stopAgent: (id) => agentAction(id, agentService.stopAgent, 'stopped'),
    restartAgent: async (id) => {
      updateAgent({ id, status: 'restarting' });
      await agentAction(id, agentService.restartAgent, 'running');
    },
    clearError,
  };
}

export const useAgent = (agentId) => useAsyncData(() => agentService.getAgent(agentId), [agentId]);
export const useAgentLogs = (agentId) => useAsyncData((params = {}) => agentService.getAgentLogs(agentId, params), [agentId]);
export const useAgentMetrics = (agentId) => useAsyncData((params = {}) => agentService.getAgentMetrics(agentId, params), [agentId]);

export default useAgentData;
