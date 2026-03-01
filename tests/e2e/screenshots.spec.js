/**
 * Screenshot capture for documentation.
 * Run with: npx playwright test tests/e2e/screenshots.spec.js
 * Output: docs/screenshots/
 *
 * Seeds realistic demo data before capturing so screenshots look lived-in.
 */

const { test } = require('@playwright/test');
const path = require('path');

const SCREENSHOTS_DIR = path.resolve(__dirname, '../../docs/screenshots');
const BASE = 'http://127.0.0.1:8092';

const profileCookie = {
  name: 'profile_id', value: '1', domain: '127.0.0.1',
  path: '/', httpOnly: false, secure: false, sameSite: 'Lax'
};
const profileNameCookie = {
  name: 'profile_name', value: 'John%20Smith', domain: '127.0.0.1',
  path: '/', httpOnly: false, secure: false, sameSite: 'Lax'
};

test.use({ viewport: { width: 390, height: 844 } }); // iPhone 14 Pro

// ─── Seed demo data once before all screenshots ───────────────────────────────
test.beforeAll(async ({ request }) => {
  const cookie = 'profile_id=1';

  // Rename default profile to John Smith and enable shopping list
  await request.put(`${BASE}/api/profiles/1`, {
    headers: { Cookie: cookie },
    data: { name: 'John Smith', color: '#3b82f6', show_shopping_list: true }
  });

  // Add a second profile for the profiles page screenshot
  await request.post(`${BASE}/api/profiles`, {
    data: { name: 'Sarah Smith', color: '#10b981' }
  });

  // ── Delete the 5 seeded default tasks and replace with richer ones ──
  const existing = await request.get(`${BASE}/api/tasks`, { headers: { Cookie: cookie } });
  const existingTasks = await existing.json();
  for (const t of existingTasks) {
    await request.delete(`${BASE}/api/tasks/${t.id}`, { headers: { Cookie: cookie } });
  }

  // Daily habit tasks
  const dailyTasks = [
    { title: 'Morning workout', icon: 'mdi-dumbbell', is_required: true },
    { title: 'Read for 20 minutes', icon: 'mdi-book-open-variant', is_required: true },
    { title: 'Drink 8 glasses of water', icon: 'mdi-cup-water', is_required: true },
    { title: 'Take vitamins', icon: 'mdi-pill', is_required: true },
    { title: 'Meditate for 10 minutes', icon: 'mdi-brain', is_required: false },
    { title: 'Evening walk', icon: 'mdi-walk', is_required: false },
  ];
  const createdDaily = [];
  for (const t of dailyTasks) {
    const res = await request.post(`${BASE}/api/tasks`, {
      headers: { Cookie: cookie },
      data: { ...t, task_type: 'daily' }
    });
    createdDaily.push(await res.json());
  }

  // Punch list (to-do) tasks
  const todoTasks = [
    { title: 'Schedule dentist appointment', icon: 'mdi-tooth', due_date: null },
    { title: 'Buy birthday gift for mom', icon: 'mdi-gift', due_date: null },
    { title: 'Call insurance company', icon: 'mdi-phone', due_date: null },
    { title: 'Renew car registration', icon: 'mdi-car', due_date: null },
  ];
  for (const t of todoTasks) {
    await request.post(`${BASE}/api/tasks`, {
      headers: { Cookie: cookie },
      data: { ...t, task_type: 'punch_list', is_required: false }
    });
  }

  // Scheduled tasks
  await request.post(`${BASE}/api/tasks`, {
    headers: { Cookie: cookie },
    data: {
      title: 'Take out the trash',
      icon: 'mdi-trash-can',
      task_type: 'scheduled',
      is_required: false,
      recurrence_pattern: { type: 'weekly', interval: 1, day_of_week: 3 } // Thursday
    }
  });
  await request.post(`${BASE}/api/tasks`, {
    headers: { Cookie: cookie },
    data: {
      title: 'Change air filter',
      icon: 'mdi-air-filter',
      task_type: 'scheduled',
      is_required: false,
      recurrence_pattern: { type: 'monthly', interval: 1, day_of_month: 1 }
    }
  });

  // Shopping list items
  const shoppingItems = [
    { title: 'Milk (2%)', icon: 'mdi-bottle-soda' },
    { title: 'Eggs (dozen)', icon: 'mdi-egg' },
    { title: 'Chicken breast', icon: 'mdi-food-drumstick' },
    { title: 'Spinach', icon: 'mdi-leaf' },
    { title: 'Greek yogurt', icon: 'mdi-food-variant' },
    { title: 'Olive oil', icon: 'mdi-bottle-tonic' },
    { title: 'Bananas', icon: 'mdi-fruit-grapes' },
  ];
  for (const item of shoppingItems) {
    await request.post(`${BASE}/api/tasks`, {
      headers: { Cookie: cookie },
      data: { ...item, task_type: 'shopping_list', is_required: false }
    });
  }

  // Check off some daily tasks to show partial progress (3 of 6)
  const today = new Date().toISOString().split('T')[0];
  for (const t of createdDaily.slice(0, 3)) {
    await request.put(`${BASE}/api/days/${today}/checks/${t.id}`, {
      headers: { Cookie: cookie },
      data: { checked: true }
    });
  }

  // ── Household tasks ──
  // Clear any existing household tasks first
  const hhRes = await request.get(`${BASE}/api/household/tasks`);
  const hhTasks = await hhRes.json();
  for (const t of hhTasks) {
    await request.delete(`${BASE}/api/household/tasks/${t.id}`);
  }

  // Add clean, realistic household tasks
  const householdTasks = [
    { title: 'Vacuum living room', frequency: 'weekly', recurrence_day_of_week: 6, icon: 'mdi-vacuum' },
    { title: 'Clean bathrooms', frequency: 'weekly', recurrence_day_of_week: 6, icon: 'mdi-shower-head' },
    { title: 'Mow the lawn', frequency: 'biweekly', recurrence_day_of_week: 5, icon: 'mdi-grass' },
    { title: 'Change bed sheets', frequency: 'biweekly', recurrence_day_of_week: 0, icon: 'mdi-bed' },
    { title: 'Clean refrigerator', frequency: 'monthly', recurrence_day_of_month: 1, icon: 'mdi-fridge' },
    { title: 'Replace HVAC filter', frequency: 'quarterly', icon: 'mdi-air-filter' },
    { title: 'Deep clean oven', frequency: 'monthly', recurrence_day_of_month: 15, icon: 'mdi-stove' },
    { title: 'Wash windows', frequency: 'quarterly', icon: 'mdi-window-closed-variant' },
  ];

  const createdHH = [];
  for (const t of householdTasks) {
    const res = await request.post(`${BASE}/api/household/tasks`, { data: t });
    createdHH.push(await res.json());
  }

  // Mark a couple as recently completed so it doesn't look brand new
  if (createdHH[0]) {
    await request.post(`${BASE}/api/household/tasks/${createdHH[0].id}/complete`, {
      headers: { Cookie: cookie }
    });
  }
  if (createdHH[1]) {
    await request.post(`${BASE}/api/household/tasks/${createdHH[1].id}/complete`, {
      headers: { Cookie: cookie }
    });
  }
});

