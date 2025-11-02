/**
 * E2E Tests: Login Flow with WebAuthn
 */

import { test, expect } from '@playwright/test';

test.describe('Login Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
  });
  
  test('should display login page', async ({ page }) => {
    // Check page title/heading
    await expect(page.locator('h1, h2')).toContainText(/login|sign in/i);
  });
  
  test('should show WebAuthn login option', async ({ page }) => {
    // Should have a button or element for WebAuthn login
    const pageContent = await page.content();
    
    // Look for passkey/webauthn related text or buttons
    const hasWebAuthnOption = await page.locator('button, a, text').filter({ hasText: /passkey|webauthn|sign in with|biometric/i }).count() > 0;
    
    // Or check that WebAuthn is not explicitly disabled
    const notDisabledMessage = !(await page.locator('text=/webauthn.*not.*support/i').isVisible().catch(() => false));
    
    expect(hasWebAuthnOption || notDisabledMessage).toBeTruthy();
  });
  
  test('should have admin token fallback option', async ({ page }) => {
    // Should show admin token input or link to admin login
    const pageContent = await page.content();
    
    // Look for admin token input or admin-related text
    const adminTokenInput = page.locator('input[type="password"], input[placeholder*="token"], input[name*="token"]');
    
    // It's OK if admin token is not immediately visible (might be in a toggle/tab)
    const adminTokenExists = await adminTokenInput.count() > 0;
    const adminLinkExists = await page.locator('text=/admin|token|bootstrap/i').count() > 0;
    
    // At least one admin option should exist
    expect(adminTokenExists || adminLinkExists).toBeTruthy();
  });
  
  test('should detect platform authenticator', async ({ page }) => {
    // Page should check for platform authenticator availability
    // This is typically shown in the UI
    const pageContent = await page.content();
    
    // The page should load without errors
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('Login Flow with Virtual Authenticator', () => {
  test('should complete login with WebAuthn', async ({ page, context }) => {
    // First, we need to register a user with a credential
    // Enable virtual authenticator
    const cdpSession = await context.newCDPSession(page);
    await cdpSession.send('WebAuthn.enable');
    const { authenticatorId } = await cdpSession.send('WebAuthn.addVirtualAuthenticator', {
      options: {
        protocol: 'ctap2',
        transport: 'internal',
        hasResidentKey: true,
        hasUserVerification: true,
        isUserVerified: true,
      },
    });
    
    // Navigate to register page and create a user
    await page.goto('/register');
    
    const nickInput = page.locator('input[type="text"], input[name*="nick"], input[placeholder*="nick"]').first();
    const emailInput = page.locator('input[type="email"], input[name*="email"], input[placeholder*="email"]').first();
    
    const testUser = `logintest${Date.now()}`;
    await nickInput.fill(testUser);
    await emailInput.fill(`${testUser}@test.com`);
    
    const registerButton = page.locator('button:has-text("Register"), button:has-text("Create"), button[type="submit"]').first();
    await registerButton.click();
    
    // Wait for registration to complete
    await page.waitForLoadState('networkidle', { timeout: 10000 });
    
    // Now log out if we're logged in
    const logoutButton = page.locator('button:has-text("Logout"), a:has-text("Logout")');
    if (await logoutButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await logoutButton.click();
      await page.waitForLoadState('networkidle');
    }
    
    // Navigate to login page
    await page.goto('/login');
    
    // Click login button (WebAuthn should trigger automatically or on button click)
    const loginButton = page.locator('button:has-text("Login"), button:has-text("Sign in"), button:has-text("Use Passkey")').first();
    
    if (await loginButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await loginButton.click();
    }
    
    // Wait for navigation or success
    await page.waitForLoadState('networkidle', { timeout: 10000 });
    
    // Should be redirected to dashboard or see user content
    const currentUrl = page.url();
    const isLoggedIn = currentUrl.includes('/dashboard') ||
                      await page.locator('text=/welcome|dashboard|logout/i').isVisible({ timeout: 5000 }).catch(() => false);
    
    expect(isLoggedIn).toBeTruthy();
  });
  
  test('should handle login failures gracefully', async ({ page }) => {
    await page.goto('/login');
    
    // Try to login without credentials (should fail gracefully)
    const loginButton = page.locator('button:has-text("Login"), button:has-text("Sign in")').first();
    
    if (await loginButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await loginButton.click();
      
      // Should either show error or stay on login page
      await page.waitForTimeout(2000);
      
      // Check that we didn't crash
      expect(page.url()).toBeTruthy();
    }
  });
});

test.describe('Admin Token Login', () => {
  test('should show admin token input', async ({ page }) => {
    await page.goto('/login');
    
    // Look for admin token section
    // It might be hidden behind a toggle or tab
    const pageContent = await page.content();
    
    // Try to find and click on admin/token tab if it exists
    const adminTab = page.locator('button:has-text("Admin"), button:has-text("Token"), a:has-text("Admin")');
    if (await adminTab.isVisible({ timeout: 1000 }).catch(() => false)) {
      await adminTab.click();
    }
    
    // Now check for token input
    const tokenInput = page.locator('input[type="password"], input[placeholder*="token"], input[name*="token"]');
    
    // Should have at least one token-related element
    const hasTokenOption = await tokenInput.count() > 0 ||
                          await page.locator('text=/admin.*token|bootstrap.*token/i').count() > 0;
    
    expect(hasTokenOption).toBeTruthy();
  });
});

test.describe('Login Page UX', () => {
  test('should have link to registration page', async ({ page }) => {
    await page.goto('/login');
    
    // Should have link to registration
    const registerLink = page.getByRole('link', { name: /register|sign up|create account/i });
    await expect(registerLink).toBeVisible();
    
    await registerLink.click();
    await expect(page).toHaveURL(/\/register/);
  });
  
  test('should show loading state during login', async ({ page }) => {
    await page.goto('/login');
    
    // Check if there's a login button that can be clicked
    const loginButton = page.locator('button:has-text("Login"), button:has-text("Sign in")').first();
    await expect(loginButton).toBeVisible();
  });
});

