const { spawn } = require('child_process');
const path = require('path');
const { PYTHON_PATH, BASIC_FOLDER_PATH, CAMPAIGN_STATES } = require('../config/constants');

class ProcessManager {
  constructor() {
    this.currentProcess = null;
    this.campaignState = CAMPAIGN_STATES.IDLE;
    this.logs = [];
    this.statistics = {
      totalSent: 0,
      totalFailed: 0,
      totalEmails: 0,
      startTime: null,
      endTime: null,
      currentEmail: null,
      smtpFailures: {}
    };
    this.io = null;
  }

  setSocketIO(io) {
    this.io = io;
  }

  emitUpdate(event, data) {
    if (this.io) {
      this.io.emit(event, data);
    }
  }

  addLog(message, type = 'info') {
    const logEntry = {
      timestamp: new Date().toISOString(),
      message,
      type
    };
    this.logs.push(logEntry);
    
    // Keep only last 1000 logs in memory
    if (this.logs.length > 1000) {
      this.logs = this.logs.slice(-1000);
    }
    
    this.emitUpdate('log:new', logEntry);
    return logEntry;
  }

  startCampaign(callback) {
    if (this.currentProcess) {
      throw new Error('Campaign already running');
    }

    this.campaignState = CAMPAIGN_STATES.RUNNING;
    this.statistics.startTime = new Date().toISOString();
    this.statistics.totalSent = 0;
    this.statistics.totalFailed = 0;
    this.logs = [];

    const scriptPath = path.resolve(__dirname, '../../', BASIC_FOLDER_PATH, 'mainnotall.py');
    const workingDir = path.resolve(__dirname, '../../', BASIC_FOLDER_PATH);

    this.addLog('Starting email campaign...', 'info');
    this.emitUpdate('campaign:started', { state: this.campaignState });

    this.currentProcess = spawn(PYTHON_PATH, [scriptPath], {
      cwd: workingDir,
      env: process.env
    });

    this.currentProcess.stdout.on('data', (data) => {
      const output = data.toString();
      this.parseOutput(output);
      
      if (callback) {
        callback({ type: 'stdout', data: output });
      }
    });

    this.currentProcess.stderr.on('data', (data) => {
      const error = data.toString();
      this.addLog(error, 'error');
      
      if (callback) {
        callback({ type: 'stderr', data: error });
      }
    });

    this.currentProcess.on('close', (code) => {
      this.addLog(`Campaign process exited with code ${code}`, code === 0 ? 'info' : 'error');
      this.campaignState = code === 0 ? CAMPAIGN_STATES.COMPLETED : CAMPAIGN_STATES.STOPPED;
      this.statistics.endTime = new Date().toISOString();
      this.currentProcess = null;
      
      this.emitUpdate('campaign:completed', { 
        state: this.campaignState,
        statistics: this.statistics
      });
      
      if (callback) {
        callback({ type: 'close', code });
      }
    });

    this.currentProcess.on('error', (error) => {
      this.addLog(`Process error: ${error.message}`, 'error');
      this.campaignState = CAMPAIGN_STATES.STOPPED;
      this.currentProcess = null;
      
      if (callback) {
        callback({ type: 'error', error: error.message });
      }
    });

    return {
      success: true,
      message: 'Campaign started',
      pid: this.currentProcess.pid
    };
  }

  stopCampaign() {
    if (!this.currentProcess) {
      throw new Error('No campaign is running');
    }

    this.addLog('Stopping campaign...', 'info');
    
    try {
      this.currentProcess.kill('SIGTERM');
      
      setTimeout(() => {
        if (this.currentProcess) {
          this.currentProcess.kill('SIGKILL');
        }
      }, 5000);

      this.campaignState = CAMPAIGN_STATES.STOPPED;
      this.statistics.endTime = new Date().toISOString();
      this.emitUpdate('campaign:stopped', { state: this.campaignState });
      
      return { success: true, message: 'Campaign stopped' };
    } catch (error) {
      throw new Error(`Failed to stop campaign: ${error.message}`);
    }
  }

  parseOutput(output) {
    // Parse Python script output to extract information
    const lines = output.split('\n');
    
    for (const line of lines) {
      // Detect successful send
      if (line.includes('SENT ')) {
        const emailMatch = line.match(/SENT\s+([^\s]+)/);
        if (emailMatch) {
          this.statistics.totalSent++;
          this.statistics.currentEmail = emailMatch[1];
          this.addLog(`Successfully sent to ${emailMatch[1]}`, 'success');
          
          this.emitUpdate('campaign:progress', {
            totalSent: this.statistics.totalSent,
            totalFailed: this.statistics.totalFailed,
            currentEmail: this.statistics.currentEmail
          });
        }
      }
      
      // Detect failed send
      if (line.includes('Failed ')) {
        const emailMatch = line.match(/Failed\s+([^\s]+)/);
        if (emailMatch) {
          this.statistics.totalFailed++;
          this.addLog(`Failed to send to ${emailMatch[1]}`, 'error');
          
          this.emitUpdate('campaign:progress', {
            totalSent: this.statistics.totalSent,
            totalFailed: this.statistics.totalFailed
          });
        }
      }
      
      // Detect SMTP server disabled
      if (line.includes('DISABLED') || line.includes('already failed')) {
        const serverMatch = line.match(/([^\s]+:\d+)/);
        if (serverMatch) {
          const server = serverMatch[1];
          this.statistics.smtpFailures[server] = (this.statistics.smtpFailures[server] || 0) + 1;
          this.addLog(`SMTP server ${server} disabled`, 'warning');
          
          this.emitUpdate('smtp:disabled', {
            server,
            failures: this.statistics.smtpFailures[server]
          });
        }
      }
      
      // Detect loaded SMTP servers count
      if (line.includes('Loaded') && line.includes('SMTP servers')) {
        const countMatch = line.match(/Loaded\s+(\d+)\s+SMTP/);
        if (countMatch) {
          this.addLog(`Loaded ${countMatch[1]} SMTP servers`, 'info');
        }
      }
      
      // Detect total emails sent at completion
      if (line.includes('Total emails sent:')) {
        const totalMatch = line.match(/Total emails sent:\s+(\d+)/);
        if (totalMatch) {
          this.statistics.totalSent = parseInt(totalMatch[1]);
          this.addLog(`Campaign completed. Total emails sent: ${totalMatch[1]}`, 'success');
        }
      }
    }
  }

  getState() {
    return {
      state: this.campaignState,
      statistics: this.statistics,
      isRunning: this.currentProcess !== null,
      pid: this.currentProcess ? this.currentProcess.pid : null
    };
  }

  getLogs(limit = 100) {
    return this.logs.slice(-limit);
  }

  clearLogs() {
    this.logs = [];
    return { success: true, message: 'Logs cleared' };
  }

  getStatistics() {
    return this.statistics;
  }
}

module.exports = new ProcessManager();
