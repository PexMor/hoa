/**
 * VersionInfo Component Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/preact';
import { VersionInfo } from './VersionInfo';
import * as api from '../services/api';

// Mock the API
vi.mock('../services/api', () => ({
  api: {
    auth: {
      health: vi.fn(),
    },
  },
}));

describe('VersionInfo', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders frontend version immediately', () => {
    render(<VersionInfo />);
    
    expect(screen.getByText(/Frontend:/)).toBeInTheDocument();
    expect(screen.getByText(/v1.0.0/)).toBeInTheDocument();
  });

  it('fetches and displays backend version', async () => {
    const mockHealthData = {
      status: 'healthy',
      version: '1.0.0',
      git_commit: 'abc123',
      git_branch: 'main',
      build_date: '2025-10-23 19:00:00 UTC',
    };

    vi.mocked(api.api.auth.health).mockResolvedValue(mockHealthData);

    render(<VersionInfo />);

    await waitFor(() => {
      expect(screen.getByText(/Backend:/)).toBeInTheDocument();
      expect(screen.getAllByText(/v1.0.0/)).toHaveLength(2); // Frontend and Backend
      expect(screen.getByText(/\(abc123\)/)).toBeInTheDocument();
    });
  });

  it('displays build date when available', async () => {
    const mockHealthData = {
      status: 'healthy',
      version: '1.0.0',
      git_commit: 'def456',
      git_branch: 'main',
      build_date: '2025-10-23 19:00:00 UTC',
    };

    vi.mocked(api.api.auth.health).mockResolvedValue(mockHealthData);

    render(<VersionInfo />);

    await waitFor(() => {
      expect(screen.getByText(/Built:/)).toBeInTheDocument();
      expect(screen.getByText(/2025-10-23 19:00:00 UTC/)).toBeInTheDocument();
    });
  });

  it('handles fetch error gracefully', async () => {
    vi.mocked(api.api.auth.health).mockRejectedValue(new Error('Network error'));

    render(<VersionInfo />);

    // Should still display frontend version
    expect(screen.getByText(/Frontend:/)).toBeInTheDocument();
    expect(screen.getByText(/v1.0.0/)).toBeInTheDocument();

    // Backend info should not appear
    await waitFor(() => {
      expect(screen.queryByText(/Backend:/)).not.toBeInTheDocument();
    });
  });

  it('does not display commit if unknown', async () => {
    const mockHealthData = {
      status: 'healthy',
      version: '1.0.0',
      git_commit: 'unknown',
      git_branch: 'main',
      build_date: '2025-10-23 19:00:00 UTC',
    };

    vi.mocked(api.api.auth.health).mockResolvedValue(mockHealthData);

    render(<VersionInfo />);

    await waitFor(() => {
      expect(screen.getByText(/Backend:/)).toBeInTheDocument();
      expect(screen.queryByText(/\(unknown\)/)).not.toBeInTheDocument();
    });
  });
});

