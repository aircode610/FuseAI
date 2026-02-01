/**
 * AgentAPI Component
 * API testing playground: shows agent's custom endpoints and params, run via backend proxy.
 */

import { useState, useMemo, useEffect } from 'react';
import { Copy, Play } from 'lucide-react';
import { Card, CardHeader, CardBody, Button, Textarea } from '../common';
import agentService from '../../services/agentService';
import './AgentAPI.css';

function buildDefaultBody(bodyParams) {
  const obj = {};
  (bodyParams || []).forEach((p) => {
    const name = p.name || 'param';
    const desc = (p.description || '').toLowerCase();
    if (p.type === 'int' || p.type === 'integer') {
      // Default "n" or "number of X" params to 5 for easier testing
      if (name === 'n' || desc.includes('number of') || desc.includes('how many')) obj[name] = 5;
      else obj[name] = 0;
    } else if (p.type === 'bool' || p.type === 'boolean') obj[name] = false;
    else if (p.type === 'list[str]' || p.type === 'list') obj[name] = [];
    else obj[name] = '';
  });
  return obj;
}

export function AgentAPI({ agent }) {
  const endpoints = agent?.endpoints || [];
  const firstEndpoint = endpoints[0];
  const [selectedPath, setSelectedPath] = useState(firstEndpoint?.path || '/execute');
  const selectedEndpoint = useMemo(
    () => endpoints.find((ep) => ep.path === selectedPath) || firstEndpoint,
    [endpoints, selectedPath, firstEndpoint]
  );

  const pathParams = selectedEndpoint?.path_parameters || [];
  const queryParams = selectedEndpoint?.query_parameters || [];
  const bodyParams = selectedEndpoint?.body_parameters || [];

  const defaultBody = useMemo(() => buildDefaultBody(bodyParams), [bodyParams]);

  const [pathValues, setPathValues] = useState({});
  const [queryValues, setQueryValues] = useState({});
  const [requestBody, setRequestBody] = useState('{}');
  const [inputMode, setInputMode] = useState('fields'); // 'fields' | 'json' | 'curl'

  useEffect(() => {
    const pv = {};
    pathParams.forEach((p) => { pv[p.name] = ''; });
    setPathValues(pv);
    const qv = {};
    queryParams.forEach((p) => { qv[p.name] = ''; });
    setQueryValues(qv);
    setRequestBody(JSON.stringify(buildDefaultBody(bodyParams), null, 2));
  }, [selectedPath, selectedEndpoint?.path]);
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);

  const baseUrl = agent?.apiUrl || agent?.baseUrl || '';

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  const method = (selectedEndpoint?.method || 'POST').toUpperCase();
  const pathForRequest = pathParams.length
    ? selectedPath.replace(/\{(\w+)\}/g, (_, key) => pathValues[key] ?? '')
    : selectedPath;

  const generateCurl = () => {
    const url = pathForRequest.startsWith('http') ? pathForRequest : `${baseUrl}${pathForRequest}`;
    let curl = `curl -X ${method} "${url}"`;
    curl += `\n  -H "Content-Type: application/json"`;
    if (method !== 'GET' && requestBody) {
      curl += `\n  -d '${requestBody.replace(/\n/g, '')}'`;
    }
    return curl;
  };

  const sendRequest = async () => {
    if (!agent?.id) return;
    setLoading(true);
    setResponse(null);
    try {
      let body = null;
      try {
        body = JSON.parse(requestBody || '{}');
      } catch {
        body = {};
      }
      const payload = {
        method,
        path: pathForRequest,
        query: queryParams.length ? queryValues : undefined,
        body: method !== 'GET' ? body : undefined,
      };
      const result = await agentService.testEndpoint(agent.id, payload);
      setResponse({
        status: result.status,
        duration: result.duration ?? 0,
        body: result.body ?? result,
      });
    } catch (error) {
      setResponse({
        status: 500,
        duration: 0,
        body: { error: error.message || 'Request failed. Is the agent running?' },
      });
    } finally {
      setLoading(false);
    }
  };

  if (!agent) return null;

  return (
    <div className="agent-api">
      <Card padding="none">
        <CardHeader>
          <h3>API Documentation</h3>
        </CardHeader>
        <CardBody>
          <div className="api-info">
            <div className="api-info__item">
              <span className="api-info__label">Base URL</span>
              <div className="api-info__value-row">
                <code className="api-info__code">{baseUrl || '—'}</code>
                {baseUrl && (
                  <button
                    className="api-info__copy"
                    onClick={() => copyToClipboard(baseUrl)}
                    title="Copy"
                  >
                    <Copy size={14} />
                  </button>
                )}
              </div>
            </div>
            {agent.status !== 'running' && (
              <p className="api-info__hint">
                Deploy the agent to run requests. Use the Dashboard to start this agent.
              </p>
            )}
          </div>
        </CardBody>
      </Card>

      {endpoints.length === 0 ? (
        <Card padding="none">
          <CardBody>
            <p className="api-info__hint">No endpoints defined for this agent.</p>
          </CardBody>
        </Card>
      ) : (
        endpoints.map((ep) => (
          <Card key={ep.path || ep.operation_id} padding="none">
            <CardHeader>
              <div className="endpoint-header">
                <span className="endpoint-method">{(ep.method || 'POST').toUpperCase()}</span>
                <code className="endpoint-path">{ep.path || '/execute'}</code>
                {ep.operation_id && (
                  <span className="endpoint-operation-id">operation_id: {ep.operation_id}</span>
                )}
              </div>
            </CardHeader>
            <CardBody>
              {ep.summary && (
                <p className="endpoint-description">{ep.summary}</p>
              )}
              {ep.response_description && (
                <p className="endpoint-response-desc"><strong>Response:</strong> {ep.response_description}</p>
              )}

              <h4 className="api-section-title">Parameters (all fields from API)</h4>
              <div className="api-params-table-wrap">
                <table className="api-params-table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Type</th>
                      <th>Location</th>
                      <th>Required</th>
                      <th>Description</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(ep.path_parameters || []).map((p) => (
                      <tr key={`path-${p.name}`}>
                        <td><code>{p.name}</code></td>
                        <td>{p.type || 'str'}</td>
                        <td>path</td>
                        <td>{p.required !== false ? 'Yes' : 'No'}</td>
                        <td>{p.description || '—'}</td>
                      </tr>
                    ))}
                    {(ep.query_parameters || []).map((p) => (
                      <tr key={`query-${p.name}`}>
                        <td><code>{p.name}</code></td>
                        <td>{p.type || 'str'}</td>
                        <td>query</td>
                        <td>{p.required !== false ? 'Yes' : 'No'}</td>
                        <td>{p.description || '—'}</td>
                      </tr>
                    ))}
                    {(ep.body_parameters || []).map((p) => (
                      <tr key={`body-${p.name}`}>
                        <td><code>{p.name}</code></td>
                        <td>{p.type || 'str'}</td>
                        <td>body</td>
                        <td>{p.required !== false ? 'Yes' : 'No'}</td>
                        <td>{p.description || '—'}</td>
                      </tr>
                    ))}
                    {(!ep.path_parameters?.length && !ep.query_parameters?.length && !ep.body_parameters?.length) && (
                      <tr><td colSpan={5} className="api-params-empty">No parameters</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </CardBody>
          </Card>
        ))
      )}

      {/* Try It Out — Fields / JSON / cURL + Send Request lower */}
      {selectedEndpoint && (
        <Card padding="none">
          <CardHeader>
            <h3>Try It Out</h3>
          </CardHeader>
          <CardBody>
            {endpoints.length > 1 && (
              <div className="api-playground__select">
                <label className="api-playground__label">Endpoint</label>
                <select
                  value={selectedPath}
                  onChange={(e) => setSelectedPath(e.target.value)}
                  className="api-playground__select-input"
                >
                  {endpoints.map((ep) => (
                    <option key={ep.path} value={ep.path}>
                      {ep.method} {ep.path}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Input mode: Fields | JSON | cURL */}
            <div className="api-playground__mode-tabs">
              {['fields', 'json', 'curl'].map((mode) => (
                <button
                  key={mode}
                  type="button"
                  className={`api-playground__mode-tab ${inputMode === mode ? 'api-playground__mode-tab--active' : ''}`}
                  onClick={() => setInputMode(mode)}
                >
                  {mode === 'fields' && 'Fields'}
                  {mode === 'json' && 'JSON'}
                  {mode === 'curl' && 'cURL'}
                </button>
              ))}
            </div>

            {/* Fields: one input per param */}
            {inputMode === 'fields' && (
              <div className="api-playground__fields">
                {pathParams.length === 0 && queryParams.length === 0 && bodyParams.length === 0 && method !== 'GET' && (
                  <p className="api-info__hint">No parameters for this endpoint. Use JSON mode to send an empty body or optional fields.</p>
                )}
                {pathParams.length > 0 && (
                  <div className="api-playground__input">
                    <label className="api-playground__label">Path parameters</label>
                    <div className="api-playground__params">
                      {pathParams.map((p) => (
                        <div key={p.name} className="api-playground__field">
                          <label className="api-playground__field-label">{p.name}</label>
                          <input
                            placeholder={p.description || p.name}
                            value={pathValues[p.name] ?? ''}
                            onChange={(e) =>
                              setPathValues((prev) => ({ ...prev, [p.name]: e.target.value }))
                            }
                            className="api-playground__param-input"
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {queryParams.length > 0 && (
                  <div className="api-playground__input">
                    <label className="api-playground__label">Query parameters</label>
                    <div className="api-playground__params">
                      {queryParams.map((p) => (
                        <div key={p.name} className="api-playground__field">
                          <label className="api-playground__field-label">{p.name}</label>
                          <input
                            placeholder={p.description || p.name}
                            value={queryValues[p.name] ?? ''}
                            onChange={(e) =>
                              setQueryValues((prev) => ({ ...prev, [p.name]: e.target.value }))
                            }
                            className="api-playground__param-input"
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {(bodyParams.length > 0 || (method !== 'GET' && !pathParams.length && !queryParams.length)) && (
                  <div className="api-playground__input">
                    <label className="api-playground__label">Body parameters</label>
                    <div className="api-playground__params api-playground__params--vertical">
                      {(bodyParams.length > 0 ? bodyParams : [{ name: 'body', type: 'str', description: 'JSON body' }]).map((p) => (
                        <div key={p.name} className="api-playground__field">
                          <label className="api-playground__field-label">
                            {p.name}
                            {p.description && <span className="api-playground__field-desc"> — {p.description}</span>}
                          </label>
                          <input
                            type={p.type === 'int' || p.type === 'integer' ? 'number' : 'text'}
                            placeholder={p.description || p.name}
                            value={(() => {
                              try {
                                const b = JSON.parse(requestBody || '{}');
                                const v = b[p.name];
                                return v === undefined ? '' : String(v);
                              } catch { return ''; }
                            })()}
                            onChange={(e) => {
                              const val = e.target.value;
                              try {
                                const b = JSON.parse(requestBody || '{}');
                                if (p.type === 'int' || p.type === 'integer') b[p.name] = val === '' ? 0 : parseInt(val, 10);
                                else b[p.name] = val;
                                setRequestBody(JSON.stringify(b, null, 2));
                              } catch {
                                setRequestBody(JSON.stringify({ [p.name]: val }, null, 2));
                              }
                            }}
                            className="api-playground__param-input"
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* JSON: raw request body */}
            {inputMode === 'json' && (
              <div className="api-playground__input">
                <label className="api-playground__label">Request Body</label>
                <Textarea
                  value={requestBody}
                  onChange={(e) => setRequestBody(e.target.value)}
                  rows={6}
                  className="api-playground__textarea"
                />
              </div>
            )}

            {/* cURL: copy command */}
            {inputMode === 'curl' && (
              <div className="api-playground__input">
                <label className="api-playground__label">cURL command</label>
                <div className="api-playground__curl-wrap">
                  <pre className="api-curl">{generateCurl()}</pre>
                  <Button variant="ghost" size="sm" icon={Copy} onClick={() => copyToClipboard(generateCurl())}>
                    Copy
                  </Button>
                </div>
              </div>
            )}

            <div className="api-playground__submit-wrap">
              <Button
                icon={Play}
                onClick={sendRequest}
                loading={loading}
                disabled={agent.status !== 'running'}
                className="api-playground__submit"
              >
                Send Request
              </Button>
            </div>

            {response && (
              <div className="api-playground__response">
                <div className="api-response__header">
                  <span
                    className={`api-response__status api-response__status--${
                      response.status < 400 ? 'success' : 'error'
                    }`}
                  >
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
          </CardBody>
        </Card>
      )}

    </div>
  );
}

export default AgentAPI;
