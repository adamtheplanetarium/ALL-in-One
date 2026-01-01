const processManager = require('../services/processManager');

function setupWebSocket(io) {
  // Set the socket.io instance in process manager
  processManager.setSocketIO(io);

  io.on('connection', (socket) => {
    console.log('Client connected:', socket.id);

    // Send current state on connection
    socket.emit('campaign:state', processManager.getState());
    socket.emit('campaign:statistics', processManager.getStatistics());
    socket.emit('logs:history', processManager.getLogs(50));

    // Handle disconnect
    socket.on('disconnect', () => {
      console.log('Client disconnected:', socket.id);
    });

    // Client requests current state
    socket.on('request:state', () => {
      socket.emit('campaign:state', processManager.getState());
    });

    // Client requests statistics
    socket.on('request:statistics', () => {
      socket.emit('campaign:statistics', processManager.getStatistics());
    });

    // Client requests logs
    socket.on('request:logs', (limit = 100) => {
      socket.emit('logs:history', processManager.getLogs(limit));
    });
  });
}

module.exports = setupWebSocket;
