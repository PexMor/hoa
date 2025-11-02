/**
 * HOA Frontend Entry Point
 */

import { render } from 'preact';
import { App } from './app';
import { setApiBaseUrl } from './services/api';
import { loadConfig } from './config';

// Import styles
import './styles/main.css';

// Load config and initialize
async function init() {
  try {
    // Load config using the config module
    const config = await loadConfig();
    
    // Set API base URL from config
    if (config.api_base_url) {
      setApiBaseUrl(config.api_base_url);
    }
    
    console.log('Loaded config:', config);
  } catch (error) {
    console.warn('Failed to load config, using defaults:', error);
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