test.beforeEach(async ({ context }) => {
  await context.addCookies([profileCookie, profileNameCookie]);
});

// ─── Screenshot tests ─────────────────────────────────────────────────────────

test('profiles page', async ({ page }) => {
  await page.goto('/profiles');
  await page.waitForLoadState('networkidle');
  await page.screenshot({ path: path.join(SCREENSHOTS_DIR, 'profiles-page.png') });
});

test('daily checklist tab', async ({ page }) => {
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  await page.screenshot({ path: path.join(SCREENSHOTS_DIR, 'checklist-page.png') });
});

test('todo list tab', async ({ page }) => {
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  await page.locator('.tab-button', { hasText: 'To-Do' }).click();
  await page.waitForTimeout(300);
  await page.screenshot({ path: path.join(SCREENSHOTS_DIR, 'todo-list-tab.png') });
});

test('shopping list tab', async ({ page }) => {
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  await page.locator('.tab-button', { hasText: 'Shopping' }).click();
  await page.waitForTimeout(300);
  await page.screenshot({ path: path.join(SCREENSHOTS_DIR, 'shopping-list-tab.png') });
});

test('household page', async ({ page }) => {
  await page.goto('/household');
  await page.waitForLoadState('networkidle');
  await page.screenshot({ path: path.join(SCREENSHOTS_DIR, 'household-page.png') });
});

test('fitbit page', async ({ page }) => {
  await page.goto('/fitbit');
  await page.waitForLoadState('networkidle');
  await page.screenshot({ path: path.join(SCREENSHOTS_DIR, 'fitbit-page.png') });
});

test('settings page', async ({ page }) => {
  await page.goto('/settings');
  await page.waitForLoadState('networkidle');
  await page.screenshot({ path: path.join(SCREENSHOTS_DIR, 'settings-page.png') });
});
