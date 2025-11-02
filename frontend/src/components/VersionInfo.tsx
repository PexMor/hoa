/**
 * Version Info Component
 * 
 * Displays backend and frontend version information
 */

import { useState, useEffect } from 'preact/hooks';
import { api } from '../services/api';

interface VersionData {
  version: string;
  git_commit: string;
  git_branch: string;
  build_date: string;
}

export function VersionInfo() {
  const [backendVersion, setBackendVersion] = useState<VersionData | null>(null);
  
  // Get frontend version from package.json (injected at build time)
  const frontendVersion = "1.0.0";

  useEffect(() => {
    const fetchVersion = async () => {
      try {
        const data = await api.auth.health();
        setBackendVersion(data as unknown as VersionData);
      } catch (error) {
        console.error('Failed to fetch version:', error);
      }
    };
    
    fetchVersion();
  }, []);

  if (!backendVersion) {
    return (
      <div className="version-info">
        <div className="version-item">
          <span className="version-label">Frontend:</span>
          <span className="version-value">v{frontendVersion}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="version-info">
      <div className="version-item">
        <span className="version-label">Backend:</span>
        <span className="version-value">
          v{backendVersion.version} 
          {backendVersion.git_commit !== 'unknown' && (
            <span className="version-commit" title={`Branch: ${backendVersion.git_branch}`}>
              {' '}({backendVersion.git_commit})
            </span>
          )}
        </span>
      </div>
      
      <div className="version-item">
        <span className="version-label">Frontend:</span>
        <span className="version-value">v{frontendVersion}</span>
      </div>
      
      {backendVersion.build_date && (
        <div className="version-item">
          <span className="version-label">Built:</span>
          <span className="version-value">{backendVersion.build_date}</span>
        </div>
      )}
    </div>
  );
}

export default VersionInfo;

