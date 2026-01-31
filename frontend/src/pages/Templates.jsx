/**
 * Templates Page
 * Browse and use pre-built agent templates
 */

import { useState } from 'react';
import { Search, ArrowRight, Zap, Clock, Webhook, Star } from 'lucide-react';
import { Input, Card, CardBody, Button, Badge } from '../components/common';
import './Templates.css';

const templates = [
  {
    id: 'trello-slack',
    name: 'Trello to Slack Notifier',
    description: 'Automatically notify Slack when Trello cards move between lists',
    services: ['Trello', 'Slack'],
    triggerType: 'webhook',
    category: 'Productivity',
    popular: true,
  },
  {
    id: 'github-discord',
    name: 'GitHub to Discord',
    description: 'Post new GitHub issues and PRs to your Discord server',
    services: ['GitHub', 'Discord'],
    triggerType: 'webhook',
    category: 'Development',
    popular: true,
  },
  {
    id: 'asana-email',
    name: 'Daily Asana Digest',
    description: 'Send a daily summary of Asana tasks to your email',
    services: ['Asana', 'Email'],
    triggerType: 'scheduled',
    category: 'Productivity',
    popular: false,
  },
  {
    id: 'jira-slack',
    name: 'Jira Updates to Slack',
    description: 'Keep your team updated with Jira ticket changes in Slack',
    services: ['Jira', 'Slack'],
    triggerType: 'webhook',
    category: 'Development',
    popular: true,
  },
  {
    id: 'salesforce-hubspot',
    name: 'Salesforce to HubSpot Sync',
    description: 'Sync new Salesforce leads to HubSpot CRM',
    services: ['Salesforce', 'HubSpot'],
    triggerType: 'webhook',
    category: 'Sales',
    popular: false,
  },
  {
    id: 'notion-slack',
    name: 'Notion Database Monitor',
    description: 'Get Slack notifications when Notion database items change',
    services: ['Notion', 'Slack'],
    triggerType: 'scheduled',
    category: 'Productivity',
    popular: false,
  },
];

const categories = ['All', 'Productivity', 'Development', 'Sales', 'Marketing'];

export function Templates() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');

  const filteredTemplates = templates.filter(template => {
    const matchesSearch = template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          template.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === 'All' || template.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const getTriggerIcon = (type) => {
    switch (type) {
      case 'webhook':
        return <Webhook size={14} />;
      case 'scheduled':
        return <Clock size={14} />;
      default:
        return <Zap size={14} />;
    }
  };

  return (
    <div className="page templates">
      <div className="page__header">
        <div className="page__header-content">
          <h1 className="page__title">Templates</h1>
          <p className="page__description">
            Start with pre-built templates and customize for your needs
          </p>
        </div>
      </div>

      <div className="templates__filters">
        <Input
          icon={Search}
          placeholder="Search templates..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="templates__search"
        />
        <div className="templates__categories">
          {categories.map(category => (
            <button
              key={category}
              className={`templates__category ${selectedCategory === category ? 'templates__category--active' : ''}`}
              onClick={() => setSelectedCategory(category)}
            >
              {category}
            </button>
          ))}
        </div>
      </div>

      <div className="templates__grid">
        {filteredTemplates.map(template => (
          <Card key={template.id} className="template-card" hoverable>
            <CardBody>
              <div className="template-card__header">
                <h3 className="template-card__name">{template.name}</h3>
                {template.popular && (
                  <Badge variant="accent" size="sm">
                    <Star size={12} /> Popular
                  </Badge>
                )}
              </div>
              <p className="template-card__description">{template.description}</p>
              <div className="template-card__meta">
                <span className="template-card__services">
                  {template.services.join(' → ')}
                </span>
                <span className="template-card__trigger">
                  {getTriggerIcon(template.triggerType)}
                  {template.triggerType}
                </span>
              </div>
              <Button 
                variant="outline" 
                size="sm" 
                icon={ArrowRight} 
                iconPosition="right"
                className="template-card__button"
              >
                Use Template
              </Button>
            </CardBody>
          </Card>
        ))}
      </div>

      {filteredTemplates.length === 0 && (
        <div className="empty-state">
          <h3 className="empty-state__title">No templates found</h3>
          <p className="empty-state__description">
            Try adjusting your search or filter criteria
          </p>
        </div>
      )}
    </div>
  );
}

export default Templates;
