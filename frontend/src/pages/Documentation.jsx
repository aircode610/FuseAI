import { Sparkles, Zap, Code, Rocket, Shield, Users, ClipboardList, MessageSquare, BarChart3, Bell, BookOpen } from 'lucide-react';
import { Card, CardBody } from '../components/common';
import './Documentation.css';

export function Documentation() {
  const features = [
    {
      icon: Sparkles,
      title: 'Natural Language Generation',
      description: 'Describe what you want in plain English, and FuseAI generates the agent for you.',
      color: 'primary',
    },
    {
      icon: Zap,
      title: 'Instant Deployment',
      description: 'Your agents are deployed and ready to use in seconds, no DevOps required.',
      color: 'secondary',
    },
    {
      icon: Code,
      title: 'Auto-Generated Code',
      description: 'View, download, and customize the FastAPI code that powers your agents.',
      color: 'accent',
    },
    {
      icon: Shield,
      title: 'Error Intelligence',
      description: 'AI-powered error handling with web search to find solutions automatically.',
      color: 'primary',
    },
    {
      icon: Users,
      title: 'Multi-Service Support',
      description: 'Connect Trello, Slack, GitHub, Asana, and more through Zapier integration.',
      color: 'secondary',
    },
    {
      icon: Rocket,
      title: 'Real-Time Monitoring',
      description: 'Track performance, logs, and metrics for all your agents in one dashboard.',
      color: 'accent',
    },
  ];

  const howItWorks = [
    {
      step: '1',
      title: 'Describe Your Agent',
      description: 'Tell us what you want: "When a Trello card moves to Done, post a summary to Slack"',
    },
    {
      step: '2',
      title: 'Review the Plan',
      description: 'FuseAI analyzes your request and designs the API, Zapier actions, and workflow',
    },
    {
      step: '3',
      title: 'Configure & Deploy',
      description: 'Add your API keys, customize settings, and deploy with one click',
    },
    {
      step: '4',
      title: 'Monitor & Iterate',
      description: 'Watch your agent work, view logs, and make improvements as needed',
    },
  ];

  const useCases = [
    {
      icon: ClipboardList,
      title: 'Project Management',
      description: 'Sync tasks between Trello, Asana, and Jira. Notify teams when work is completed.',
      color: 'primary',
    },
    {
      icon: MessageSquare,
      title: 'Communication',
      description: 'Post GitHub issues to Discord, send daily digests to Slack, alert teams of critical events.',
      color: 'secondary',
    },
    {
      icon: BarChart3,
      title: 'Analytics',
      description: 'Aggregate data from multiple sources, generate reports, track KPIs across platforms.',
      color: 'accent',
    },
    {
      icon: Bell,
      title: 'Monitoring',
      description: 'Watch for changes, trigger actions on specific events, automate incident response.',
      color: 'primary',
    },
  ];

  return (
    <div className="page documentation fade-in">
      {/* Hero Section */}
      <div className="docs__hero">
        <div className="docs__hero-icon">
          <BookOpen size={48} />
        </div>
        <h1 className="docs__hero-title">Welcome to FuseAI</h1>
        <p className="docs__hero-subtitle">
          Build, deploy, and monitor AI agents that connect your favorite services—no code required
        </p>
      </div>

      {/* What is FuseAI */}
      <section className="docs__section fade-in-scale">
        <h2 className="docs__section-title">What is FuseAI?</h2>
        <Card className="docs__intro-card hover-glow">
          <CardBody>
            <p className="docs__intro-text">
              <strong>FuseAI</strong> is an AI-powered agent generator that turns your ideas into working automation agents. 
              Simply describe what you want in natural language, and we'll build, deploy, and monitor the agent for you.
            </p>
            <p className="docs__intro-text">
              Our platform generates <strong>FastAPI applications</strong> that use <strong>Zapier</strong> as the integration layer, 
              giving you access to 5,000+ apps and services. Each agent comes with built-in monitoring, error handling with 
              AI-powered solutions, and a testing playground.
            </p>
          </CardBody>
        </Card>
      </section>

      {/* Features */}
      <section className="docs__section">
        <h2 className="docs__section-title">Key Features</h2>
        <div className="docs__features">
          {features.map((feature, index) => (
            <Card 
              key={feature.title} 
              className="docs__feature-card hover-lift"
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <CardBody>
                <div className={`docs__feature-icon docs__feature-icon--${feature.color}`}>
                  <feature.icon size={28} />
                </div>
                <h3 className="docs__feature-title">{feature.title}</h3>
                <p className="docs__feature-description">{feature.description}</p>
              </CardBody>
            </Card>
          ))}
        </div>
      </section>

      {/* Use Cases */}
      <section className="docs__section">
        <h2 className="docs__section-title">Use Cases</h2>
        <div className="docs__use-cases">
          {useCases.map((useCase, index) => (
            <Card 
              key={useCase.title} 
              className="docs__use-case hover-glow"
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <CardBody>
                <div className={`docs__use-case-header`}>
                  <div className={`docs__use-case-icon docs__use-case-icon--${useCase.color}`}>
                    <useCase.icon size={24} />
                  </div>
                  <h3>{useCase.title}</h3>
                </div>
                <p>{useCase.description}</p>
              </CardBody>
            </Card>
          ))}
        </div>
      </section>

      {/* Example */}
      <section className="docs__section">
        <h2 className="docs__section-title">Example: Trello to Slack Agent</h2>
        <Card className="docs__example-card fade-in-scale">
          <CardBody>
            <div className="docs__example">
              <div className="docs__example-prompt">
                <strong>Your Prompt:</strong>
                <p>"When a Trello card moves to the 'Done' list, post a summary with the card details to our #dev-team Slack channel"</p>
              </div>
              <div className="docs__example-arrow">↓</div>
              <div className="docs__example-output">
                <strong>FuseAI Generates:</strong>
                <ul>
                  <li>API endpoint: <code>POST /webhook/trigger</code></li>
                  <li>Zapier integration with Trello & Slack</li>
                  <li>FastAPI application with error handling</li>
                  <li>Monitoring dashboard with logs & metrics</li>
                  <li>Testing playground to try it out</li>
                </ul>
              </div>
            </div>
          </CardBody>
        </Card>
      </section>

      {/* Get Started CTA */}
      <section className="docs__cta">
        <Card className="docs__cta-card hover-glow">
          <CardBody>
            <h2>Ready to Build Your First Agent?</h2>
            <p>Head to the dashboard and click "Create Agent" to get started!</p>
            <div className="docs__cta-buttons">
              <a href="/" className="docs__cta-btn docs__cta-btn--primary">
                <Sparkles size={18} />
                Go to Dashboard
              </a>
            </div>
          </CardBody>
        </Card>
      </section>
    </div>
  );
}

export default Documentation;
