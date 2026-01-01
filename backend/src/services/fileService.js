const fs = require('fs').promises;
const path = require('path');
const { BASIC_FOLDER_PATH } = require('../config/constants');

class FileService {
  constructor() {
    this.basePath = path.resolve(__dirname, '../../', BASIC_FOLDER_PATH);
  }

  getFilePath(filename) {
    return path.join(this.basePath, filename);
  }

  async readFile(filename) {
    try {
      const filePath = this.getFilePath(filename);
      const content = await fs.readFile(filePath, 'utf-8');
      return content;
    } catch (error) {
      throw new Error(`Failed to read file ${filename}: ${error.message}`);
    }
  }

  async writeFile(filename, content) {
    try {
      const filePath = this.getFilePath(filename);
      await fs.writeFile(filePath, content, 'utf-8');
      return true;
    } catch (error) {
      throw new Error(`Failed to write file ${filename}: ${error.message}`);
    }
  }

  async readLines(filename) {
    const content = await this.readFile(filename);
    return content.split('\n').filter(line => line.trim());
  }

  async writeLines(filename, lines) {
    const content = lines.join('\n');
    return await this.writeFile(filename, content);
  }

  async appendLine(filename, line) {
    try {
      const filePath = this.getFilePath(filename);
      await fs.appendFile(filePath, line + '\n', 'utf-8');
      return true;
    } catch (error) {
      throw new Error(`Failed to append to file ${filename}: ${error.message}`);
    }
  }

  async fileExists(filename) {
    try {
      const filePath = this.getFilePath(filename);
      await fs.access(filePath);
      return true;
    } catch {
      return false;
    }
  }

  async getFileStats(filename) {
    try {
      const filePath = this.getFilePath(filename);
      const stats = await fs.stat(filePath);
      return {
        size: stats.size,
        modified: stats.mtime,
        created: stats.birthtime
      };
    } catch (error) {
      return null;
    }
  }

  async countLines(filename) {
    try {
      const lines = await this.readLines(filename);
      return lines.length;
    } catch {
      return 0;
    }
  }

  // SMTP file operations
  async readSMTPServers() {
    try {
      const content = await this.readFile('smtp.txt');
      const lines = content.split('\n').filter(line => line.trim());
      
      // Skip header line
      const servers = lines.slice(1).map(line => {
        const parts = line.split(',').map(p => p.trim());
        if (parts.length >= 4) {
          return {
            host: parts[0],
            port: parseInt(parts[1]),
            username: parts[2],
            password: parts[3],
            status: 'active',
            failures: 0
          };
        }
        return null;
      }).filter(Boolean);
      
      return servers;
    } catch (error) {
      return [];
    }
  }

  async writeSMTPServers(servers) {
    const header = 'host,port,user,pass';
    const lines = [header, ...servers.map(s => 
      `${s.host},${s.port},${s.username},${s.password}`
    )];
    return await this.writeLines('smtp.txt', lines);
  }

  async addSMTPServer(server) {
    const servers = await this.readSMTPServers();
    servers.push(server);
    return await this.writeSMTPServers(servers);
  }

  async removeSMTPServer(host, username) {
    const servers = await this.readSMTPServers();
    const filtered = servers.filter(s => 
      !(s.host === host && s.username === username)
    );
    return await this.writeSMTPServers(filtered);
  }

  // Config.ini operations
  async readConfigIni() {
    const ini = require('ini');
    try {
      const content = await this.readFile('config.ini');
      return ini.parse(content);
    } catch (error) {
      throw new Error(`Failed to read config.ini: ${error.message}`);
    }
  }

  async writeConfigIni(config) {
    const ini = require('ini');
    try {
      const content = ini.stringify(config);
      return await this.writeFile('config.ini', content);
    } catch (error) {
      throw new Error(`Failed to write config.ini: ${error.message}`);
    }
  }

  async updateConfigSetting(section, key, value) {
    const config = await this.readConfigIni();
    if (!config[section]) {
      config[section] = {};
    }
    config[section][key] = value;
    return await this.writeConfigIni(config);
  }
}

module.exports = new FileService();
