/**
 * Agent Context - Simplified
 * Global state management for agents
 */

import { createContext, useContext, useReducer, useMemo } from 'react';

const AgentContext = createContext(null);

const ACTIONS = {
  SET_AGENTS: 'SET_AGENTS',
  ADD_AGENT: 'ADD_AGENT',
  UPDATE_AGENT: 'UPDATE_AGENT',
  REMOVE_AGENT: 'REMOVE_AGENT',
  SET_LOADING: 'SET_LOADING',
  SET_ERROR: 'SET_ERROR',
};

const initialState = {
  agents: [],
  loading: false,
  error: null,
};

function agentReducer(state, action) {
  switch (action.type) {
    case ACTIONS.SET_AGENTS:
      return { ...state, agents: action.payload, loading: false };
    
    case ACTIONS.ADD_AGENT:
      return { ...state, agents: [action.payload, ...state.agents] };
    
    case ACTIONS.UPDATE_AGENT:
      return {
        ...state,
        agents: state.agents.map(agent =>
          agent.id === action.payload.id ? { ...agent, ...action.payload } : agent
        ),
      };
    
    case ACTIONS.REMOVE_AGENT:
      return {
        ...state,
        agents: state.agents.filter(agent => agent.id !== action.payload),
      };
    
    case ACTIONS.SET_LOADING:
      return { ...state, loading: action.payload };
    
    case ACTIONS.SET_ERROR:
      return { ...state, error: action.payload, loading: false };
    
    default:
      return state;
  }
}

export function AgentProvider({ children }) {
  const [state, dispatch] = useReducer(agentReducer, initialState);

  const actions = useMemo(() => ({
    setAgents: (agents) => dispatch({ type: ACTIONS.SET_AGENTS, payload: agents }),
    addAgent: (agent) => dispatch({ type: ACTIONS.ADD_AGENT, payload: agent }),
    updateAgent: (agent) => dispatch({ type: ACTIONS.UPDATE_AGENT, payload: agent }),
    removeAgent: (id) => dispatch({ type: ACTIONS.REMOVE_AGENT, payload: id }),
    setLoading: (loading) => dispatch({ type: ACTIONS.SET_LOADING, payload: loading }),
    setError: (error) => dispatch({ type: ACTIONS.SET_ERROR, payload: error }),
    clearError: () => dispatch({ type: ACTIONS.SET_ERROR, payload: null }),
  }), []);

  const value = useMemo(() => ({ ...state, ...actions }), [state, actions]);

  return <AgentContext.Provider value={value}>{children}</AgentContext.Provider>;
}

export function useAgents() {
  const context = useContext(AgentContext);
  if (!context) throw new Error('useAgents must be used within AgentProvider');
  return context;
}

export default AgentContext;
