import React, { useState } from 'react';
import { Card, Input, Button, message, Space } from 'antd';
import { LockOutlined, MailOutlined } from '@ant-design/icons';
import { useApp } from '../../context/AppContext';
import './Login.css';

const Login = () => {
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useApp();

  const handleLogin = async () => {
    if (!password) {
      message.error('Please enter password');
      return;
    }

    setLoading(true);
    const result = await login(password);
    setLoading(false);

    if (result.success) {
      message.success('Login successful!');
    } else {
      message.error(result.error);
      setPassword('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleLogin();
    }
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <Card className="login-card">
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <div className="login-header">
              <MailOutlined className="login-icon" />
              <h1>ALL-in-One</h1>
              <p>Email Portal</p>
            </div>
            
            <Input.Password
              size="large"
              prefix={<LockOutlined />}
              placeholder="Enter Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={loading}
            />
            
            <Button
              type="primary"
              size="large"
              block
              loading={loading}
              onClick={handleLogin}
            >
              Login
            </Button>
          </Space>
        </Card>
      </div>
    </div>
  );
};

export default Login;
