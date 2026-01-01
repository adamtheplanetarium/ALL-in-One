import React, { useEffect, useState } from 'react';
import { Row, Col, Card, Statistic, Progress, Tag, Space, Button, message } from 'antd';
import {
  SendOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  CloudServerOutlined,
  MailOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
} from '@ant-design/icons';
import { useApp } from '../../context/AppContext';
import { campaignAPI, emailAPI, smtpAPI } from '../../services/api';
import LogViewer from '../Logs';
import './Dashboard.css';

const Dashboard = () => {
  const { campaignState, logs } = useApp();
  const [emailStats, setEmailStats] = useState({ recipientCount: 0, fromCount: 0 });
  const [smtpCount, setSmtpCount] = useState(0);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchStatistics();
  }, []);

  const fetchStatistics = async () => {
    try {
      const [emailRes, smtpRes] = await Promise.all([
        emailAPI.getStatistics(),
        smtpAPI.getServers(),
      ]);
      
      setEmailStats(emailRes.data.statistics);
      setSmtpCount(smtpRes.data.servers.length);
    } catch (error) {
      console.error('Failed to fetch statistics:', error);
    }
  };

  const handleStartCampaign = async () => {
    if (emailStats.recipientCount === 0) {
      message.error('Please upload recipient emails first');
      return;
    }
    if (smtpCount === 0) {
      message.error('Please add SMTP servers first');
      return;
    }

    setLoading(true);
    try {
      await campaignAPI.start();
      message.success('Campaign started successfully!');
    } catch (error) {
      message.error(error.response?.data?.error || 'Failed to start campaign');
    } finally {
      setLoading(false);
    }
  };

  const handleStopCampaign = async () => {
    setLoading(true);
    try {
      await campaignAPI.stop();
      message.success('Campaign stopped');
    } catch (error) {
      message.error(error.response?.data?.error || 'Failed to stop campaign');
    } finally {
      setLoading(false);
    }
  };

  const stats = campaignState.statistics || {};
  const totalSent = stats.totalSent || 0;
  const totalFailed = stats.totalFailed || 0;
  const total = totalSent + totalFailed;
  const successRate = total > 0 ? ((totalSent / total) * 100).toFixed(1) : 0;

  return (
    <div className="dashboard">
      <h1>Dashboard</h1>

      {/* Campaign Control */}
      <Card className="control-card">
        <Space size="large">
          <Tag color={campaignState.isRunning ? 'green' : 'default'} className="status-tag">
            {campaignState.isRunning ? 'RUNNING' : campaignState.state.toUpperCase()}
          </Tag>
          
          {!campaignState.isRunning ? (
            <Button
              type="primary"
              size="large"
              icon={<PlayCircleOutlined />}
              onClick={handleStartCampaign}
              loading={loading}
            >
              Start Campaign
            </Button>
          ) : (
            <Button
              danger
              size="large"
              icon={<PauseCircleOutlined />}
              onClick={handleStopCampaign}
              loading={loading}
            >
              Stop Campaign
            </Button>
          )}
        </Space>
      </Card>

      {/* Statistics */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Emails Sent"
              value={totalSent}
              prefix={<SendOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Failed"
              value={totalFailed}
              prefix={<CloseCircleOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Success Rate"
              value={successRate}
              suffix="%"
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Recipients Remaining"
              value={emailStats.recipientCount}
              prefix={<MailOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="SMTP Servers"
              value={smtpCount}
              prefix={<CloudServerOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="From Emails"
              value={emailStats.fromCount}
              prefix={<MailOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={12}>
          <Card title="Progress">
            <Progress
              percent={emailStats.recipientCount > 0 ? 
                ((totalSent / (totalSent + emailStats.recipientCount)) * 100).toFixed(1) : 0}
              status={campaignState.isRunning ? 'active' : 'normal'}
            />
            <p style={{ marginTop: 10, textAlign: 'center' }}>
              {totalSent} / {totalSent + emailStats.recipientCount} emails processed
            </p>
          </Card>
        </Col>
      </Row>

      {/* Live Logs */}
      <Card title="Live Campaign Logs" style={{ marginTop: 16 }}>
        <LogViewer logs={logs} height={400} />
      </Card>
    </div>
  );
};

export default Dashboard;
