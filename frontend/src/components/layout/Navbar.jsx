/**
 * Navbar Component
 * Main navigation header
 */

import { Link, useLocation } from 'react-router-dom';
import { Sparkles, LayoutDashboard, BookOpen, User, ChevronDown } from 'lucide-react';
import { useState } from 'react';
import './Navbar.css';

export function Navbar() {
  const location = useLocation();
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  const navItems = [
    { path: '/', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/docs', label: 'Docs', icon: BookOpen },
  ];

  return (
    <header className="navbar">
      <div className="navbar__container">
        <Link to="/" className="navbar__brand">
          <Sparkles className="navbar__logo" size={24} />
          <span className="navbar__brand-text">FuseAI</span>
        </Link>

        <nav className="navbar__nav">
          {navItems.map(item => (
            <Link
              key={item.path}
              to={item.path}
              className={`navbar__link ${location.pathname === item.path ? 'navbar__link--active' : ''}`}
            >
              <item.icon size={18} />
              <span>{item.label}</span>
            </Link>
          ))}
        </nav>

        <div className="navbar__actions">
          <div className="navbar__user">
            <button 
              className="navbar__user-button"
              onClick={() => setUserMenuOpen(!userMenuOpen)}
            >
              <div className="navbar__avatar">
                <User size={18} />
              </div>
              <span className="navbar__user-name">User</span>
              <ChevronDown size={16} />
            </button>
            
            {userMenuOpen && (
              <div className="navbar__dropdown">
                <Link to="/settings" className="navbar__dropdown-item">
                  Account Settings
                </Link>
                <Link to="/api-keys" className="navbar__dropdown-item">
                  API Keys
                </Link>
                <Link to="/docs" className="navbar__dropdown-item">
                  Documentation
                </Link>
                <hr className="navbar__dropdown-divider" />
                <button className="navbar__dropdown-item navbar__dropdown-item--danger">
                  Sign Out
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}

export default Navbar;
