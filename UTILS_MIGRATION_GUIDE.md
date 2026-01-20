# Utils.js Migration Guide

This guide helps you replace duplicate inline formatters with the consolidated utilities in `/static/js/utils.js`.

## Overview

**Phase 1 Complete**: The `utils.js` file has been created with all consolidated formatters and is now loaded in `base.html`. All functions are available globally on the `window` object.

**Next Steps**: Update templates to use the new utilities (Phase 2+).

---

## Date & Time Formatters

### formatDueDate()
**Replaces:**
- `index.html:510-521` - `formatDueDate()` function
- `household.html:509-530` - `formatDueDate()` function

**Old Code:**
```javascript
formatDueDate(dueDate) {
    if (!dueDate) return '';
    const due = new Date(dueDate + 'T00:00:00');
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const diffDays = Math.ceil((due - today) / (1000 * 60 * 60 * 24));
    // ... more logic
}
```

**New Code:**
```javascript
// Simply call the global function
formatDueDate(dueDate)

// With options
formatDueDate(dueDate, { showEmoji: false, warnOverdue: true })
```

**Locations to Update:**
- `index.html:515` - In `punchListData()` Alpine component
- `household.html:520` - In `householdData()` Alpine component

---

### formatCompletedDate()
**Replaces:**
- `index.html:523-534` - `formatCompletedDate()` function
- `household.html:532-543` - Similar logic

**Old Code:**
```javascript
formatCompletedDate(completedAt) {
    if (!completedAt) return '';
    const completed = new Date(completedAt);
    const diffDays = Math.floor((today - completed) / (1000 * 60 * 60  24));
    if (diffDays === 0) return 'today';
    if (diffDays === 1) return 'yesterday';
    // ... more
}
```

**New Code:**
```javascript
formatCompletedDate(completedAt)
```

**Locations to Update:**
- `index.html:528` - In punch list task rendering
- `household.html:537` - In completion history

---

### formatDateDisplay()
**Replaces:**
- `fitbit.html:1130-1138` - `formatDateDisplay()` function

**Old Code:**
```javascript
formatDateDisplay(dateStr) {
    const date = new Date(dateStr + 'T00:00:00');
    return date.toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}
```

**New Code:**
```javascript
formatDateDisplay(dateStr)
```

**Locations to Update:**
- `fitbit.html:1133` - In "No data" message

---

### formatSyncTime()
**Replaces:**
- `fitbit.html:1140-1150` - `formatSyncTime()` function

**Old Code:**
```javascript
formatSyncTime(timestamp) {
    if (!timestamp) return '-';
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
    });
}
```

**New Code:**
```javascript
formatSyncTime(timestamp)
```

**Locations to Update:**
- `fitbit.html:1145` - In metrics table "Synced At" column

---

### formatDateLocal()
**Replaces:**
- `fitbit.html:865-870` - `formatDateLocal()` function
- Multiple inline implementations

**Old Code:**
```javascript
formatDateLocal(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}
```

**New Code:**
```javascript
formatDateLocal(date)
```

**Locations to Update:**
- `fitbit.html:869` - In `previousDay()` function
- `fitbit.html:881` - In `nextDay()` function
- `fitbit.html:905-906` - In `loadTrendData()` function
- Plus 10+ more locations in `fitbit.html`

---

### parseDateOnly()
**Replaces:**
- ~~`base.html:64-67`~~ - **ALREADY REMOVED** ✅
- All inline date parsing logic

**Old Code:**
```javascript
function parseDateOnly(dateStr) {
    const [year, month, day] = dateStr.split('-').map(Number);
    return new Date(year, month - 1, day);
}
```

**New Code:**
```javascript
parseDateOnly(dateStr)
```

**Locations to Update:**
- Already available globally via utils.js
- All templates can now use this function directly

---

## Metric & Number Formatters

### formatNumber()
**Replaces:**
- `fitbit.html:1073-1076` - `formatNumber()` function
- Inline `.toLocaleString('en-US')` calls

**Old Code:**
```javascript
formatNumber(value) {
    if (value == null) return '-';
    return Math.round(value).toLocaleString('en-US');
}
```

**New Code:**
```javascript
formatNumber(value)
```

**Locations to Update:**
- `fitbit.html:128` - Steps value display
- `fitbit.html:143` - Active minutes display
- `fitbit.html:148` - Calories display
- Plus 50+ more inline usages

---

### formatDecimal()
**Replaces:**
- `fitbit.html:1078-1081` - `formatDecimal()` function

**Old Code:**
```javascript
formatDecimal(value) {
    if (value == null) return '-';
    return value.toFixed(2);
}
```

