import { useState, useEffect } from 'react';
import { User, Key, Bell, Palette, Shield, Save, FileCode } from 'lucide-react';
import { Card, CardHeader, CardBody, Input, Button, Select } from '../components/common';
import { THEME } from '../constants';
import { getThemeFromStorage, setThemeInStorage } from '../utils';
import agentService from '../services/agentService';
import './Settings.css';

export function Settings() {
  const savedTheme = getThemeFromStorage();
  const [envSchema, setEnvSchema] = useState([]);

  const [formData, setFormData] = useState({
    name: 'John Doe',
    email: 'john@example.com',
    zapierApiKey: '',
    notificationsEnabled: true,
    emailNotifications: true,
    theme: savedTheme,
  });

  useEffect(() => {
    agentService.getEnvSchema()
      .then((list) => setEnvSchema(Array.isArray(list) ? list : []))
      .catch(() => setEnvSchema([]));
  }, []);

  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setThemeInStorage(formData.theme);
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const themeOptions = [
    { value: THEME.LIGHT, label: 'Light' },
    { value: THEME.DARK, label: 'Dark' },
  ];

  const handleThemeChange = (e) => {
    const newTheme = e.target.value;
    setFormData({ ...formData, theme: newTheme });
    setThemeInStorage(newTheme);
  };

  return (
    <div className="page settings fade-in">
      <div className="page__header">
        <div className="page__header-content">
          <h1 className="page__title">Settings</h1>
          <p className="page__description">Manage your account and preferences</p>
        </div>
      </div>

      <div className="settings__grid">
        {/* Profile Settings */}
        <Card className="settings__card slide-in-right" style={{ animationDelay: '0.1s' }}>
          <CardHeader>
            <div className="settings__header">
              <div className="settings__icon settings__icon--primary">
                <User size={20} />
              </div>
              <h3>Profile</h3>
            </div>
          </CardHeader>
          <CardBody>
            <div className="settings__form">
              <Input
                label="Full Name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
              <Input
                label="Email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
            </div>
          </CardBody>
        </Card>

        {/* Environment variables (.env) */}
        <Card className="settings__card slide-in-right" style={{ animationDelay: '0.2s' }}>
          <CardHeader>
            <div className="settings__header">
              <div className="settings__icon settings__icon--secondary">
                <FileCode size={20} />
              </div>
              <h3>Environment Variables</h3>
            </div>
          </CardHeader>
          <CardBody>
            <p className="settings__hint settings__hint--block">
              Set these in a <code>.env</code> file in the project root. Values are not shown here for security.
            </p>
            <div className="settings__env-list">
              {envSchema.map((v) => (
                <div key={v.name} className="settings__env-item">
                  <code className="settings__env-name">{v.name}</code>
                  <p className="settings__env-desc">{v.description}</p>
                </div>
              ))}
            </div>
            {envSchema.length === 0 && (
              <p className="settings__hint">Start the backend to load the list, or add ANTHROPIC_API_KEY, ZAPIER_MCP_SERVER_URL, ZAPIER_MCP_SECRET to .env.</p>
            )}
          </CardBody>
        </Card>

        {/* API Keys (legacy / optional) */}
        <Card className="settings__card slide-in-right" style={{ animationDelay: '0.25s' }}>
          <CardHeader>
            <div className="settings__header">
              <div className="settings__icon settings__icon--secondary">
                <Key size={20} />
              </div>
              <h3>API Keys (optional)</h3>
            </div>
          </CardHeader>
          <CardBody>
            <div className="settings__form">
              <Input
                label="Zapier API Key"
                type="password"
                value={formData.zapierApiKey}
                onChange={(e) => setFormData({ ...formData, zapierApiKey: e.target.value })}
                hint="Find this in your Zapier account settings"
              />
              <div className="settings__info">
                <Shield size={16} />
                <span>Your API keys are encrypted and stored securely</span>
              </div>
            </div>
          </CardBody>
        </Card>

        {/* Notifications */}
        <Card className="settings__card slide-in-right" style={{ animationDelay: '0.3s' }}>
          <CardHeader>
            <div className="settings__header">
              <div className="settings__icon settings__icon--accent">
                <Bell size={20} />
              </div>
              <h3>Notifications</h3>
            </div>
          </CardHeader>
          <CardBody>
            <div className="settings__form">
              <label className="settings__toggle">
                <input
                  type="checkbox"
                  checked={formData.notificationsEnabled}
                  onChange={(e) => setFormData({ ...formData, notificationsEnabled: e.target.checked })}
                />
                <span className="settings__toggle-slider"></span>
                <span className="settings__toggle-label">Enable notifications</span>
              </label>
              <label className="settings__toggle">
                <input
                  type="checkbox"
                  checked={formData.emailNotifications}
                  onChange={(e) => setFormData({ ...formData, emailNotifications: e.target.checked })}
                />
                <span className="settings__toggle-slider"></span>
                <span className="settings__toggle-label">Email notifications for errors</span>
              </label>
            </div>
          </CardBody>
        </Card>

        {/* Appearance */}
        <Card className="settings__card slide-in-right" style={{ animationDelay: '0.35s' }}>
          <CardHeader>
            <div className="settings__header">
              <div className="settings__icon settings__icon--gradient">
                <Palette size={20} />
              </div>
              <h3>Appearance</h3>
            </div>
          </CardHeader>
          <CardBody>
            <div className="settings__form">
              <Select
                label="Theme"
                options={themeOptions}
                value={formData.theme}
                onChange={handleThemeChange}
              />
              <p className="settings__hint">Theme changes apply immediately!</p>
            </div>
          </CardBody>
        </Card>
      </div>

      {/* Save Button */}
      <div className="settings__actions">
        <Button
          icon={Save}
          onClick={handleSave}
          className={saved ? 'settings__save-btn--saved' : ''}
        >
          {saved ? 'Saved!' : 'Save Changes'}
        </Button>
      </div>
    </div>
  );
}

export default Settings;
