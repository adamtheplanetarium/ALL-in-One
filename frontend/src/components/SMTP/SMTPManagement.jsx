import React, { useEffect, useState } from 'react';
import { Card, Table, Button, Modal, Form, Input, message, Popconfirm, Space, Tag } from 'antd';
import { PlusOutlined, DeleteOutlined, ThunderboltOutlined } from '@ant-design/icons';
import { smtpAPI } from '../../services/api';

const SMTPManagement = () => {
  const [servers, setServers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchServers();
  }, []);

  const fetchServers = async () => {
    setLoading(true);
    try {
      const response = await smtpAPI.getServers();
      setServers(response.data.servers);
    } catch (error) {
      message.error('Failed to fetch SMTP servers');
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async (values) => {
    try {
      await smtpAPI.addServer(values);
      message.success('SMTP server added successfully');
      setModalVisible(false);
      form.resetFields();
      fetchServers();
    } catch (error) {
      message.error(error.response?.data?.error || 'Failed to add server');
    }
  };

  const handleDelete = async (record) => {
    try {
      await smtpAPI.deleteServer(record.host, record.username);
      message.success('SMTP server deleted');
      fetchServers();
    } catch (error) {
      message.error('Failed to delete server');
    }
  };

  const handleTest = async (record) => {
    try {
      const response = await smtpAPI.testServer(record);
      if (response.data.result.connected) {
        message.success('SMTP connection successful!');
      } else {
        message.error('SMTP connection failed');
      }
    } catch (error) {
      message.error('Test failed');
    }
  };

  const columns = [
    {
      title: 'Host',
      dataIndex: 'host',
      key: 'host',
      width: '25%',
    },
    {
      title: 'Port',
      dataIndex: 'port',
      key: 'port',
      width: '10%',
    },
    {
      title: 'Username',
      dataIndex: 'username',
      key: 'username',
      width: '30%',
    },
    {
      title: 'Status',
      key: 'status',
      width: '15%',
      render: (_, record) => (
        <Tag color={record.status === 'active' ? 'green' : 'red'}>
          {record.status?.toUpperCase() || 'ACTIVE'}
        </Tag>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: '20%',
      render: (_, record) => (
        <Space>
          <Button
            size="small"
            icon={<ThunderboltOutlined />}
            onClick={() => handleTest(record)}
          >
            Test
          </Button>
          <Popconfirm
            title="Delete this server?"
            onConfirm={() => handleDelete(record)}
            okText="Yes"
            cancelText="No"
          >
            <Button size="small" danger icon={<DeleteOutlined />}>
              Delete
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <h1>SMTP Server Management</h1>
      <Card>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setModalVisible(true)}
          style={{ marginBottom: 16 }}
        >
          Add SMTP Server
        </Button>

        <Table
          columns={columns}
          dataSource={servers}
          loading={loading}
          rowKey={(record) => `${record.host}-${record.username}`}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      <Modal
        title="Add SMTP Server"
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
        }}
        footer={null}
      >
        <Form form={form} onFinish={handleAdd} layout="vertical">
          <Form.Item
            name="host"
            label="Host"
            rules={[{ required: true, message: 'Please enter host' }]}
          >
            <Input placeholder="smtp.example.com" />
          </Form.Item>
          <Form.Item
            name="port"
            label="Port"
            rules={[{ required: true, message: 'Please enter port' }]}
          >
            <Input type="number" placeholder="587" />
          </Form.Item>
          <Form.Item
            name="username"
            label="Username"
            rules={[{ required: true, message: 'Please enter username' }]}
          >
            <Input placeholder="user@example.com" />
          </Form.Item>
          <Form.Item
            name="password"
            label="Password"
            rules={[{ required: true, message: 'Please enter password' }]}
          >
            <Input.Password placeholder="Password" />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                Add Server
              </Button>
              <Button onClick={() => setModalVisible(false)}>Cancel</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default SMTPManagement;
