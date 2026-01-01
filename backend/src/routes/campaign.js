const express = require('express');
const router = express.Router();
const campaignController = require('../controllers/campaignController');
const { authenticatePassword } = require('../middleware/auth');

// Apply authentication to all routes
router.use(authenticatePassword);

router.post('/start', campaignController.startCampaign);
router.post('/stop', campaignController.stopCampaign);
router.get('/state', campaignController.getCampaignState);
router.get('/statistics', campaignController.getCampaignStatistics);
router.get('/logs', campaignController.getCampaignLogs);
router.delete('/logs', campaignController.clearLogs);
router.get('/config', campaignController.getCampaignConfig);
router.put('/config', campaignController.updateCampaignConfig);
router.put('/config/full', campaignController.updateFullConfig);

module.exports = router;
