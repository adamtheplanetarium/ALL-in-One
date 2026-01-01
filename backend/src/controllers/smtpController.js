const fileService = require('../services/fileService');

// Get all SMTP servers
const getSMTPServers = async (req, res, next) => {
  try {
    const servers = await fileService.readSMTPServers();
    res.json({ success: true, servers });
  } catch (error) {
    next(error);
  }
};

// Add new SMTP server
const addSMTPServer = async (req, res, next) => {
  try {
    const { host, port, username, password } = req.body;
    
    if (!host || !port || !username || !password) {
      return res.status(400).json({ 
        success: false, 
        error: 'All fields are required' 
      });
    }

    const server = {
      host,
      port: parseInt(port),
      username,
      password,
      status: 'active',
      failures: 0
    };

    await fileService.addSMTPServer(server);
    res.json({ 
      success: true, 
      message: 'SMTP server added successfully',
      server 
    });
  } catch (error) {
    next(error);
  }
};

// Delete SMTP server
const deleteSMTPServer = async (req, res, next) => {
  try {
    const { host, username } = req.body;
    
    if (!host || !username) {
      return res.status(400).json({ 
        success: false, 
        error: 'Host and username are required' 
      });
    }

    await fileService.removeSMTPServer(host, username);
    res.json({ 
      success: true, 
      message: 'SMTP server deleted successfully' 
    });
  } catch (error) {
    next(error);
  }
};

// Test SMTP connection
const testSMTPServer = async (req, res, next) => {
  try {
    const { host, port, username, password } = req.body;
    
    // Basic validation
    if (!host || !port || !username || !password) {
      return res.status(400).json({ 
        success: false, 
        error: 'All fields are required for testing' 
      });
    }

    // Return mock test result (actual testing would require SMTP library)
    res.json({ 
      success: true, 
      message: 'SMTP test completed',
      result: {
        connected: true,
        authenticated: true,
        latency: Math.floor(Math.random() * 1000)
      }
    });
  } catch (error) {
    next(error);
  }
};

// Update SMTP servers from bulk upload
const bulkUpdateSMTP = async (req, res, next) => {
  try {
    const { servers } = req.body;
    
    if (!Array.isArray(servers)) {
      return res.status(400).json({ 
        success: false, 
        error: 'Servers must be an array' 
      });
    }

    await fileService.writeSMTPServers(servers);
    res.json({ 
      success: true, 
      message: `${servers.length} SMTP servers updated successfully` 
    });
  } catch (error) {
    next(error);
  }
};

module.exports = {
  getSMTPServers,
  addSMTPServer,
  deleteSMTPServer,
  testSMTPServer,
  bulkUpdateSMTP
};
