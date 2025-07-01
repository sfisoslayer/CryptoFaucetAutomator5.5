import React, { useState, useEffect } from 'react';
import './App.css';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [sessionCount, setSessionCount] = useState(10);
  const [isRunning, setIsRunning] = useState(false);
  const [currentSession, setCurrentSession] = useState(null);
  const [walletStats, setWalletStats] = useState({
    total_balance: 0,
    total_claimed_today: 0,
    successful_claims: 0,
    failed_claims: 0,
    active_sessions: 0
  });
  const [claimLogs, setClaimLogs] = useState([]);
  const [faucetSites, setFaucetSites] = useState([]);
  const [sessionStatus, setSessionStatus] = useState(null);

  // Auto-refresh data every 5 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      fetchWalletStats();
      fetchClaimLogs();
      if (currentSession) {
        fetchSessionStatus(currentSession);
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [currentSession]);

  // Initial data load
  useEffect(() => {
    fetchWalletStats();
    fetchClaimLogs();
    fetchFaucetSites();
  }, []);

  const fetchWalletStats = async () => {
    try {
      const response = await axios.get(`${API}/wallet-stats`);
      setWalletStats(response.data);
    } catch (error) {
      console.error('Failed to fetch wallet stats:', error);
    }
  };

  const fetchClaimLogs = async () => {
    try {
      const response = await axios.get(`${API}/claim-logs?limit=50`);
      setClaimLogs(response.data);
    } catch (error) {
      console.error('Failed to fetch claim logs:', error);
    }
  };

  const fetchFaucetSites = async () => {
    try {
      const response = await axios.get(`${API}/faucet-sites`);
      setFaucetSites(response.data);
    } catch (error) {
      console.error('Failed to fetch faucet sites:', error);
    }
  };

  const fetchSessionStatus = async (sessionId) => {
    try {
      const response = await axios.get(`${API}/session-status/${sessionId}`);
      setSessionStatus(response.data);
    } catch (error) {
      console.error('Failed to fetch session status:', error);
    }
  };

  const startSession = async () => {
    try {
      const sessionConfig = {
        session_count: sessionCount,
        auto_withdrawal: true,
        withdrawal_threshold: 0.0000093,
        withdrawal_address: "bc1qzh55yrw9z4ve9zxy04xuw9mq838g5c06tqvrxk",
        proxy_enabled: true,
        captcha_solving: true
      };

      const response = await axios.post(`${API}/start-session`, sessionConfig);
      setCurrentSession(response.data.session_id);
      setIsRunning(true);
      
      alert(`Started ${sessionCount} claiming sessions!`);
    } catch (error) {
      console.error('Failed to start session:', error);
      alert('Failed to start session: ' + error.response?.data?.detail);
    }
  };

  const stopSession = async () => {
    if (!currentSession) return;

    try {
      await axios.delete(`${API}/stop-session/${currentSession}`);
      setIsRunning(false);
      setCurrentSession(null);
      setSessionStatus(null);
      alert('Session stopped!');
    } catch (error) {
      console.error('Failed to stop session:', error);
      alert('Failed to stop session');
    }
  };

  const formatBTC = (amount) => {
    return (amount || 0).toFixed(8);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'success': return 'text-green-500';
      case 'failed': return 'text-red-500';
      case 'captcha_failed': return 'text-yellow-500';
      default: return 'text-gray-500';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-5xl font-bold text-white mb-4">
            🚀 Crypto Faucet Auto-Claimer
          </h1>
          <p className="text-xl text-gray-300">
            Automated claiming from 100+ faucet sites with real BTC withdrawals
          </p>
        </div>

        {/* Wallet Stats Dashboard */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-6 mb-8">
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 text-center">
            <h3 className="text-lg font-semibold text-white mb-2">Total Balance</h3>
            <p className="text-3xl font-bold text-yellow-400">
              ₿ {formatBTC(walletStats.total_balance)}
            </p>
          </div>
          
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 text-center">
            <h3 className="text-lg font-semibold text-white mb-2">Today's Claims</h3>
            <p className="text-3xl font-bold text-green-400">
              ₿ {formatBTC(walletStats.total_claimed_today)}
            </p>
          </div>
          
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 text-center">
            <h3 className="text-lg font-semibold text-white mb-2">Successful</h3>
            <p className="text-3xl font-bold text-green-400">
              {walletStats.successful_claims}
            </p>
          </div>
          
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 text-center">
            <h3 className="text-lg font-semibold text-white mb-2">Failed</h3>
            <p className="text-3xl font-bold text-red-400">
              {walletStats.failed_claims}
            </p>
          </div>
          
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 text-center">
            <h3 className="text-lg font-semibold text-white mb-2">Active Sessions</h3>
            <p className="text-3xl font-bold text-blue-400">
              {walletStats.active_sessions}
            </p>
          </div>
        </div>

        {/* Session Control Panel */}
        <div className="bg-white/10 backdrop-blur-md rounded-xl p-8 mb-8">
          <h2 className="text-2xl font-bold text-white mb-6">Session Control</h2>
          
          <div className="flex flex-col md:flex-row gap-6 items-center">
            <div className="flex-1">
              <label className="block text-white text-lg font-semibold mb-4">
                Number of Sessions: {sessionCount}
              </label>
              <input
                type="range"
                min="1"
                max="10000"
                value={sessionCount}
                onChange={(e) => setSessionCount(parseInt(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
                disabled={isRunning}
              />
              <div className="flex justify-between text-gray-300 mt-2">
                <span>1</span>
                <span>5000</span>
                <span>10000</span>
              </div>
            </div>
            
            <div className="flex gap-4">
              {!isRunning ? (
                <button
                  onClick={startSession}
                  className="bg-green-600 hover:bg-green-700 text-white font-bold py-4 px-8 rounded-xl transition-colors text-lg"
                >
                  🚀 Start Claiming
                </button>
              ) : (
                <button
                  onClick={stopSession}
                  className="bg-red-600 hover:bg-red-700 text-white font-bold py-4 px-8 rounded-xl transition-colors text-lg"
                >
                  🛑 Stop Sessions
                </button>
              )}
            </div>
          </div>

          {/* Session Status */}
          {sessionStatus && (
            <div className="mt-6 p-4 bg-white/5 rounded-lg">
              <h3 className="text-lg font-semibold text-white mb-2">Current Session Status</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-gray-300">Status:</span>
                  <span className={`ml-2 font-semibold ${
                    sessionStatus.status === 'running' ? 'text-green-400' : 
                    sessionStatus.status === 'completed' ? 'text-blue-400' : 'text-red-400'
                  }`}>
                    {sessionStatus.status}
                  </span>
                </div>
                <div>
                  <span className="text-gray-300">Total Claims:</span>
                  <span className="ml-2 text-white font-semibold">
                    {sessionStatus.stats?.total_claims || 0}
                  </span>
                </div>
                <div>
                  <span className="text-gray-300">Successful:</span>
                  <span className="ml-2 text-green-400 font-semibold">
                    {sessionStatus.stats?.successful_claims || 0}
                  </span>
                </div>
                <div>
                  <span className="text-gray-300">Earned:</span>
                  <span className="ml-2 text-yellow-400 font-semibold">
                    ₿ {formatBTC(sessionStatus.stats?.total_earned)}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Two Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Recent Claims Log */}
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6">
            <h3 className="text-xl font-bold text-white mb-4">
              📊 Recent Claims ({claimLogs.length})
            </h3>
            <div className="max-h-96 overflow-y-auto">
              {claimLogs.length > 0 ? (
                <div className="space-y-2">
                  {claimLogs.map((log, index) => (
                    <div key={index} className="bg-white/5 rounded-lg p-3 text-sm">
                      <div className="flex justify-between items-center">
                        <span className="text-white font-medium">{log.faucet_name}</span>
                        <span className={`font-semibold ${getStatusColor(log.status)}`}>
                          {log.status}
                        </span>
                      </div>
                      {log.amount > 0 && (
                        <div className="text-yellow-400 font-mono">
                          +₿ {formatBTC(log.amount)}
                        </div>
                      )}
                      <div className="text-gray-400 text-xs">
                        {new Date(log.timestamp).toLocaleString()}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-gray-400 text-center py-8">
                  No claims yet. Start a session to begin claiming!
                </div>
              )}
            </div>
          </div>

          {/* Supported Faucet Sites */}
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6">
            <h3 className="text-xl font-bold text-white mb-4">
              🎯 Supported Faucets ({faucetSites.length})
            </h3>
            <div className="max-h-96 overflow-y-auto">
              <div className="grid gap-2">
                {faucetSites.map((site, index) => (
                  <div key={index} className="bg-white/5 rounded-lg p-3 flex justify-between items-center">
                    <div>
                      <span className="text-white font-medium">{site.name}</span>
                      <div className="text-gray-400 text-xs">
                        Cooldown: {site.cooldown}min
                      </div>
                    </div>
                    <div className="text-green-400 text-xs">
                      Active
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div className="mt-4 text-center">
              <div className="text-gray-300 text-sm">
                Auto-withdrawal at ₿ 0.0000093 to:
              </div>
              <div className="text-yellow-400 text-xs font-mono mt-1 break-all">
                bc1qzh55yrw9z4ve9zxy04xuw9mq838g5c06tqvrxk
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center mt-8 text-gray-400">
          <p>🔥 Automated crypto claiming with real blockchain withdrawals</p>
          <p className="text-sm mt-2">Updates every 5 seconds • Free proxy rotation • CAPTCHA solving enabled</p>
        </div>
      </div>
    </div>
  );
}

export default App;