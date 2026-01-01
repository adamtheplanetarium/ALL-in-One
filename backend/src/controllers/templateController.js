const fileService = require('../services/fileService');
const path = require('path');

// Get email template
const getTemplate = async (req, res, next) => {
  try {
    const config = await fileService.readConfigIni();
    const letterPath = config.Settings.LETTERPATH || 'ma.html';
    
    let content = '';
    const exists = await fileService.fileExists(letterPath);
    
    if (exists) {
      content = await fileService.readFile(letterPath);
    }
    
    res.json({ 
      success: true, 
      template: content,
      filename: letterPath
    });
  } catch (error) {
    next(error);
  }
};

// Save email template
const saveTemplate = async (req, res, next) => {
  try {
    const { content, filename } = req.body;
    
    if (!content) {
      return res.status(400).json({ 
        success: false, 
        error: 'Template content is required' 
      });
    }

    const templateFile = filename || 'ma.html';
    await fileService.writeFile(templateFile, content);
    
    // Update config.ini with new template path
    await fileService.updateConfigSetting('Settings', 'LETTERPATH', templateFile);
    
    res.json({ 
      success: true, 
      message: 'Template saved successfully',
      filename: templateFile
    });
  } catch (error) {
    next(error);
  }
};

// Get available template variables
const getTemplateVariables = async (req, res, next) => {
  try {
    const variables = [
      {
        name: 'LINKREDIRECT',
        description: 'URL to be shortened and used as redirect link',
        example: 'https://example.com/page'
      },
      {
        name: 'IMGREDIRECT',
        description: 'Image URL to be shortened',
        example: 'https://example.com/image.jpg'
      },
      {
        name: 'RANDOM',
        description: 'Random 6-digit number',
        example: '123456'
      },
      {
        name: 'CapitalS',
        description: 'Capitalized domain from SMTP sender',
        example: 'Gmail'
      },
      {
        name: 'randomchar',
        description: 'Random 5-digit number for sender name',
        example: '54321'
      },
      {
        name: 'DATEX',
        description: 'Current date formatted',
        example: 'Wednesday, January 01, 2026'
      }
    ];
    
    res.json({ success: true, variables });
  } catch (error) {
    next(error);
  }
};

module.exports = {
  getTemplate,
  saveTemplate,
  getTemplateVariables
};
