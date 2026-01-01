import React, { useEffect, useState } from 'react';
import { Card, Form, Input, InputNumber, Switch, Button, message, Divider, Row, Col } from 'antd';
import { SaveOutlined } from '@ant-design/icons';
import { campaignAPI } from '../../services/api';

const CampaignSettings = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      const response = await campaignAPI.getConfig();
      const settings = response.data.config.Settings;
      
      form.setFieldsValue({
        subject: settings.subject,
        SENDERNAME: settings.SENDERNAME,
        threads: parseInt(settings.threads),
        SLEEPTIME: parseFloat(settings.SLEEPTIME),
        important: settings.important === '1',
        TESTMODE: settings.TESTMODE === '1',
        DEBUG: settings.DEBUG === '1',
      });
    } catch (error) {
      message.error('Failed to load configuration');
    }
  };

  const handleSave = async (values) => {
    setLoading(true);
    try {
      const updates = [
        { section: 'Settings', key: 'subject', value: values.subject },
        { section: 'Settings', key: 'SENDERNAME', value: values.SENDERNAME },
        { section: 'Settings', key: 'threads', value: values.threads.toString() },
        { section: 'Settings', key: 'SLEEPTIME', value: values.SLEEPTIME.toString() },
        { section: 'Settings', key: 'important', value: values.important ? '1' : '0' },
        { section: 'Settings', key: 'TESTMODE', value: values.TESTMODE ? '1' : '0' },
        { section: 'Settings', key: 'DEBUG', value: values.DEBUG ? '1' : '0' },
      ];

      for (const update of updates) {
        await campaignAPI.updateConfig(update.section, update.key, update.value);
      }

      message.success('Settings saved successfully!');
    } catch (error) {
      message.error('Failed to save settings');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1>Campaign Settings</h1>
      
      <Card>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSave}
          initialValues={{
            threads: 3,
            SLEEPTIME: 1,
            important: false,
            TESTMODE: true,
            DEBUG: false,
          }}
        >
          <Divider>Email Settings</Divider>
          
          <Form.Item
            name="subject"
            label="Email Subject"
            rules={[{ required: true, message: 'Subject is required' }]}
            extra="Use CapitalS for capitalized domain, randomchar for random numbers, DATEX for date"
          >
            <Input placeholder="Your subject line here" />
          </Form.Item>

          <Form.Item
            name="SENDERNAME"
            label="Sender Name"
            rules={[{ required: true, message: 'Sender name is required' }]}
            extra="Use CapitalS for capitalized domain, randomchar for random numbers"
          >
            <Input placeholder="e.g., Support or CapitalS Team" />
          </Form.Item>

          <Divider>Performance Settings</Divider>

          <Row gutter={16}>
            <Col xs={24} md={12}>
              <Form.Item
                name="threads"
                label="Number of Threads"
                rules={[{ required: true, message: 'Threads is required' }]}
                extra="Number of concurrent email sending threads (1-10)"
              >
                <InputNumber min={1} max={10} style={{ width: '100%' }} />
              </Form.Item>
            </Col>

            <Col xs={24} md={12}>
              <Form.Item
                name="SLEEPTIME"
                label="Sleep Time (seconds)"
                rules={[{ required: true, message: 'Sleep time is required' }]}
                extra="Delay between emails in seconds"
              >
                <InputNumber min={0} max={60} step={0.1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Divider>Email Flags</Divider>

          <Form.Item
            name="important"
            label="Mark as Important"
            valuePropName="checked"
            extra="Mark emails with high priority flag"
          >
            <Switch />
          </Form.Item>

          <Divider>Debug Options</Divider>

          <Form.Item
            name="TESTMODE"
            label="Test Mode"
            valuePropName="checked"
            extra="Enable test mode (emails won't be removed from list after sending)"
          >
            <Switch />
          </Form.Item>

          <Form.Item
            name="DEBUG"
            label="Debug Mode"
            valuePropName="checked"
            extra="Enable detailed SMTP debugging output"
          >
            <Switch />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={loading} size="large">
              Save Settings
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

export default CampaignSettings;
