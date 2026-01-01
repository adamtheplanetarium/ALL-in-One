const fileService = require('../services/fileService');

// Get recipient emails list
const getRecipientEmails = async (req, res, next) => {
  try {
    const emails = await fileService.readLines('emailx.txt');
    const count = emails.length;
    
    res.json({ 
      success: true, 
      count,
      emails: emails.slice(0, 100) // Return first 100 for preview
    });
  } catch (error) {
    next(error);
  }
};

// Get from emails list
const getFromEmails = async (req, res, next) => {
  try {
    const emails = await fileService.readLines('from.txt');
    const count = emails.length;
    
    res.json({ 
      success: true, 
      count,
      emails: emails.slice(0, 100) // Return first 100 for preview
    });
  } catch (error) {
    next(error);
  }
};

// Upload recipient emails
const uploadRecipientEmails = async (req, res, next) => {
  try {
    const { emails } = req.body;
    
    if (!emails || !Array.isArray(emails)) {
      return res.status(400).json({ 
        success: false, 
        error: 'Emails array is required' 
      });
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const validEmails = emails.filter(email => emailRegex.test(email.trim()));
    
    await fileService.writeLines('emailx.txt', validEmails);
    
    res.json({ 
      success: true, 
      message: `${validEmails.length} recipient emails uploaded successfully`,
      count: validEmails.length
    });
  } catch (error) {
    next(error);
  }
};

// Upload from emails
const uploadFromEmails = async (req, res, next) => {
  try {
    const { emails } = req.body;
    
    if (!emails || !Array.isArray(emails)) {
      return res.status(400).json({ 
        success: false, 
        error: 'Emails array is required' 
      });
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const validEmails = emails.filter(email => emailRegex.test(email.trim()));
    
    await fileService.writeLines('from.txt', validEmails);
    
    res.json({ 
      success: true, 
      message: `${validEmails.length} from emails uploaded successfully`,
      count: validEmails.length
    });
  } catch (error) {
    next(error);
  }
};

// Clear recipient emails
const clearRecipientEmails = async (req, res, next) => {
  try {
    await fileService.writeLines('emailx.txt', []);
    res.json({ 
      success: true, 
      message: 'Recipient emails cleared' 
    });
  } catch (error) {
    next(error);
  }
};

// Clear from emails
const clearFromEmails = async (req, res, next) => {
  try {
    await fileService.writeLines('from.txt', []);
    res.json({ 
      success: true, 
      message: 'From emails cleared' 
    });
  } catch (error) {
    next(error);
  }
};

// Get email statistics
const getEmailStatistics = async (req, res, next) => {
  try {
    const recipientCount = await fileService.countLines('emailx.txt');
    const fromCount = await fileService.countLines('from.txt');
    
    res.json({ 
      success: true, 
      statistics: {
        recipientCount,
        fromCount
      }
    });
  } catch (error) {
    next(error);
  }
};

module.exports = {
  getRecipientEmails,
  getFromEmails,
  uploadRecipientEmails,
  uploadFromEmails,
  clearRecipientEmails,
  clearFromEmails,
  getEmailStatistics
};