**New Code:**
```javascript
formatDecimal(value)

// Or with custom decimal places
formatDecimal(value, 3)
```

**Locations to Update:**
- `fitbit.html:156` - Distance display
- `fitbit.html:191` - Cardio fitness display
- Plus 20+ more locations

---

### formatSleepHours()
**Replaces:**
- `fitbit.html:1083-1088` - `formatSleepHours()` function
- Similar logic in multiple places

**Old Code:**
```javascript
formatSleepHours(minutes) {
    if (!minutes) return '-';
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    return `${hours}h ${mins}m`;
}
```

**New Code:**
```javascript
formatSleepHours(minutes)
```

**Locations to Update:**
- `fitbit.html:135` - Sleep value display
- `fitbit.html:295-297` - Stats card sleep averages
- Plus 15+ more locations

---

### formatFitbitProgress()
**Replaces:**
- `index.html:536-570` - `formatFitbitProgress()` function

**Old Code:**
```javascript
formatFitbitProgress(task) {
    if (!task || !task.fitbit_current_value || !task.fitbit_goal_value) return '';
    const current = task.fitbit_current_value;
    const goal = task.fitbit_goal_value;
    // ... complex logic for different metric types
}
```

**New Code:**
```javascript
formatFitbitProgress(task)
```

**Locations to Update:**
- `index.html:88` - Fitbit progress badge in task cards
- Any other Fitbit integration displays

---

### formatMetricValue()
**NEW UTILITY** - Intelligently formats based on metric type

**Usage:**
```javascript
// Automatically chooses the right formatter based on metric type
formatMetricValue(value, 'sleep_minutes')  // → "7h 30m"
formatMetricValue(value, 'steps')          // → "10,342"
formatMetricValue(value, 'distance')       // → "5.23"
```

**Locations to Use:**
- `fitbit.html:261` - Replace inline `formatValue()` with `formatMetricValue()`
- Any other metric display that needs type-aware formatting

---

### formatMetricName()
**Replaces:**
- `fitbit.html:1104-1128` - `formatMetricName()` function

**Old Code:**
```javascript
formatMetricName(key) {
    const names = {
        'steps': 'Steps',
        'sleep_minutes': 'Sleep Duration',
        // ... 20+ more mappings
    };
    return names[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}
```

**New Code:**
```javascript
formatMetricName(key)
```

**Locations to Update:**
- `fitbit.html:260` - Metric table metric name column

---

### formatTrend()
**Replaces:**
- `fitbit.html:1152-1156` - `formatTrend()` function

**Old Code:**
```javascript
formatTrend(value) {
    if (value == null || value === 0) return '—';
    const sign = value >= 0 ? '↑' : '↓';
    return `${sign} ${Math.abs(Math.round(value))}%`;
}
```

**New Code:**
```javascript
formatTrend(value)
```

**Locations to Update:**
- `fitbit.html:328` - Week steps trend display
- `fitbit.html:333` - Week sleep trend display

---

## Task Formatters

### formatRecurrence()
**NEW UTILITY** - Format recurrence patterns for scheduled tasks

**Usage:**
```javascript
formatRecurrence(task)  // → "📅 Weekly on Mon"
```

**Locations to Use:**
- `index.html:169` - Scheduled task metadata badges

---

### formatFrequency()
**NEW UTILITY** - Format household task frequency labels

**Usage:**
```javascript
formatFrequency('weekly')     // → "Weekly"
formatFrequency('todo')       // → "To-Do"
formatFrequency('quarterly')  // → "Quarterly"
```

**Locations to Use:**
- `household.html:58` - Frequency badge display

---

### getTaskTypeLabel()
**NEW UTILITY** - Get human-readable task type labels

**Usage:**
```javascript
getTaskTypeLabel('punch_list')  // → "Todo"
getTaskTypeLabel('scheduled')   // → "Scheduled"
getTaskTypeLabel('daily')       // → "Daily"
```

**Locations to Use:**
- `index.html` - Task card type badges

---

### getTaskTypeBadgeClass()
**NEW UTILITY** - Get CSS class for task type badges

**Usage:**
```javascript
getTaskTypeBadgeClass('punch_list')  // → "badge-todo"
getTaskTypeBadgeClass('scheduled')   // → "badge-scheduled"
```

**Locations to Use:**
- `index.html` - Dynamic badge styling

---

## Validation & Helpers

### isTaskOverdue()
**NEW UTILITY** - Check if a task is overdue

**Usage:**
```javascript
isTaskOverdue(task)  // → true/false
```

**Locations to Use:**
- Replace inline overdue checks in task rendering

---

### getStreakBadgeClass()
**NEW UTILITY** - Get CSS class based on streak length

