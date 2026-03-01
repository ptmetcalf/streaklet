const { test, expect } = require('@playwright/test');

const profileCookie = {
  name: 'profile_id',
  value: '1',
  domain: '127.0.0.1',
  path: '/',
  httpOnly: false,
  secure: false,
  sameSite: 'Lax'
};

const profileNameCookie = {
  name: 'profile_name',
  value: 'Default%20Profile',
  domain: '127.0.0.1',
  path: '/',
  httpOnly: false,
  secure: false,
  sameSite: 'Lax'
};

function uniqueName(prefix) {
  return `${prefix} ${Date.now()}-${Math.floor(Math.random() * 1000)}`;
}

test.beforeEach(async ({ context }) => {
  await context.addCookies([profileCookie, profileNameCookie]);
});

test('today page can complete a daily task', async ({ page }) => {
  const pageErrors = [];
  page.on('pageerror', (error) => pageErrors.push(error.message));

  await page.goto('/');
  await expect(page.getByRole('heading', { name: "Today's Checklist" })).toBeVisible();

  const markCompleteButton = page.locator('button.btn-task-complete').filter({ hasText: 'Mark Complete' }).first();
  await expect(markCompleteButton).toBeVisible();
  await markCompleteButton.click();

  await expect(page.locator('button.btn-task-complete').filter({ hasText: 'Undo' }).first()).toBeVisible();
  expect(pageErrors).toEqual([]);
});

test('can archive, restore, and delete a personal daily task from edit flow', async ({ page }) => {
  const taskTitle = uniqueName('E2E Daily');

  await page.goto('/');
  await page.locator('.add-task-card').filter({ hasText: 'Add New Daily Task' }).first().click();

  const addModal = page.locator('.modal-content').filter({ hasText: 'Add New Daily Task' });
  await expect(addModal).toBeVisible();
  await addModal.locator('input.form-field__input').first().fill(taskTitle);
  await addModal.getByRole('button', { name: 'Add Task' }).click();

  const taskCard = page.locator('.unified-task-card').filter({ hasText: taskTitle }).first();
  await expect(taskCard).toBeVisible();
  await taskCard.getByRole('button', { name: 'Edit' }).click();

  const editModal = page.locator('.modal-content').filter({ hasText: 'Edit Task' });
  await expect(editModal).toBeVisible();
  await editModal.getByLabel(/Active/).uncheck();
  await editModal.getByRole('button', { name: 'Update Task' }).click();

  const archivedToggle = page.getByRole('button', { name: /Archived Daily Tasks/ });
  await expect(archivedToggle).toBeVisible();
  await archivedToggle.click();

  const archivedCard = page.locator('.unified-task-card').filter({ hasText: taskTitle }).first();
  await expect(archivedCard).toBeVisible();
  await archivedCard.getByRole('button', { name: /Restore/ }).click();

  const restoredCard = page.locator('.unified-task-card').filter({ hasText: taskTitle }).first();
  await expect(restoredCard).toBeVisible();
  await restoredCard.getByRole('button', { name: 'Edit' }).click();

  const reloadedEditModal = page.locator('.modal-content').filter({ hasText: 'Edit Task' });
  await expect(reloadedEditModal).toBeVisible();
  await reloadedEditModal.getByRole('button', { name: 'Delete Task' }).click();

  const deleteModal = page.locator('.modal-content').filter({ hasText: 'Delete Task?' });
  await expect(deleteModal).toBeVisible();
  await deleteModal.getByRole('button', { name: 'Delete Task' }).click();

  await expect(page.locator('.unified-task-card').filter({ hasText: taskTitle })).toHaveCount(0);
});

test('can archive, restore, and delete a household task from edit flow', async ({ page }) => {
  const taskTitle = uniqueName('E2E Household');

  await page.goto('/household');
  await expect(page.getByRole('heading', { name: 'Household Tasks' })).toBeVisible();

  await page.getByText('Add New Household Task').first().click();
  const addModal = page.locator('.modal-content').filter({ hasText: 'Add New Household Task' });
  await expect(addModal).toBeVisible();
  await addModal.locator('input.form-field__input').first().fill(taskTitle);
  await addModal.getByRole('button', { name: 'Add Task' }).click();

  const taskCard = page.locator('.unified-task-card').filter({ hasText: taskTitle }).first();
  await expect(taskCard).toBeVisible();
  await taskCard.getByRole('button', { name: 'Edit' }).click();

  const editModal = page.locator('.modal-content').filter({ hasText: 'Edit Household Task' });
  await expect(editModal).toBeVisible();
  await editModal.getByLabel(/Active/).uncheck();
  await editModal.getByRole('button', { name: 'Update Task' }).click();

  const archivedToggle = page.getByRole('button', { name: /Archived Household Tasks/ });
  await expect(archivedToggle).toBeVisible();
  await archivedToggle.click();

  const archivedCard = page.locator('.unified-task-card').filter({ hasText: taskTitle }).first();
  await expect(archivedCard).toBeVisible();
  await archivedCard.getByRole('button', { name: /Restore/ }).click();

  const restoredCard = page.locator('.unified-task-card')
    .filter({ hasText: taskTitle })
    .filter({ has: page.getByRole('button', { name: /Mark Complete/ }) })
    .first();
  await expect(restoredCard).toBeVisible();
  await restoredCard.getByRole('button', { name: 'Edit' }).click();

  const reloadedEditModal = page.locator('.modal-content').filter({ hasText: 'Edit Household Task' });
  await expect(reloadedEditModal).toBeVisible();
  await reloadedEditModal.getByRole('button', { name: 'Delete Task' }).click();

  const deleteModal = page.locator('.modal-content').filter({ hasText: 'Delete Household Task?' });
  await expect(deleteModal).toBeVisible();
  await deleteModal.getByRole('button', { name: 'Delete Task' }).click();

  await expect(page.locator('.unified-task-card').filter({ hasText: taskTitle })).toHaveCount(0);
});

test('fitbit connection status loads on settings and fitbit page renders', async ({ page }) => {
  await page.goto('/settings');
  await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Fitbit' })).toBeVisible();

  const connectButton = page.getByRole('button', { name: 'Connect to Fitbit' });
  const connectedLabel = page.getByText('Connected to Fitbit');
  if (await connectButton.count()) {
    await expect(connectButton).toBeVisible();
  } else {
    await expect(connectedLabel).toBeVisible();
  }

  await page.goto('/fitbit');
  await expect(page.getByRole('heading', { name: 'Fitbit Metrics' })).toBeVisible();
});
