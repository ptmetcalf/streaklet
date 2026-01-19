# Task Types

Streaklet supports three types of tasks to cover different use cases: **Daily Tasks** for building habits, **Todo List** for one-off items, and **Scheduled Tasks** for recurring actions at custom intervals.

## Daily Tasks

Daily tasks are core habits you want to track every day. These are the foundation of your streak tracking.

### Features

- **Always visible** on the Daily tab
- **Counts toward streaks** when marked required
- **Repeats every day** automatically
- **Optional or Required** - Required tasks must be completed to continue your streak

### Best For

- Morning routines (meditation, exercise)
- Daily reading goals
- Hydration tracking
- Medication reminders
- Any habit you want to do every single day

### Example Daily Tasks

- Morning meditation
- 30 minute workout
- Read 10 pages
- Practice guitar 20 minutes
- Drink 8 glasses of water

## Todo List

Todo List tasks are one-off items that need to get done but don't repeat daily. They're perfect for errands, reminders, and short-term goals.

### Features

- **Separate tab** to avoid cluttering your daily habits
- **Optional due dates** - Set deadlines or leave open-ended
- **Auto-archives after 7 days** when completed
- **Does NOT affect streaks** - Completing or ignoring these won't break your streak
- **Collapsible completed section** - Keeps your list clean while showing recent accomplishments

### Best For

- Errands (call dentist, fix faucet, buy groceries)
- One-time projects
- Reminders that aren't tied to a specific date
- Things you want to remember but aren't daily habits

### Example Todo Items

- Call dentist for appointment
- Fix kitchen faucet leak
- Update resume
- Return library books
- Schedule car maintenance

### Due Date Indicators

- ⚠️ **Overdue** - Task is past due date (shown in red)
- 📅 **Due today** - Task is due today
- 📅 **Due tomorrow** - Task is due tomorrow
- 📅 **Due in X days** - Shows countdown to due date

## Scheduled Tasks

Scheduled tasks are recurring actions that happen at custom intervals (weekly, monthly, or every N days). They're perfect for maintenance tasks and periodic reminders.

### Features

- **Custom recurrence patterns**:
  - **Weekly** - Every Monday, Tuesday, etc.
  - **Monthly** - Specific day of month (1st, 15th, etc.)
  - **Every N days** - Flexible interval (every 3 days, every 2 weeks, etc.)
- **Only appears on due dates** - Doesn't clutter your daily list when not due
- **Counts toward completion** when due and marked as required
- **Automatically calculates next occurrence** after completion

### Best For

- Weekly chores (take out trash on Thursdays)
- Monthly maintenance (change air filter on the 1st)
- Periodic reminders (give dog medicine every 7 days)
- Anything that repeats but not daily

### Example Scheduled Tasks

- Take out trash (every Thursday)
- Change air filter (1st of every month)
- Give dog heartworm medicine (every 30 days)
- Water plants (every 3 days)
- Pay rent (1st of every month)

### Recurrence Patterns

**Weekly Pattern:**
```json
{
  "type": "weekly",
  "interval": 1,
  "day_of_week": 3  // 0=Monday, 6=Sunday
}
```

**Monthly Pattern:**
```json
{
  "type": "monthly",
  "interval": 1,
  "day_of_month": 15
}
```

**Days Interval Pattern:**
```json
{
  "type": "days",
  "interval": 7  // Every 7 days
}
```

## Task Type Comparison

| Feature | Daily | Todo List | Scheduled |
|---------|-------|-----------|-----------|
| **Frequency** | Every day | One-time | Custom interval |
| **Affects Streak** | Yes (if required) | No | Yes (if required, when due) |
| **Visibility** | Always on Daily tab | Separate tab | Only when due |
| **Due Dates** | N/A | Optional | Calculated automatically |
| **Auto-Archives** | No | After 7 days | No |
| **Best For** | Daily habits | Errands & reminders | Periodic maintenance |

## Managing Tasks

### Creating Tasks

1. Go to **Settings** page
2. Click **Add New Task**
3. Select task category:
   - **Daily Recurring** - For daily habits
   - **One-Off (Todo List)** - For errands
   - **Scheduled Recurring** - For periodic tasks
4. Fill in details (title, due date for todos, recurrence for scheduled)
5. Mark as **Required** if it should affect your streak
6. Click **Save**

### Filtering in Settings

Use the filter buttons to view specific task types:

- **All** - See all active tasks
- **Daily** - Only daily habits
- **Todo** - Only incomplete todo items (completed items are hidden)
- **Scheduled** - Only scheduled recurring tasks

This keeps your settings organized even with 40+ tasks.

### Editing Tasks

1. Go to **Settings** page
2. Filter to find your task
3. Click **Edit** next to the task
4. Make changes
5. Click **Save**

**Note:** Completed todo items are automatically hidden in Settings since there's nothing to manage.

### Completing Tasks

**Daily and Scheduled Tasks:**
- Tap the checkbox in the checklist
- Scheduled tasks automatically calculate next occurrence

**Todo List Items:**
- Tap the checkbox to mark complete
- Completed items move to collapsible section
- Auto-archive after 7 days

## Tips & Best Practices

### Starting Out

- **Begin with 3-5 daily tasks** - Don't overwhelm yourself
- **Use required flags wisely** - Only mark truly essential habits as required
- **Add todos as they come up** - Quick capture prevents forgetting

### Organizing Your Tasks

- **Keep daily list focused** - If something doesn't need to be daily, use scheduled or todo
- **Use scheduled for predictable recurring tasks** - Takes them off your daily list
- **Review todo list weekly** - Archive or delete stale items

### Streak Strategy

- **Make required tasks achievable** - Your streak depends on these
- **Use optional tasks for stretch goals** - Build consistency without pressure
- **Don't let todos break your streak** - They're intentionally excluded from streak calculation

### Mobile Usage

- **Swipe through tabs** - Quick navigation on touch devices
- **Install as PWA** - Add to home screen for native app feel
- **Badge counts** - Tab badges show incomplete counts at a glance

## Next Steps

- [Enable Fitbit Integration](fitbit.md) - Auto-complete daily tasks with fitness data
- [Configure Profiles](profiles.md) - Set up tasks for family members
- [View API Reference](../api/endpoints.md) - Programmatically manage tasks
