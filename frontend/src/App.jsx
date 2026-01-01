import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, Spin } from 'antd';
import { AppProvider, useApp } from './context/AppContext';
import Login from './components/Auth/Login';
import MainLayout from './components/Layout/MainLayout';
import Dashboard from './components/Dashboard/Dashboard';
import SMTPManagement from './components/SMTP/SMTPManagement';
import EmailListManagement from './components/Emails/EmailListManagement';
import TemplateEditor from './components/Template/TemplateEditor';
import CampaignSettings from './components/Campaign/CampaignSettings';

const PrivateRoute = ({ children }) => {
  const { isAuthenticated, isLoading } = useApp();

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Spin size="large" />
      </div>
    );
  }

  return isAuthenticated ? children : <Navigate to="/login" />;
};

const AppRoutes = () => {
  const { isAuthenticated } = useApp();

  return (
    <Router>
      <Routes>
        <Route
          path="/login"
          element={isAuthenticated ? <Navigate to="/" /> : <Login />}
        />
        <Route
          path="/*"
          element={
            <PrivateRoute>
              <MainLayout>
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/smtp" element={<SMTPManagement />} />
                  <Route path="/emails" element={<EmailListManagement />} />
                  <Route path="/template" element={<TemplateEditor />} />
                  <Route path="/campaign" element={<CampaignSettings />} />
                  <Route path="/settings" element={<CampaignSettings />} />
                </Routes>
              </MainLayout>
            </PrivateRoute>
          }
        />
      </Routes>
    </Router>
  );
};

function App() {
  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#667eea',
        },
      }}
    >
      <AppProvider>
        <AppRoutes />
      </AppProvider>
    </ConfigProvider>
  );
}

export default App;
