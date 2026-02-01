/**
 * Tabs Component
 * Tab navigation
 */

import './Tabs.css';

export function Tabs({ 
  tabs,
  activeTab,
  onChange,
  className = '',
}) {
  return (
    <div className={`tabs ${className}`}>
      <div className="tabs__list" role="tablist">
        {tabs.map(tab => (
          <button
            key={tab.id}
            role="tab"
            className={`tabs__tab ${activeTab === tab.id ? 'tabs__tab--active' : ''}`}
            onClick={() => onChange(tab.id)}
            aria-selected={activeTab === tab.id}
          >
            {tab.icon && <tab.icon size={16} className="tabs__tab-icon" />}
            <span>{tab.label}</span>
            {tab.badge !== undefined && (
              <span className="tabs__tab-badge">{tab.badge}</span>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}

export function TabPanel({ children, isActive, className = '' }) {
  if (!isActive) return null;
  
  return (
    <div className={`tabs__panel ${className}`} role="tabpanel">
      {children}
    </div>
  );
}

export default Tabs;
