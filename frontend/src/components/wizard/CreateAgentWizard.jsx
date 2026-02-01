/**
 * CreateAgentWizard Component
 * Step 1: Describe prompt → "Analyze" calls backend to suggest name + plan (no create).
 * Step 2: Suggested name (editable) + plan. Step 3: Configure name → "Deploy Agent" creates + deploys.
 */

import { useState } from 'react';
import { Wand2, ArrowRight, ArrowLeft, Check, Loader, Settings } from 'lucide-react';
import { Button, Input, Textarea, Card, CardBody } from '../common';
import agentService from '../../services/agentService';
import './CreateAgentWizard.css';

const STEPS = [
  { id: 'prompt', title: 'Describe Your Agent', icon: Wand2 },
  { id: 'name', title: 'Suggested Name & Plan', icon: Check },
  { id: 'configure', title: 'Configure & Deploy', icon: Settings },
];

export function CreateAgentWizard({ onComplete, onCancel }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [createError, setCreateError] = useState(null);
  const [formData, setFormData] = useState({
    prompt: '',
    name: '',
    sourceService: '',
    targetService: '',
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
      const result = await agentService.analyzePrompt(formData.prompt.trim());
      setPlan(result);
      setFormData(prev => ({
        ...prev,
        name: result.suggestedName || prev.name,
        sourceService: result.services?.[0],
        targetService: result.services?.[1],
      }));
      setCurrentStep(1);
    } catch (err) {
      setCreateError(err?.message || err?.data?.detail || 'Failed to analyze. Is the backend running on port 8000?');
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
    setCreateError(null);
    setIsAnalyzing(true);
    try {
      const agent = await agentService.createAgent({
        prompt: formData.prompt.trim(),
        name: formData.name?.trim() || undefined,
      });
      onComplete?.({ ...formData, ...agent });
    } catch (err) {
      setCreateError(err?.message || err?.data?.detail || 'Failed to create agent.');
    } finally {
      setIsAnalyzing(false);
    }
  };

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
              <p>Be specific about the services and actions you need.</p>
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
              <h2>Suggested Name & Plan</h2>
              <p>We've analyzed your request. Edit the name if you like, then continue to deploy.</p>
            </div>

            <div className="wizard__plan">
              <Card className="wizard__plan-card">
                <CardBody>
                  <Input
                    label="Agent Name (suggested)"
                    value={formData.name}
                    onChange={(e) => updateFormData('name', e.target.value)}
                    placeholder="e.g. Trello Done Notifier"
                  />
                  <div className="plan-section">
                    <span className="plan-label">Services</span>
                    <span className="plan-value">{(plan.services || []).join(' → ') || '—'}</span>
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
            </div>
          </div>
        )}

        {/* Step 3: Configure & Deploy */}
        {currentStep === 2 && (
          <div className="wizard__step-content">
            <div className="wizard__header">
              <h2>Configure & Deploy</h2>
              <p>Confirm the agent name and create your API agent (on-demand only).</p>
            </div>

            <div className="wizard__form">
              <Input
                label="Agent Name"
                value={formData.name}
                onChange={(e) => updateFormData('name', e.target.value)}
                required
              />
              {createError && (
                <div className="wizard__error" role="alert">{createError}</div>
              )}
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
              disabled={!formData.name?.trim()}
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
