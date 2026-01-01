import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';

function Campaigns() {
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // 'all', 'draft', 'running', 'paused', 'completed', 'stopped'
  const navigate = useNavigate();

  useEffect(() => {
    fetchCampaigns();
    const interval = setInterval(fetchCampaigns, 5000); // Auto-refresh
    return () => clearInterval(interval);
  }, [filter]);

  const fetchCampaigns = async () => {
    try {
      const token = localStorage.getItem('token');
      const url = filter === 'all' ? '/api/campaigns' : `/api/campaigns?status=${filter}`;
      
      const response = await axios.get(url, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setCampaigns(response.data.campaigns || []);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching campaigns:', error);
      setLoading(false);
    }
  };

  const deleteCampaign = async (id) => {
    if (!confirm('Are you sure you want to delete this campaign?')) return;
    
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`/api/campaigns/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchCampaigns();
    } catch (error) {
      alert('Error deleting campaign: ' + error.response?.data?.error);
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      draft: 'bg-gray-100 text-gray-800',
      running: 'bg-green-100 text-green-800',
      paused: 'bg-yellow-100 text-yellow-800',
      completed: 'bg-blue-100 text-blue-800',
      stopped: 'bg-red-100 text-red-800',
      error: 'bg-red-100 text-red-800'
    };
    
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${styles[status] || styles.draft}`}>
        {status.toUpperCase()}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl">Loading campaigns...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Email Campaigns</h1>
        <Link
          to="/campaigns/new"
          className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold flex items-center space-x-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          <span>New Campaign</span>
        </Link>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow mb-6 p-4">
        <div className="flex space-x-2 overflow-x-auto">
          {['all', 'draft', 'running', 'paused', 'completed', 'stopped'].map(status => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={`px-4 py-2 rounded-lg font-medium whitespace-nowrap ${
                filter === status
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Campaigns List */}
      {campaigns.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <svg className="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          <h3 className="text-xl font-semibold text-gray-700 mb-2">No campaigns found</h3>
          <p className="text-gray-500 mb-6">Get started by creating your first email campaign</p>
          <Link
            to="/campaigns/new"
            className="inline-block bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold"
          >
            Create Campaign
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6">
          {campaigns.map(campaign => (
            <div key={campaign.id} className="bg-white rounded-lg shadow hover:shadow-lg transition">
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <Link
                        to={`/campaigns/${campaign.id}`}
                        className="text-xl font-semibold text-gray-800 hover:text-blue-600"
                      >
                        {campaign.name}
                      </Link>
                      {getStatusBadge(campaign.status)}
                    </div>
                    <p className="text-gray-600 text-sm mb-3">{campaign.subject}</p>
                    <div className="flex items-center space-x-6 text-sm text-gray-500">
                      <span>📧 {campaign.total_recipients} recipients</span>
                      <span>✉️ {campaign.smtp_count} SMTP servers</span>
                      <span>📤 {campaign.from_count} FROM addresses</span>
                      <span>⏱️ {campaign.emails_per_hour} emails/hour</span>
                    </div>
                  </div>
                  
                  <div className="flex space-x-2 ml-4">
                    <Link
                      to={`/campaigns/${campaign.id}`}
                      className="px-4 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 font-medium"
                    >
                      View
                    </Link>
                    <button
                      onClick={() => deleteCampaign(campaign.id)}
                      className="px-4 py-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 font-medium"
                    >
                      Delete
                    </button>
                  </div>
                </div>

                {/* Progress Bar */}
                {campaign.status === 'running' || campaign.status === 'paused' || campaign.status === 'completed' ? (
                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span className="text-gray-600">
                        Progress: {campaign.emails_sent} / {campaign.total_recipients} sent
                      </span>
                      <span className="font-semibold text-gray-800">
                        {Math.round((campaign.emails_sent / campaign.total_recipients) * 100)}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div
                        className={`h-3 rounded-full transition-all ${
                          campaign.status === 'completed' ? 'bg-blue-600' :
                          campaign.status === 'paused' ? 'bg-yellow-500' : 'bg-green-600'
                        }`}
                        style={{ width: `${(campaign.emails_sent / campaign.total_recipients) * 100}%` }}
                      ></div>
                    </div>
                    
                    {campaign.emails_failed > 0 && (
                      <p className="text-red-600 text-sm mt-2">
                        ⚠️ {campaign.emails_failed} failed
                      </p>
                    )}
                  </div>
                ) : null}

                {/* Timestamps */}
                <div className="mt-4 pt-4 border-t flex justify-between text-xs text-gray-500">
                  <span>Created: {new Date(campaign.created_at).toLocaleDateString()}</span>
                  {campaign.started_at && (
                    <span>Started: {new Date(campaign.started_at).toLocaleString()}</span>
                  )}
                  {campaign.completed_at && (
                    <span>Completed: {new Date(campaign.completed_at).toLocaleString()}</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Campaigns;
