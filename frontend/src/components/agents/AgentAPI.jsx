/**
 * AgentAPI Component
 * API testing playground for agent detail page
 */

import { useState } from 'react';
import { Copy, Play, Eye, EyeOff } from 'lucide-react';
import { Card, CardHeader, CardBody, Button, Textarea } from '../common';
import './AgentAPI.css';

export function AgentAPI({ agent }) {
  const [showApiKey, setShowApiKey] = useState(false);
  const [requestBody, setRequestBody] = useState(
    JSON.stringify({
      board_id: "xyz789",
      card_id: "card_001",
      slack_channel: "#dev-team"
    }, null, 2)
  );
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const apiKey = import.meta.env.VITE_STRIPE_KEY;
  const baseUrl = agent?.apiUrl || 'https://forge.app/api/agent/abc123';

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  const generateCurl = () => {
    return `curl -X POST "${baseUrl}/webhook/trigger" \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: ${apiKey}" \\
  -d '${requestBody.replace(/\n/g, '')}'`;
  };

  const sendRequest = async () => {
    setLoading(true);
    try {
      // Mock response for demo
      await new Promise(resolve => setTimeout(resolve, 800));
      setResponse({
        status: 200,
        duration: 342,
        body: {
          success: true,
          message: "Posted to #dev-team",
          timestamp: new Date().toISOString()
        }
      });
    } catch (error) {
      setResponse({
        status: 500,
        duration: 0,
        body: { error: error.message }
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="agent-api">
      {/* Documentation */}
      <Card padding="none">
        <CardHeader>
          <h3>API Documentation</h3>
        </CardHeader>
        <CardBody>
          <div className="api-info">
            <div className="api-info__item">
              <span className="api-info__label">Base URL</span>
              <div className="api-info__value-row">
                <code className="api-info__code">{baseUrl}</code>
                <button 
                  className="api-info__copy"
                  onClick={() => copyToClipboard(baseUrl)}
                  title="Copy"
                >
                  <Copy size={14} />
                </button>
              </div>
            </div>

            <div className="api-info__item">
              <span className="api-info__label">Authentication</span>
              <span className="api-info__value">X-API-Key header</span>
            </div>

            <div className="api-info__item">
              <span className="api-info__label">API Key</span>
              <div className="api-info__value-row">
                <code className="api-info__code api-info__code--secret">
                  {showApiKey ? apiKey : '•'.repeat(32)}
                </code>
                <button 
                  className="api-info__copy"
                  onClick={() => setShowApiKey(!showApiKey)}
                  title={showApiKey ? 'Hide' : 'Show'}
                >
                  {showApiKey ? <EyeOff size={14} /> : <Eye size={14} />}
                </button>
                <button 
                  className="api-info__copy"
                  onClick={() => copyToClipboard(apiKey)}
                  title="Copy"
                >
                  <Copy size={14} />
                </button>
              </div>
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Endpoint */}
      <Card padding="none">
        <CardHeader>
          <div className="endpoint-header">
            <span className="endpoint-method">POST</span>
            <code className="endpoint-path">/webhook/trigger</code>
          </div>
        </CardHeader>
        <CardBody>
          <p className="endpoint-description">
            {agent?.description || 'Triggers when Trello card moves to Done list'}
          </p>

          <h4 className="api-section-title">Headers</h4>
          <div className="api-headers">
            <div className="api-header">
              <code>Content-Type</code>
              <span>application/json</span>
            </div>
            <div className="api-header">
              <code>X-API-Key</code>
              <span>Your API key</span>
            </div>
          </div>

          <h4 className="api-section-title">Request Body</h4>
          <div className="api-body-schema">
            <div className="api-param">
              <code>board_id</code>
              <span className="api-param__type">string</span>
              <span className="api-param__required">required</span>
            </div>
            <div className="api-param">
              <code>card_id</code>
              <span className="api-param__type">string</span>
              <span className="api-param__required">required</span>
            </div>
            <div className="api-param">
              <code>slack_channel</code>
              <span className="api-param__type">string</span>
              <span className="api-param__required">required</span>
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Try It Out */}
      <Card padding="none">
        <CardHeader>
          <h3>Try It Out</h3>
        </CardHeader>
        <CardBody>
          <div className="api-playground">
            <div className="api-playground__input">
              <label className="api-playground__label">Request Body</label>
              <Textarea
                value={requestBody}
                onChange={(e) => setRequestBody(e.target.value)}
                rows={6}
                className="api-playground__textarea"
              />
            </div>

            <Button 
              icon={Play} 
              onClick={sendRequest}
              loading={loading}
              className="api-playground__submit"
            >
              Send Request
            </Button>

            {response && (
              <div className="api-playground__response">
                <div className="api-response__header">
                  <span className={`api-response__status api-response__status--${response.status < 400 ? 'success' : 'error'}`}>
                    Status: {response.status} {response.status < 400 ? 'OK' : 'Error'}
                  </span>
                  <span className="api-response__duration">
                    Duration: {response.duration}ms
                  </span>
                </div>
                <pre className="api-response__body">
                  {JSON.stringify(response.body, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </CardBody>
      </Card>

      {/* cURL */}
      <Card padding="none">
        <CardHeader actions={
          <Button 
            variant="ghost" 
            size="sm" 
            icon={Copy}
            onClick={() => copyToClipboard(generateCurl())}
          >
            Copy
          </Button>
        }>
          <h3>cURL Command</h3>
        </CardHeader>
        <CardBody>
          <pre className="api-curl">{generateCurl()}</pre>
        </CardBody>
      </Card>
    </div>
  );
}

export default AgentAPI;
