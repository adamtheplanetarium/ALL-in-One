import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../services/api';
import socketService from '../services/socket';

const AppContext = createContext();

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within AppProvider');
  }
  return context;
};

export const AppProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [campaignState, setCampaignState] = useState({
    state: 'idle',
    statistics: {},
    isRunning: false,
  });
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    checkAuth();
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      connectWebSocket();
    } else {
      socketService.disconnect();
    }
  }, [isAuthenticated]);

  const checkAuth = async () => {
    try {
      const response = await authAPI.checkAuth();
      setIsAuthenticated(response.data.authenticated);
    } catch (error) {
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (password) => {
    try {
      await authAPI.login(password);
      setIsAuthenticated(true);
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.error || 'Login failed' 
      };
    }
  };

  const logout = async () => {
    try {
      await authAPI.logout();
      setIsAuthenticated(false);
      socketService.disconnect();
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  const connectWebSocket = () => {
    const socket = socketService.connect();

    socket.on('campaign:state', (data) => {
      setCampaignState(data);
    });

    socket.on('campaign:started', (data) => {
      setCampaignState(prev => ({ ...prev, ...data }));
    });

    socket.on('campaign:progress', (data) => {
      setCampaignState(prev => ({
        ...prev,
        statistics: { ...prev.statistics, ...data },
      }));
    });

    socket.on('campaign:completed', (data) => {
      setCampaignState(prev => ({ ...prev, ...data }));
    });

    socket.on('campaign:stopped', (data) => {
      setCampaignState(prev => ({ ...prev, ...data }));
    });

    socket.on('log:new', (log) => {
      setLogs(prev => [...prev.slice(-999), log]);
    });

    socket.on('logs:history', (logsData) => {
      setLogs(logsData);
    });

    socket.on('campaign:statistics', (statistics) => {
      setCampaignState(prev => ({ ...prev, statistics }));
    });
  };

  const value = {
    isAuthenticated,
    isLoading,
    login,
    logout,
    campaignState,
    logs,
    setLogs,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};
