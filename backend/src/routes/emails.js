const express = require('express');
const router = express.Router();
const emailController = require('../controllers/emailController');
const { authenticatePassword } = require('../middleware/auth');

// Apply authentication to all routes
router.use(authenticatePassword);

router.get('/recipients', emailController.getRecipientEmails);
router.get('/from', emailController.getFromEmails);
router.get('/statistics', emailController.getEmailStatistics);
router.post('/recipients', emailController.uploadRecipientEmails);
router.post('/from', emailController.uploadFromEmails);
router.delete('/recipients', emailController.clearRecipientEmails);
router.delete('/from', emailController.clearFromEmails);

module.exports = router;
