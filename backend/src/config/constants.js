require('dotenv').config();

module.exports = {
  PORT: process.env.PORT || 5000,
  PASSWORD: process.env.PASSWORD || '@OLDISGOLD2026@',
  SESSION_SECRET: process.env.SESSION_SECRET || 'supersecretkey12345',
  PYTHON_PATH: process.env.PYTHON_PATH || 'python',
  BASIC_FOLDER_PATH: process.env.BASIC_FOLDER_PATH || '../Basic',
  CORS_ORIGIN: process.env.CORS_ORIGIN || 'http://localhost:3000',
  NODE_ENV: process.env.NODE_ENV || 'development',
  
  // File paths
  CONFIG_FILE: 'config.ini',
  SMTP_FILE: 'smtp.txt',
  WORKING_SMTP_FILE: 'working_smtp.txt',
  EMAIL_LIST_FILE: 'emailx.txt',
  FROM_LIST_FILE: 'from.txt',
  
  // Campaign states
  CAMPAIGN_STATES: {
    IDLE: 'idle',
    RUNNING: 'running',
    PAUSED: 'paused',
    STOPPED: 'stopped',
    COMPLETED: 'completed'
  }
};
