const express = require('express');
const router = express.Router();
const templateController = require('../controllers/templateController');
const { authenticatePassword } = require('../middleware/auth');

// Apply authentication to all routes
router.use(authenticatePassword);

router.get('/', templateController.getTemplate);
router.post('/', templateController.saveTemplate);
router.get('/variables', templateController.getTemplateVariables);

module.exports = router;
