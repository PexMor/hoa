/**
 * HOA Frontend Entry Point
 */

import { render } from 'preact';
import { App } from './app';
import { setApiBaseUrl } from './services/api';

// Import styles
import './styles/main.css';

// Load config and initialize
async function init() {
  try {
    // Try to load config.json
    const response = await fetch('/config.json');
    const config = await response.json();
    
    // Set API base URL from config
    if (config.api_base_url) {
      setApiBaseUrl(config.api_base_url);
    }
    
    console.log('Loaded config:', config);
  } catch (error) {
    console.warn('Failed to load config.json, using defaults:', error);
    // Use default API base URL
    setApiBaseUrl('/api');
  }
  
  // Render app
  const root = document.getElementById('app');
  if (root) {
    render(<App />, root);
  }
}

// Start the app
init();
