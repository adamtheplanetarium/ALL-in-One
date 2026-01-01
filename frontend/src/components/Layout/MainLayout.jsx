import React, { useState } from 'react';
import { Layout, Menu } from 'antd';
import { Link, useLocation } from 'react-router-dom';
import {
  DashboardOutlined,
  MailOutlined,
  SendOutlined,
  FileTextOutlined,
  SettingOutlined,
  CloudServerOutlined,
  LogoutOutlined,
} from '@ant-design/icons';
import { useApp } from '../../context/AppContext';
import './MainLayout.css';

const { Header, Sider, Content } = Layout;

const MainLayout = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();
  const { logout } = useApp();

  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: <Link to="/">Dashboard</Link>,
    },
    {
      key: '/smtp',
      icon: <CloudServerOutlined />,
      label: <Link to="/smtp">SMTP Servers</Link>,
    },
    {
      key: '/emails',
      icon: <MailOutlined />,
      label: <Link to="/emails">Email Lists</Link>,
    },
    {
      key: '/template',
      icon: <FileTextOutlined />,
      label: <Link to="/template">Template</Link>,
    },
    {
      key: '/campaign',
      icon: <SendOutlined />,
      label: <Link to="/campaign">Campaign</Link>,
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: <Link to="/settings">Settings</Link>,
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible collapsed={collapsed} onCollapse={setCollapsed}>
        <div className="logo">
          <MailOutlined />
          {!collapsed && <span>Email Portal</span>}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
        />
      </Sider>
      <Layout>
        <Header className="site-layout-header">
          <div className="header-content">
            <h2>ALL-in-One Email Portal</h2>
            <LogoutOutlined
              className="logout-icon"
              onClick={logout}
              title="Logout"
            />
          </div>
        </Header>
        <Content style={{ margin: '24px 16px', padding: 24, background: '#f0f2f5' }}>
          {children}
        </Content>
      </Layout>
    </Layout>
  );
};

export default MainLayout;
