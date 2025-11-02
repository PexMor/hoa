/**
 * 404 Not Found Page
 */

import { route } from 'preact-router';

interface RouteProps {
  path?: string;
  default?: boolean;
}

export function NotFound(_props?: RouteProps) {
  return (
    <div className="not-found-container">
      <div className="not-found-content">
        <h1>404</h1>
        <h2>Page Not Found</h2>
        <p>The page you're looking for doesn't exist.</p>
        <button className="btn btn-primary" onClick={() => route('/')}>
          Go Home
        </button>
      </div>
    </div>
  );
}

export default NotFound;
