const express = require('express');
const router = express.Router();
const smtpController = require('../controllers/smtpController');
const { authenticatePassword } = require('../middleware/auth');

// Apply authentication to all routes
router.use(authenticatePassword);

router.get('/', smtpController.getSMTPServers);
router.post('/', smtpController.addSMTPServer);
router.delete('/', smtpController.deleteSMTPServer);
router.post('/test', smtpController.testSMTPServer);
router.put('/bulk', smtpController.bulkUpdateSMTP);

module.exports = router;
