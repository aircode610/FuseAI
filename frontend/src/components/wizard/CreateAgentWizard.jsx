/**
 * CreateAgentWizard Component
 * Multi-step wizard for creating new agents.
 * Step 0: prompt → "Analyze" calls backend to create + generate + deploy agent.
 * Step 1: review plan (from API). Step 2: configure. "Deploy Agent" adds agent to UI.
 */

import { useState } from 'react';
import { Wand2, ArrowRight, ArrowLeft, Check, Loader, Zap, Clock, Webhook, Settings } from 'lucide-react';
import { Button, Input, Textarea, Select, Card, CardBody } from '../common';
import agentService from '../../services/agentService';
import './CreateAgentWizard.css';

const STEPS = [
  { id: 'prompt', title: 'Describe Your Agent', icon: Wand2 },
  { id: 'review', title: 'Review Plan', icon: Check },
  { id: 'configure', title: 'Configure', icon: Settings },
];

export function CreateAgentWizard({ onComplete, onCancel }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [createError, setCreateError] = useState(null);
  const [formData, setFormData] = useState({
    prompt: '',
    name: '',
    triggerType: 'webhook',
    zapierApiKey: '',
    sourceService: '',
    targetService: '',
    slackChannel: '',
    schedule: '',
    enableWebSearch: true,
    enableRetry: true,
  });
  const [plan, setPlan] = useState(null);

  const updateFormData = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const analyzePrompt = async () => {
    setCreateError(null);
    setIsAnalyzing(true);
    try {
      const agent = await agentService.createAgent({
        prompt: formData.prompt.trim(),
        name: formData.name?.trim() || undefined,
      });
      setPlan(agent);
      setFormData(prev => ({
        ...prev,
        name: agent.name || prev.name,
        sourceService: agent.services?.[0],
        targetService: agent.services?.[1],
      }));
      setCurrentStep(1);
    } catch (err) {
      setCreateError(err?.message || err?.data?.detail || 'Failed to create agent. Is the backend running on port 8000?');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleNext = () => {
    if (currentStep === 0) {
      analyzePrompt();
    } else if (currentStep < STEPS.length - 1) {
      setCurrentStep(prev => prev + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1);
    }
  };

  const handleDeploy = async () => {
    if (plan) {
      onComplete?.({ ...formData, ...plan });
    }
  };

  const triggerOptions = [
    { value: 'webhook', label: 'Webhook (triggered by external service)' },
    { value: 'scheduled', label: 'Scheduled (runs on a schedule)' },
    { value: 'on_demand', label: 'On-Demand (called manually)' },
  ];

  return (
    <div className="wizard">
      {/* Progress Steps */}
      <div className="wizard__progress">
        {STEPS.map((step, index) => (
          <div
            key={step.id}
            className={`wizard__step ${index === currentStep ? 'wizard__step--active' : ''} ${index < currentStep ? 'wizard__step--completed' : ''}`}
          >
            <div className="wizard__step-icon">
              {index < currentStep ? (
                <Check size={18} />
              ) : (
                <step.icon size={18} />
              )}
            </div>
            <span className="wizard__step-title">{step.title}</span>
            {index < STEPS.length - 1 && <div className="wizard__step-connector" />}
          </div>
        ))}
      </div>

      {/* Step Content */}
      <div className="wizard__content">
        {/* Step 1: Prompt */}
        {currentStep === 0 && (
          <div className="wizard__step-content">
            <div className="wizard__header">
              <h2>Describe what you want your agent to do</h2>
              <p>Be specific about the trigger, services, and actions you need.</p>
            </div>
            
            <Textarea
              placeholder="Example: When a Trello card moves to the 'Done' list, summarize it and post a notification to the #dev-team Slack channel"
              value={formData.prompt}
              onChange={(e) => updateFormData('prompt', e.target.value)}
              rows={6}
              className="wizard__textarea"
            />

            {createError && (
              <div className="wizard__error" role="alert">
                {createError}
              </div>
            )}
            <div className="wizard__examples">
              <h4>Example prompts:</h4>
              <ul>
                <li onClick={() => updateFormData('prompt', 'When a Trello card moves to Done, post a summary to Slack')}>
                  When a Trello card moves to Done, post a summary to Slack
                </li>
                <li onClick={() => updateFormData('prompt', 'Every day at 9am, compile Asana tasks and send a digest to Discord')}>
                  Every day at 9am, compile Asana tasks and send a digest to Discord
                </li>
                <li onClick={() => updateFormData('prompt', 'When someone creates a GitHub issue, create a corresponding Trello card')}>
                  When someone creates a GitHub issue, create a corresponding Trello card
                </li>
              </ul>
            </div>
          </div>
        )}

        {/* Step 2: Review Plan */}
        {currentStep === 1 && plan && (
          <div className="wizard__step-content">
            <div className="wizard__header">
              <h2>Review Your Agent Plan</h2>
              <p>We've analyzed your request. Here's what we'll build:</p>
            </div>

            <div className="wizard__plan">
              <Card className="wizard__plan-card">
                <CardBody>
                  <div className="plan-section">
                    <span className="plan-label">Agent Name</span>
                    <span className="plan-value">{plan.name}</span>
                  </div>
                  <div className="plan-section">
                    <span className="plan-label">Type</span>
                    <div className="plan-badge">
                      {plan.triggerType === 'webhook' && <Webhook size={14} />}
                      {plan.triggerType === 'scheduled' && <Clock size={14} />}
                      {plan.triggerType === 'on_demand' && <Zap size={14} />}
                      <span>{plan.triggerType}</span>
                    </div>
                  </div>
                  <div className="plan-section">
                    <span className="plan-label">Services</span>
                    <span className="plan-value">{plan.services.join(' → ')}</span>
                  </div>
                </CardBody>
              </Card>

              <Card className="wizard__plan-card">
                <CardBody>
                  <h4>API Endpoints</h4>
                  {(plan.endpoints || []).map((endpoint, idx) => (
                    <div key={idx} className="plan-endpoint">
                      <span className="plan-endpoint__method">{endpoint.method || 'POST'}</span>
                      <code className="plan-endpoint__path">{endpoint.path || '/execute'}</code>
                      {endpoint.summary && (
                        <span className="plan-endpoint__summary">{endpoint.summary}</span>
                      )}
                    </div>
                  ))}
                </CardBody>
              </Card>

              {plan.apiUrl && (
                <div className="plan-base-url">
                  <span>Base URL:</span>
                  <code>{plan.apiUrl}</code>
                </div>
              )}

              {plan.status === 'deploying' && (
                <p className="wizard__deploying">Agent is deploying in the background. Add to dashboard to see it.</p>
              )}
            </div>
          </div>
        )}

        {/* Step 3: Configure */}
        {currentStep === 2 && (
          <div className="wizard__step-content">
            <div className="wizard__header">
              <h2>Configure Your Agent</h2>
              <p>Set up the final details before deployment.</p>
            </div>

            <div className="wizard__form">
              <Input
                label="Agent Name"
                value={formData.name}
                onChange={(e) => updateFormData('name', e.target.value)}
                required
              />

              <Select
                label="Trigger Type"
                options={triggerOptions}
                value={formData.triggerType}
                onChange={(e) => updateFormData('triggerType', e.target.value)}
              />

              <Input
                label="Zapier API Key"
                type="password"
                value={formData.zapierApiKey}
                onChange={(e) => updateFormData('zapierApiKey', e.target.value)}
                hint="Find this in your Zapier account settings"
              />

              {formData.targetService === 'Slack' && (
                <Input
                  label="Slack Channel"
                  value={formData.slackChannel}
                  onChange={(e) => updateFormData('slackChannel', e.target.value)}
                  placeholder="#channel-name"
                />
              )}

              {formData.triggerType === 'scheduled' && (
                <Input
                  label="Schedule (Cron Expression)"
                  value={formData.schedule}
                  onChange={(e) => updateFormData('schedule', e.target.value)}
                  placeholder="0 9 * * *"
                  hint="e.g., '0 9 * * *' for daily at 9 AM"
                />
              )}

              <div className="wizard__options">
                <h4>Advanced Options</h4>
                <label className="wizard__checkbox">
                  <input
                    type="checkbox"
                    checked={formData.enableWebSearch}
                    onChange={(e) => updateFormData('enableWebSearch', e.target.checked)}
                  />
                  <span>Enable web search for error solutions</span>
                </label>
                <label className="wizard__checkbox">
                  <input
                    type="checkbox"
                    checked={formData.enableRetry}
                    onChange={(e) => updateFormData('enableRetry', e.target.checked)}
                  />
                  <span>Enable automatic retry on failure (3 attempts)</span>
                </label>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Footer Actions */}
      <div className="wizard__footer">
        <Button variant="ghost" onClick={onCancel}>
          Cancel
        </Button>
        <div className="wizard__footer-actions">
          {currentStep > 0 && (
            <Button variant="outline" icon={ArrowLeft} onClick={handleBack}>
              Back
            </Button>
          )}
          {currentStep < STEPS.length - 1 ? (
            <Button 
              icon={isAnalyzing ? Loader : ArrowRight} 
              iconPosition="right"
              onClick={handleNext}
              disabled={currentStep === 0 && !formData.prompt}
              loading={isAnalyzing}
            >
              {currentStep === 0 ? 'Analyze' : 'Next'}
            </Button>
          ) : (
            <Button 
              variant="success"
              icon={isAnalyzing ? Loader : Check}
              onClick={handleDeploy}
              loading={isAnalyzing}
            >
              Deploy Agent
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

export default CreateAgentWizard;