**Usage:**
```javascript
getStreakBadgeClass(100)  // → "streak-legendary"
getStreakBadgeClass(30)   // → "streak-amazing"
getStreakBadgeClass(5)    // → "streak-building"
```

**Locations to Use:**
- History page streak displays
- Any streak visualization

---

### clamp()
**NEW UTILITY** - Constrain a value between min and max

**Usage:**
```javascript
clamp(value, 0, 100)  // Ensures value is between 0-100
```

---

### debounce()
**NEW UTILITY** - Debounce function calls

**Usage:**
```javascript
const debouncedSearch = debounce(async function(query) {
    await searchTasks(query);
}, 300);
```

**Locations to Use:**
- Search inputs
- Auto-save functionality
- Window resize handlers

---

## Migration Strategy

### Step 1: Test Utils Loading
1. Open browser console on any page
2. Type `formatNumber(12345)`
3. Should see: `"12,345"`
4. Type `formatSleepHours(450)`
5. Should see: `"7h 30m"`

### Step 2: Migrate One Template at a Time

**Priority Order:**
1. **fitbit.html** - Highest duplication (50+ uses)
2. **index.html** - Main page (30+ uses)
3. **household.html** - Moderate use (15+ uses)
4. **settings.html** - Lowest impact (5+ uses)

### Step 3: Search and Replace Pattern

For each template:
```bash
# 1. Search for local function definition
# Example: "formatNumber(value)" in Alpine component

# 2. Delete the local function

# 3. Calls to the function work automatically (now using global)
```

### Step 4: Test After Each Change
- Check browser console for errors
- Test functionality manually
- Verify formatters work correctly

### Step 5: Commit Incrementally
```bash
git add app/web/templates/fitbit.html
git commit -m "refactor: migrate fitbit.html to use utils.js formatters"

git add app/web/templates/index.html
git commit -m "refactor: migrate index.html to use utils.js formatters"
```

---

## Example: Migrating fitbit.html

### Before (lines 1073-1102):
```javascript
function fitbitMetrics() {
    return {
        // ... state ...

        formatNumber(value) {
            if (value == null) return '-';
            return Math.round(value).toLocaleString('en-US');
        },

        formatDecimal(value) {
            if (value == null) return '-';
            return value.toFixed(2);
        },

        formatSleepHours(minutes) {
            if (!minutes) return '-';
            const hours = Math.floor(minutes / 60);
            const mins = Math.round(minutes % 60);
            return `${hours}h ${mins}m`;
        },

        // ... more methods ...
    }
}
```

### After:
```javascript
function fitbitMetrics() {
    return {
        // ... state ...

        // formatNumber, formatDecimal, formatSleepHours now use global utils.js
        // No local definitions needed - calls work automatically!

        // ... more methods ...
    }
}
```

All usages like `x-text="formatNumber(value)"` continue to work because the functions are now global!

---

## Verification Checklist

After migrating a template:

- [ ] No JavaScript console errors
- [ ] Date formatting displays correctly
- [ ] Number formatting shows commas
- [ ] Sleep hours show "Xh Ym" format
- [ ] Fitbit progress displays correctly
- [ ] Due dates show relative time
- [ ] Trend indicators show arrows
- [ ] Empty states render properly

---

## Troubleshooting

### Functions not defined
**Problem:** `Uncaught ReferenceError: formatNumber is not defined`

**Solution:** Ensure `utils.js` is loaded before the template's inline scripts. Check browser Network tab to confirm `/static/js/utils.js` loads successfully.

### Wrong format output
**Problem:** Formatter returns unexpected value

**Solution:** Check the parameters you're passing. Some utilities have optional parameters:
```javascript
formatDueDate(date, { showEmoji: false })  // Options object
formatDecimal(value, 3)                     // Decimal places
```

### Alpine.js scope issues
**Problem:** `this.formatNumber is not a function` inside Alpine component

**Solution:** Use the global function directly, don't use `this.`:
```javascript
// ❌ Wrong
x-text="this.formatNumber(value)"

// ✅ Correct
x-text="formatNumber(value)"
```

---

## Benefits of Migration

After completing the migration:

1. **Reduced Code**: ~1,300 lines removed across all templates
2. **Consistency**: All pages use identical formatting logic
3. **Maintainability**: Fix bugs once, all pages benefit
4. **Performance**: Shared code means less to parse/execute
5. **Testing**: Can unit test formatters in isolation
6. **Developer Experience**: Clear, documented API for all formatters

---

## Next Phase: Button Consolidation

After utils migration is complete, Phase 2 will create a shared `components.css` file for unified button styles. See main consolidation analysis for details.
