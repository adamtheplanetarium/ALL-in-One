import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import io from 'socket.io-client';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

function CampaignDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [campaign, setCampaign] = useState(null);
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState([]);
  const [socket, setSocket] = useState(null);
  const [loading, setLoading] = useState(true);
  const [logsPage, setLogsPage] = useState(1);
  const [hasMoreLogs, setHasMoreLogs] = useState(true);

  useEffect(() => {
    fetchCampaignDetails();
    fetchLogs();
    
    // Setup WebSocket connection
    const newSocket = io(window.location.origin, {
      auth: { token: localStorage.getItem('token') }
    });
    
    setSocket(newSocket);

    newSocket.on('connected', (data) => {
      console.log('WebSocket connected:', data);
      // Subscribe to this campaign's updates
      newSocket.emit('subscribe_campaign', { campaign_id: id });
    });

    newSocket.on('campaign_update', (data) => {
      console.log('Campaign update received:', data);
      if (data.campaign_id === id) {
        // Update campaign stats in real-time
        setCampaign(prev => ({
          ...prev,
          emails_sent: data.emails_sent,
          emails_failed: data.emails_failed,
          status: data.status
        }));
        
        // Add to activity log
        if (data.log) {
          setLogs(prev => [data.log, ...prev]);
        }
      }
    });

    return () => {
      if (newSocket) {
        newSocket.emit('unsubscribe_campaign', { campaign_id: id });
        newSocket.disconnect();
      }
    };
  }, [id]);

  const fetchCampaignDetails = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`/api/campaigns/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCampaign(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching campaign:', error);
      setLoading(false);
    }
  };

  const fetchLogs = async (page = 1) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`/api/campaigns/${id}/logs?page=${page}&limit=50`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (page === 1) {
        setLogs(response.data.logs || []);
      } else {
        setLogs(prev => [...prev, ...(response.data.logs || [])]);
      }
      
      setHasMoreLogs(response.data.has_more || false);
    } catch (error) {
      console.error('Error fetching logs:', error);
    }
  };

  const handleStart = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`/api/campaigns/${id}/start`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchCampaignDetails();
    } catch (error) {
      alert('Error starting campaign: ' + error.response?.data?.error);
    }
  };

  const handlePause = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`/api/campaigns/${id}/pause`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchCampaignDetails();
    } catch (error) {
      alert('Error pausing campaign: ' + error.response?.data?.error);
    }
  };

  const handleResume = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`/api/campaigns/${id}/resume`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchCampaignDetails();
    } catch (error) {
      alert('Error resuming campaign: ' + error.response?.data?.error);
    }
  };

  const handleStop = async () => {
    if (!confirm('Are you sure you want to stop this campaign? This cannot be undone.')) return;
    
    try {
      const token = localStorage.getItem('token');
      await axios.post(`/api/campaigns/${id}/stop`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchCampaignDetails();
    } catch (error) {
      alert('Error stopping campaign: ' + error.response?.data?.error);
    }
  };

  if (loading || !campaign) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl">Loading campaign...</div>
      </div>
    );
  }

  const progress = campaign.total_recipients > 0 
    ? Math.round((campaign.emails_sent / campaign.total_recipients) * 100) 
    : 0;

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex justify-between items-start mb-8">
        <div>
          <Link to="/campaigns" className="text-blue-600 hover:underline mb-2 inline-block">
            ← Back to Campaigns
          </Link>
          <h1 className="text-3xl font-bold">{campaign.name}</h1>
          <p className="text-gray-600 mt-2">{campaign.subject}</p>
        </div>
        
        {/* Control Buttons */}
        <div className="flex space-x-2">
          {campaign.status === 'draft' && (
            <button
              onClick={handleStart}
              className="px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg font-semibold"
            >
              Start Campaign
            </button>
          )}
          
          {campaign.status === 'running' && (
            <>
              <button
                onClick={handlePause}
                className="px-6 py-3 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg font-semibold"
              >
                Pause
              </button>
              <button
                onClick={handleStop}
                className="px-6 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg font-semibold"
              >
                Stop
              </button>
            </>
          )}
          
          {campaign.status === 'paused' && (
            <>
              <button
                onClick={handleResume}
                className="px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg font-semibold"
              >
                Resume
              </button>
              <button
                onClick={handleStop}
                className="px-6 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg font-semibold"
              >
                Stop
              </button>
            </>
          )}
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-500 text-sm mb-2">Status</p>
          <p className="text-2xl font-bold capitalize">{campaign.status}</p>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-500 text-sm mb-2">Progress</p>
          <p className="text-2xl font-bold text-blue-600">{progress}%</p>
          <p className="text-sm text-gray-600 mt-1">
            {campaign.emails_sent} / {campaign.total_recipients}
          </p>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-500 text-sm mb-2">Success Rate</p>
          <p className="text-2xl font-bold text-green-600">
            {campaign.emails_sent > 0 
              ? Math.round((campaign.emails_sent / (campaign.emails_sent + campaign.emails_failed)) * 100) 
              : 0}%
          </p>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-500 text-sm mb-2">Failed</p>
          <p className="text-2xl font-bold text-red-600">{campaign.emails_failed}</p>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-xl font-semibold mb-4">Campaign Progress</h2>
        <div className="w-full bg-gray-200 rounded-full h-6 mb-2">
          <div
            className={`h-6 rounded-full transition-all flex items-center justify-end pr-3 text-white text-sm font-semibold ${
              campaign.status === 'completed' ? 'bg-blue-600' :
              campaign.status === 'paused' ? 'bg-yellow-500' :
              campaign.status === 'running' ? 'bg-green-600' : 'bg-gray-400'
            }`}
            style={{ width: `${progress}%` }}
          >
            {progress > 5 ? `${progress}%` : ''}
          </div>
        </div>
        <div className="flex justify-between text-sm text-gray-600 mt-2">
          <span>{campaign.emails_sent} sent</span>
          <span>{campaign.total_recipients - campaign.emails_sent} remaining</span>
        </div>
      </div>

      {/* Campaign Settings */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-xl font-semibold mb-4">Campaign Settings</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p className="text-gray-500 text-sm">Emails Per Hour</p>
            <p className="text-lg font-semibold">{campaign.emails_per_hour}</p>
          </div>
          <div>
            <p className="text-gray-500 text-sm">Thread Count</p>
            <p className="text-lg font-semibold">{campaign.thread_count}</p>
          </div>
          <div>
            <p className="text-gray-500 text-sm">SMTP Servers</p>
            <p className="text-lg font-semibold">{campaign.smtp_count}</p>
          </div>
          <div>
            <p className="text-gray-500 text-sm">FROM Addresses</p>
            <p className="text-lg font-semibold">{campaign.from_count}</p>
          </div>
          <div>
            <p className="text-gray-500 text-sm">Track Opens</p>
            <p className="text-lg font-semibold">{campaign.track_opens ? 'Yes' : 'No'}</p>
          </div>
          <div>
            <p className="text-gray-500 text-sm">Track Clicks</p>
            <p className="text-lg font-semibold">{campaign.track_clicks ? 'Yes' : 'No'}</p>
          </div>
        </div>
      </div>

      {/* Activity Log */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b">
          <h2 className="text-xl font-semibold">Activity Log</h2>
        </div>
        <div className="p-6">
          {logs.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No activity yet</p>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {logs.map((log, index) => (
                <div key={index} className="flex items-start space-x-3 text-sm">
                  <div className={`mt-1 w-2 h-2 rounded-full ${
                    log.level === 'success' ? 'bg-green-500' :
                    log.level === 'error' ? 'bg-red-500' :
                    log.level === 'warning' ? 'bg-yellow-500' : 'bg-blue-500'
                  }`}></div>
                  <div className="flex-1">
                    <p className="text-gray-800">{log.message}</p>
                    {log.to_address && (
                      <p className="text-gray-500 text-xs">To: {log.to_address}</p>
                    )}
                    <p className="text-gray-500 text-xs mt-1">
                      {new Date(log.timestamp).toLocaleString()}
                    </p>
                  </div>
                </div>
              ))}
              
              {hasMoreLogs && (
                <button
                  onClick={() => {
                    const nextPage = logsPage + 1;
                    setLogsPage(nextPage);
                    fetchLogs(nextPage);
                  }}
                  className="w-full py-2 text-blue-600 hover:text-blue-700 font-medium"
                >
                  Load More
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default CampaignDetails;
