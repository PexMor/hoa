/**
 * Main App Component
 * 
 * Sets up routing and auth context
 */

import Router from 'preact-router';
import { AuthProvider } from './hooks/useAuth';

// Pages
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Admin from './pages/Admin';
import NotFound from './pages/NotFound';

export function App() {
  return (
    <AuthProvider>
      <div id="app">
        <Router>
          <Home path="/" />
          <Login path="/login" />
          <Register path="/register" />
          <Dashboard path="/dashboard" />
          <Admin path="/admin" />
          <NotFound default />
        </Router>
      </div>
    </AuthProvider>
  );
}

export default App;
