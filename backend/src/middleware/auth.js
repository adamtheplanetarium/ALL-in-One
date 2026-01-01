const { PASSWORD } = require('../config/constants');

const authenticatePassword = (req, res, next) => {
  if (req.session && req.session.authenticated) {
    return next();
  }
  return res.status(401).json({ error: 'Unauthorized. Please login.' });
};

const login = (req, res) => {
  const { password } = req.body;
  
  if (password === PASSWORD) {
    req.session.authenticated = true;
    req.session.loginTime = new Date().toISOString();
    return res.json({ 
      success: true, 
      message: 'Login successful',
      loginTime: req.session.loginTime
    });
  }
  
  return res.status(401).json({ 
    success: false, 
    error: 'Invalid password' 
  });
};

const logout = (req, res) => {
  req.session.destroy((err) => {
    if (err) {
      return res.status(500).json({ error: 'Logout failed' });
    }
    res.json({ success: true, message: 'Logged out successfully' });
  });
};

const checkAuth = (req, res) => {
  if (req.session && req.session.authenticated) {
    return res.json({ 
      authenticated: true,
      loginTime: req.session.loginTime
    });
  }
  return res.json({ authenticated: false });
};

module.exports = {
  authenticatePassword,
  login,
  logout,
  checkAuth
};
