/**
 * Agent Context
 * Global state management for agents
 */

import { createContext, useContext, useReducer, useCallback } from 'react';

const AgentContext = createContext(null);

// Action types
const ACTIONS = {
  SET_AGENTS: 'SET_AGENTS',
  ADD_AGENT: 'ADD_AGENT',
  UPDATE_AGENT: 'UPDATE_AGENT',
  REMOVE_AGENT: 'REMOVE_AGENT',
  SET_LOADING: 'SET_LOADING',
  SET_ERROR: 'SET_ERROR',
  CLEAR_ERROR: 'CLEAR_ERROR',
  SET_SELECTED_AGENT: 'SET_SELECTED_AGENT',
};

// Initial state
const initialState = {
  agents: [],
  selectedAgent: null,
  loading: false,
  error: null,
};

// Reducer
function agentReducer(state, action) {
  switch (action.type) {
    case ACTIONS.SET_AGENTS:
      return {
        ...state,
        agents: action.payload,
        loading: false,
      };
    
    case ACTIONS.ADD_AGENT:
      return {
        ...state,
        agents: [action.payload, ...state.agents],
      };
    
    case ACTIONS.UPDATE_AGENT:
      return {
        ...state,
        agents: state.agents.map(agent =>
          agent.id === action.payload.id
            ? { ...agent, ...action.payload }
            : agent
        ),
        selectedAgent: state.selectedAgent?.id === action.payload.id
          ? { ...state.selectedAgent, ...action.payload }
          : state.selectedAgent,
      };
    
    case ACTIONS.REMOVE_AGENT:
      return {
        ...state,
        agents: state.agents.filter(agent => agent.id !== action.payload),
        selectedAgent: state.selectedAgent?.id === action.payload
          ? null
          : state.selectedAgent,
      };
    
    case ACTIONS.SET_LOADING:
      return {
        ...state,
        loading: action.payload,
      };
    
    case ACTIONS.SET_ERROR:
      return {
        ...state,
        error: action.payload,
        loading: false,
      };
    
    case ACTIONS.CLEAR_ERROR:
      return {
        ...state,
        error: null,
      };
    
    case ACTIONS.SET_SELECTED_AGENT:
      return {
        ...state,
        selectedAgent: action.payload,
      };
    
    default:
      return state;
  }
}

// Provider component
export function AgentProvider({ children }) {
  const [state, dispatch] = useReducer(agentReducer, initialState);

  const setAgents = useCallback((agents) => {
    dispatch({ type: ACTIONS.SET_AGENTS, payload: agents });
  }, []);

  const addAgent = useCallback((agent) => {
    dispatch({ type: ACTIONS.ADD_AGENT, payload: agent });
  }, []);

  const updateAgent = useCallback((agent) => {
    dispatch({ type: ACTIONS.UPDATE_AGENT, payload: agent });
  }, []);

  const removeAgent = useCallback((agentId) => {
    dispatch({ type: ACTIONS.REMOVE_AGENT, payload: agentId });
  }, []);

  const setLoading = useCallback((loading) => {
    dispatch({ type: ACTIONS.SET_LOADING, payload: loading });
  }, []);

  const setError = useCallback((error) => {
    dispatch({ type: ACTIONS.SET_ERROR, payload: error });
  }, []);

  const clearError = useCallback(() => {
    dispatch({ type: ACTIONS.CLEAR_ERROR });
  }, []);

  const setSelectedAgent = useCallback((agent) => {
    dispatch({ type: ACTIONS.SET_SELECTED_AGENT, payload: agent });
  }, []);

  const value = {
    ...state,
    setAgents,
    addAgent,
    updateAgent,
    removeAgent,
    setLoading,
    setError,
    clearError,
    setSelectedAgent,
  };

  return (
    <AgentContext.Provider value={value}>
      {children}
    </AgentContext.Provider>
  );
}

// Hook
export function useAgents() {
  const context = useContext(AgentContext);
  if (!context) {
    throw new Error('useAgents must be used within an AgentProvider');
  }
  return context;
}

export default AgentContext;
