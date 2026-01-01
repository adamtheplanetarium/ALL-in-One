const processManager = require('../services/processManager');
const fileService = require('../services/fileService');

// Start campaign
const startCampaign = async (req, res, next) => {
  try {
    const result = processManager.startCampaign((output) => {
      // Real-time output will be sent via WebSocket
      console.log('Campaign output:', output);
    });
    
    res.json(result);
  } catch (error) {
    res.status(400).json({ 
      success: false, 
      error: error.message 
    });
  }
};

// Stop campaign
const stopCampaign = async (req, res, next) => {
  try {
    const result = processManager.stopCampaign();
    res.json(result);
  } catch (error) {
    res.status(400).json({ 
      success: false, 
      error: error.message 
    });
  }
};

// Get campaign state
const getCampaignState = async (req, res, next) => {
  try {
    const state = processManager.getState();
    res.json({ success: true, ...state });
  } catch (error) {
    next(error);
  }
};

// Get campaign statistics
const getCampaignStatistics = async (req, res, next) => {
  try {
    const statistics = processManager.getStatistics();
    res.json({ success: true, statistics });
  } catch (error) {
    next(error);
  }
};

// Get campaign logs
const getCampaignLogs = async (req, res, next) => {
  try {
    const limit = parseInt(req.query.limit) || 100;
    const logs = processManager.getLogs(limit);
    res.json({ success: true, logs });
  } catch (error) {
    next(error);
  }
};

// Clear logs
const clearLogs = async (req, res, next) => {
  try {
    const result = processManager.clearLogs();
    res.json(result);
  } catch (error) {
    next(error);
  }
};

// Get campaign configuration
const getCampaignConfig = async (req, res, next) => {
  try {
    const config = await fileService.readConfigIni();
    res.json({ success: true, config });
  } catch (error) {
    next(error);
  }
};

// Update campaign configuration
const updateCampaignConfig = async (req, res, next) => {
  try {
    const { section, key, value } = req.body;
    
    if (!section || !key || value === undefined) {
      return res.status(400).json({ 
        success: false, 
        error: 'Section, key, and value are required' 
      });
    }

    await fileService.updateConfigSetting(section, key, value);
    res.json({ 
      success: true, 
      message: 'Configuration updated successfully' 
    });
  } catch (error) {
    next(error);
  }
};

// Update full configuration
const updateFullConfig = async (req, res, next) => {
  try {
    const { config } = req.body;
    
    if (!config) {
      return res.status(400).json({ 
        success: false, 
        error: 'Configuration object is required' 
      });
    }

    await fileService.writeConfigIni(config);
    res.json({ 
      success: true, 
      message: 'Configuration updated successfully' 
    });
  } catch (error) {
    next(error);
  }
};

module.exports = {
  startCampaign,
  stopCampaign,
  getCampaignState,
  getCampaignStatistics,
  getCampaignLogs,
  clearLogs,
  getCampaignConfig,
  updateCampaignConfig,
  updateFullConfig
};
