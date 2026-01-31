/**
 * Custom hook for fetching and managing agent data
 */

import { useState, useEffect, useCallback } from 'react';
import { useAgents } from '../context/AgentContext';
import agentService from '../services/agentService';

export function useAgentData() {
  const { 
    agents, 
    setAgents, 
    addAgent, 
    updateAgent, 
    removeAgent,
    loading,
    setLoading,
    error,
    setError,
    clearError,
  } = useAgents();

  const fetchAgents = useCallback(async () => {
    setLoading(true);
    clearError();
    try {
      const data = await agentService.getAgents();
      setAgents(data);
    } catch (err) {
      setError(err.message);
    }
  }, [setAgents, setLoading, setError, clearError]);

  const createAgent = useCallback(async (agentData) => {
    setLoading(true);
    clearError();
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
  }, [addAgent, setLoading, setError, clearError]);

  const deleteAgent = useCallback(async (agentId) => {
    setLoading(true);
    clearError();
    try {
      await agentService.deleteAgent(agentId);
      removeAgent(agentId);
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [removeAgent, setLoading, setError, clearError]);

  const startAgent = useCallback(async (agentId) => {
    try {
      await agentService.startAgent(agentId);
      updateAgent({ id: agentId, status: 'running' });
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, [updateAgent, setError]);

  const stopAgent = useCallback(async (agentId) => {
    try {
      await agentService.stopAgent(agentId);
      updateAgent({ id: agentId, status: 'stopped' });
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, [updateAgent, setError]);

  const restartAgent = useCallback(async (agentId) => {
    try {
      updateAgent({ id: agentId, status: 'restarting' });
      await agentService.restartAgent(agentId);
      updateAgent({ id: agentId, status: 'running' });
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, [updateAgent, setError]);

  return {
    agents,
    loading,
    error,
    fetchAgents,
    createAgent,
    deleteAgent,
    startAgent,
    stopAgent,
    restartAgent,
    clearError,
  };
}

export function useAgent(agentId) {
  const [agent, setAgent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchAgent = useCallback(async () => {
    if (!agentId) return;
    
    setLoading(true);
    setError(null);
    try {
      const data = await agentService.getAgent(agentId);
      setAgent(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [agentId]);

  useEffect(() => {
    fetchAgent();
  }, [fetchAgent]);

  return { agent, loading, error, refetch: fetchAgent };
}

export function useAgentLogs(agentId) {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchLogs = useCallback(async (params = {}) => {
    if (!agentId) return;
    
    setLoading(true);
    setError(null);
    try {
      const data = await agentService.getAgentLogs(agentId, params);
      setLogs(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [agentId]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  return { logs, loading, error, refetch: fetchLogs };
}

export function useAgentMetrics(agentId) {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchMetrics = useCallback(async (params = {}) => {
    if (!agentId) return;
    
    setLoading(true);
    setError(null);
    try {
      const data = await agentService.getAgentMetrics(agentId, params);
      setMetrics(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [agentId]);

  useEffect(() => {
    fetchMetrics();
  }, [fetchMetrics]);

  return { metrics, loading, error, refetch: fetchMetrics };
}

export default useAgentData;
