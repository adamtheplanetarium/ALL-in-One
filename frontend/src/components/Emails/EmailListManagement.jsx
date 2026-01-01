import React, { useEffect, useState } from 'react';
import { Card, Button, Statistic, Space, Upload, message, Popconfirm, Row, Col } from 'antd';
import { UploadOutlined, DeleteOutlined, DownloadOutlined } from '@ant-design/icons';
import { emailAPI } from '../../services/api';

const EmailListManagement = () => {
  const [stats, setStats] = useState({ recipientCount: 0, fromCount: 0 });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await emailAPI.getStatistics();
      setStats(response.data.statistics);
    } catch (error) {
      message.error('Failed to fetch statistics');
    }
  };

  const handleUpload = async (file, type) => {
    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        const text = e.target.result;
        const emails = text.split('\n').map(line => line.trim()).filter(Boolean);
        
        if (type === 'recipients') {
          await emailAPI.uploadRecipients(emails);
          message.success(`${emails.length} recipient emails uploaded`);
        } else {
          await emailAPI.uploadFromEmails(emails);
          message.success(`${emails.length} from emails uploaded`);
        }
        fetchStats();
      } catch (error) {
        message.error('Failed to upload emails');
      }
    };
    reader.readAsText(file);
    return false; // Prevent default upload
  };

  const handleClear = async (type) => {
    setLoading(true);
    try {
      if (type === 'recipients') {
        await emailAPI.clearRecipients();
        message.success('Recipient emails cleared');
      } else {
        await emailAPI.clearFromEmails();
        message.success('From emails cleared');
      }
      fetchStats();
    } catch (error) {
      message.error('Failed to clear emails');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1>Email List Management</h1>
      
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title="Recipient Emails" extra={<Statistic value={stats.recipientCount} />}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Upload
                accept=".txt,.csv"
                beforeUpload={(file) => handleUpload(file, 'recipients')}
                showUploadList={false}
              >
                <Button icon={<UploadOutlined />} block>
                  Upload Recipients (.txt or .csv)
                </Button>
              </Upload>
              
              <Popconfirm
                title="Clear all recipient emails?"
                onConfirm={() => handleClear('recipients')}
                okText="Yes"
                cancelText="No"
              >
                <Button danger icon={<DeleteOutlined />} block loading={loading}>
                  Clear Recipients
                </Button>
              </Popconfirm>
            </Space>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title="From Emails (Sender Rotation)" extra={<Statistic value={stats.fromCount} />}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Upload
                accept=".txt,.csv"
                beforeUpload={(file) => handleUpload(file, 'from')}
                showUploadList={false}
              >
                <Button icon={<UploadOutlined />} block>
                  Upload From Emails (.txt or .csv)
                </Button>
              </Upload>
              
              <Popconfirm
                title="Clear all from emails?"
                onConfirm={() => handleClear('from')}
                okText="Yes"
                cancelText="No"
              >
                <Button danger icon={<DeleteOutlined />} block loading={loading}>
                  Clear From Emails
                </Button>
              </Popconfirm>
            </Space>
          </Card>
        </Col>
      </Row>

      <Card title="Instructions" style={{ marginTop: 16 }}>
        <p><strong>File Format:</strong> Upload .txt or .csv files with one email per line.</p>
        <p><strong>Recipient Emails:</strong> These are the target emails where campaigns will be sent.</p>
        <p><strong>From Emails:</strong> These emails will be rotated as senders. The system cycles through them.</p>
      </Card>
    </div>
  );
};

export default EmailListManagement;
