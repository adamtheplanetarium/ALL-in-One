import React, { useEffect, useState } from 'react';
import { Card, Button, message, Space, Tag } from 'antd';
import { SaveOutlined, EyeOutlined } from '@ant-design/icons';
import ReactQuill from 'react-quill';
import 'react-quill/dist/quill.snow.css';
import { templateAPI } from '../../services/api';
import './TemplateEditor.css';

const TemplateEditor = () => {
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [variables, setVariables] = useState([]);

  useEffect(() => {
    fetchTemplate();
    fetchVariables();
  }, []);

  const fetchTemplate = async () => {
    try {
      const response = await templateAPI.get();
      setContent(response.data.template || '');
    } catch (error) {
      message.error('Failed to load template');
    }
  };

  const fetchVariables = async () => {
    try {
      const response = await templateAPI.getVariables();
      setVariables(response.data.variables);
    } catch (error) {
      console.error('Failed to load variables');
    }
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      await templateAPI.save(content, 'ma.html');
      message.success('Template saved successfully!');
    } catch (error) {
      message.error('Failed to save template');
    } finally {
      setLoading(false);
    }
  };

  const insertVariable = (varName) => {
    setContent(content + ` ${varName} `);
  };

  const modules = {
    toolbar: [
      [{ header: [1, 2, 3, false] }],
      ['bold', 'italic', 'underline', 'strike'],
      [{ color: [] }, { background: [] }],
      [{ list: 'ordered' }, { list: 'bullet' }],
      [{ align: [] }],
      ['link', 'image'],
      ['clean'],
    ],
  };

  return (
    <div>
      <h1>Email Template Editor</h1>
      
      <Card title="Available Variables" style={{ marginBottom: 16 }}>
        <Space wrap>
          {variables.map((variable) => (
            <Tag
              key={variable.name}
              color="blue"
              style={{ cursor: 'pointer' }}
              onClick={() => insertVariable(variable.name)}
              title={variable.description}
            >
              {variable.name}
            </Tag>
          ))}
        </Space>
        <p style={{ marginTop: 10, fontSize: 12, color: '#666' }}>
          Click on a variable to insert it into the template
        </p>
      </Card>

      <Card>
        <ReactQuill
          theme="snow"
          value={content}
          onChange={setContent}
          modules={modules}
          style={{ height: '400px', marginBottom: '50px' }}
        />
        
        <Space style={{ marginTop: 16 }}>
          <Button
            type="primary"
            icon={<SaveOutlined />}
            onClick={handleSave}
            loading={loading}
            size="large"
          >
            Save Template
          </Button>
        </Space>
      </Card>

      <Card title="Variable Reference" style={{ marginTop: 16 }}>
        {variables.map((variable) => (
          <div key={variable.name} style={{ marginBottom: 10 }}>
            <Tag color="blue">{variable.name}</Tag>
            <span>{variable.description}</span>
            <span style={{ color: '#999', marginLeft: 10 }}>
              Example: {variable.example}
            </span>
          </div>
        ))}
      </Card>
    </div>
  );
};

export default TemplateEditor;
