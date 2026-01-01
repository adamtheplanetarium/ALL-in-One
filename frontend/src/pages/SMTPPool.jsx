import { useState, useEffect } from 'react';
import axios from 'axios';

function SMTPPool() {
  const [smtps, setSmtps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [showBulkImport, setShowBulkImport] = useState(false);
  const [bulkText, setBulkText] = useState('');
  const [newSmtp, setNewSmtp] = useState({
    host: '',
    port: 587,
    username: '',
    password: '',
    use_tls: true,
    name: ''
  });

  useEffect(() => {
    fetchSmtps();
  }, []);

  const fetchSmtps = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('/api/smtp', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSmtps(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching SMTPs:', error);
      setLoading(false);
    }
  };

  const handleAddSmtp = async (e) => {
    e.preventDefault();
    
    try {
      const token = localStorage.getItem('token');
      await axios.post('/api/smtp', newSmtp, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setNewSmtp({ host: '', port: 587, username: '', password: '', use_tls: true, name: '' });
      setShowAddForm(false);
      fetchSmtps();
    } catch (error) {
      alert('Error adding SMTP: ' + error.response?.data?.error);
    }
  };

  const handleBulkImport = async (e) => {
    e.preventDefault();
    
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post('/api/smtp/bulk-import', {
        smtp_list: bulkText
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      alert(response.data.message);
      setBulkText('');
      setShowBulkImport(false);
      fetchSmtps();
    } catch (error) {
      alert('Error importing SMTPs: ' + error.response?.data?.error);
    }
  };

  const testSmtp = async (id) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`/api/smtp/${id}/test`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      alert('SMTP connection successful!');
    } catch (error) {
      alert('SMTP test failed: ' + error.response?.data?.error);
    }
  };

  const deleteSmtp = async (id) => {
    if (!confirm('Are you sure you want to delete this SMTP server?')) return;
    
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`/api/smtp/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchSmtps();
    } catch (error) {
      alert('Error deleting SMTP: ' + error.response?.data?.error);
    }
  };

  const resetFailures = async () => {
    if (!confirm('Reset failure counts for all SMTP servers?')) return;
    
    try {
      const token = localStorage.getItem('token');
      await axios.post('/api/smtp/reset-failures', {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      alert('Failure counts reset successfully');
      fetchSmtps();
    } catch (error) {
      alert('Error resetting failures: ' + error.response?.data?.error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl">Loading SMTP servers...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">SMTP Pool</h1>
        <div className="flex space-x-3">
          <button
            onClick={() => setShowBulkImport(true)}
            className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg font-semibold"
          >
            Bulk Import
          </button>
          <button
            onClick={() => setShowAddForm(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold"
          >
            + Add SMTP
          </button>
          {smtps.length > 0 && (
            <button
              onClick={resetFailures}
              className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-3 rounded-lg font-semibold"
            >
              Reset Failures
            </button>
          )}
        </div>
      </div>

      {/* Stats Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-500 text-sm mb-2">Total SMTP Servers</p>
          <p className="text-3xl font-bold">{smtps.length}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-500 text-sm mb-2">Active</p>
          <p className="text-3xl font-bold text-green-600">
            {smtps.filter(s => !s.disabled).length}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-500 text-sm mb-2">Disabled</p>
          <p className="text-3xl font-bold text-red-600">
            {smtps.filter(s => s.disabled).length}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-500 text-sm mb-2">Total Sent</p>
          <p className="text-3xl font-bold text-blue-600">
            {smtps.reduce((sum, s) => sum + (s.successes || 0), 0)}
          </p>
        </div>
      </div>

      {/* Bulk Import Modal */}
      {showBulkImport && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-8 max-w-2xl w-full mx-4">
            <h2 className="text-2xl font-bold mb-4">Bulk Import SMTP Servers</h2>
            <form onSubmit={handleBulkImport}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  SMTP List (one per line)
                </label>
                <p className="text-sm text-gray-500 mb-2">
                  Format: host,port,username,password OR username:password:host:port
                </p>
                <textarea
                  value={bulkText}
                  onChange={(e) => setBulkText(e.target.value)}
                  className="w-full px-4 py-2 border rounded-lg h-64 font-mono text-sm"
                  placeholder="smtp.example.com,587,user@example.com,password&#10;user:pass:smtp.example.com:587"
                  required
                />
              </div>
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowBulkImport(false)}
                  className="px-6 py-2 border rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Import
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add SMTP Modal */}
      {showAddForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4">
            <h2 className="text-2xl font-bold mb-4">Add SMTP Server</h2>
            <form onSubmit={handleAddSmtp}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Name (optional)</label>
                  <input
                    type="text"
                    value={newSmtp.name}
                    onChange={(e) => setNewSmtp({...newSmtp, name: e.target.value})}
                    className="w-full px-4 py-2 border rounded-lg"
                    placeholder="My SMTP Server"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Host*</label>
                  <input
                    type="text"
                    value={newSmtp.host}
                    onChange={(e) => setNewSmtp({...newSmtp, host: e.target.value})}
                    className="w-full px-4 py-2 border rounded-lg"
                    placeholder="smtp.example.com"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Port*</label>
                  <input
                    type="number"
                    value={newSmtp.port}
                    onChange={(e) => setNewSmtp({...newSmtp, port: parseInt(e.target.value)})}
                    className="w-full px-4 py-2 border rounded-lg"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Username*</label>
                  <input
                    type="text"
                    value={newSmtp.username}
                    onChange={(e) => setNewSmtp({...newSmtp, username: e.target.value})}
                    className="w-full px-4 py-2 border rounded-lg"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Password*</label>
                  <input
                    type="password"
                    value={newSmtp.password}
                    onChange={(e) => setNewSmtp({...newSmtp, password: e.target.value})}
                    className="w-full px-4 py-2 border rounded-lg"
                    required
                  />
                </div>
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    checked={newSmtp.use_tls}
                    onChange={(e) => setNewSmtp({...newSmtp, use_tls: e.target.checked})}
                    className="mr-2"
                  />
                  <label className="text-sm font-medium text-gray-700">Use TLS</label>
                </div>
              </div>
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  type="button"
                  onClick={() => setShowAddForm(false)}
                  className="px-6 py-2 border rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Add Server
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* SMTP List */}
      {smtps.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <svg className="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
          </svg>
          <h3 className="text-xl font-semibold text-gray-700 mb-2">No SMTP servers configured</h3>
          <p className="text-gray-500 mb-6">Add SMTP servers to start sending emails</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {smtps.map(smtp => (
            <div key={smtp.id} className={`bg-white rounded-lg shadow p-6 ${smtp.disabled ? 'opacity-60' : ''}`}>
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h3 className="font-semibold text-lg">{smtp.name || smtp.host}</h3>
                    {smtp.disabled && (
                      <span className="px-2 py-1 bg-red-100 text-red-800 rounded-full text-xs font-semibold">
                        DISABLED
                      </span>
                    )}
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-600">
                    <div>
                      <p className="text-gray-500">Host</p>
                      <p className="font-medium">{smtp.host}:{smtp.port}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Username</p>
                      <p className="font-medium">{smtp.username}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Successes</p>
                      <p className="font-medium text-green-600">{smtp.successes || 0}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Failures</p>
                      <p className="font-medium text-red-600">{smtp.failures || 0}</p>
                    </div>
                  </div>
                  {smtp.last_error && (
                    <p className="text-red-600 text-sm mt-2">⚠️ {smtp.last_error}</p>
                  )}
                </div>
                <div className="flex space-x-2 ml-4">
                  <button
                    onClick={() => testSmtp(smtp.id)}
                    className="px-4 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 font-medium"
                  >
                    Test
                  </button>
                  <button
                    onClick={() => deleteSmtp(smtp.id)}
                    className="px-4 py-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 font-medium"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default SMTPPool;
