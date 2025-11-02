/**
 * Dynamic configuration loader for HOA frontend
 */

import type { AppConfig } from './types';

let config: AppConfig | null = null;

export async function loadConfig(): Promise<AppConfig> {
  if (config) {
    return config;
  }

  try {
    const response = await fetch('/config.json');
    if (!response.ok) {
      throw new Error('Failed to load config');
    }
    config = await response.json();
    return config!;
  } catch (error) {
    console.error('Failed to load config, using defaults:', error);
    // Return default config
    config = {
      api_base_url: '/api',
      allowed_rps: [
        {
          rp_id: 'localhost',
          rp_name: 'Local Development',
          origins: ['http://localhost:8000', 'http://localhost:3000'],
        },
      ],
      require_auth_method_approval: false,
      allow_self_service_auth: true,
    };
    return config;
  }
}

export function getConfig(): AppConfig {
  if (!config) {
    throw new Error('Config not loaded. Call loadConfig() first.');
  }
  return config;
}

