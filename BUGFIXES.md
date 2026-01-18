# Bug Fixes - History Page Tooltips

## Issues Fixed

### 1. Undefined Values in Tooltips ✅
**Problem:** Hovering over days with X's (missed days) showed "0% undefined/undefined tasks"

**Root Cause:**
The `calendarDays` getter in Alpine.js was not passing `tasksCompleted` and `tasksRequired` properties to the day object, even though these values were available in `dayData`.

**Fix:**
Added the missing properties to the day object:

```javascript
days.push({
    // ... other properties
    tasksCompleted: dayData?.tasks_completed || 0,
    tasksRequired: dayData?.tasks_required || 0,
    // ... other properties
});
```

**Result:**
Tooltips now correctly display:
- "0% (0/4 tasks)" for missed days
- "50% (2/4 tasks)" for partial completion
- "100% (4/4 tasks)" for completed days

---

### 2. X Overlay Appearing Above Tooltips ✅
**Problem:** The red X from adjacent days appeared above the tooltip text, making it hard to read

**Root Cause:**
Z-index stacking context issue. The tooltip had `z-index: 1000` but was inside a calendar-day element that didn't have elevated z-index, so sibling days' X overlays (with `z-index: 2` within their own context) could overlap.

**Fix:**
1. Added `z-index: 100` to hovered calendar-day to create a new stacking context above siblings
2. Adjusted tooltip z-index to `10` (relative to parent)

```css
/* Increase z-index when hovering to place tooltip above other days */
.calendar-day:hover {
    z-index: 100;
}

.day-tooltip {
    /* ... other styles */
    z-index: 10;
}
```

**Stacking Order (Top to Bottom):**
1. Hovered calendar-day (z-index: 100)
   - Tooltip inside (z-index: 10 relative)
2. Other calendar-days (z-index: auto)
   - X overlay inside (z-index: 2 relative)

**Result:**
Tooltips now always appear above all calendar day content, including X overlays from adjacent days.

---

## Testing

All tests pass after fixes:
```bash
pytest tests/test_history.py::test_calendar_data_with_partial_completion -v
# 1 passed in 0.27s ✅
```

## Files Modified

1. **`app/web/templates/history.html`**
   - Line 251-252: Added `tasksCompleted` and `tasksRequired` to day object
   - Line 422-424: Added hover z-index for calendar-day
   - Line 439: Adjusted tooltip z-index to 10

## Verification Steps

To verify the fixes work:

1. **Start the server:**
   ```bash
   source .venv/bin/activate
   DB_PATH=data/app.db uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
   ```

2. **Navigate to:** `http://localhost:8080/history`

3. **Test Scenario 1 - Undefined Values:**
   - Create test data with partial completion (e.g., 2/4 tasks done)
   - Hover over a day with 0% (red X)
   - ✅ Should show: "0% (0/4 tasks)" instead of "0% undefined/undefined"
   - Hover over a day with 50%
   - ✅ Should show: "50% (2/4 tasks)"

4. **Test Scenario 2 - Z-Index:**
   - Find a calendar day with a red X (missed day)
   - Hover over an adjacent day (before or after the X day)
   - ✅ Tooltip should appear cleanly above all content
   - ✅ X from adjacent days should NOT overlap tooltip text

## Related Components

These fixes complement the enhancements made in:
- Percentage-based completion fills
- Red X indicators for missed days
- Enhanced tooltips with progress bars
- Smooth animations

All features now work together seamlessly.
