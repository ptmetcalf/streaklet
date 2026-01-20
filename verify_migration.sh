#!/bin/bash

# Phase 2 Migration Verification Script
# Verifies that all local formatters have been removed from templates

echo "==================================="
echo "Phase 2 Migration Verification"
echo "==================================="
echo ""

# Check for any remaining local formatter definitions
echo "1. Checking for local formatter function definitions..."
echo ""

ERRORS=0

# Check each template for local format function definitions
check_file() {
    local file=$1
    local pattern=$2
    local name=$3

    if grep -q "$pattern" "$file" 2>/dev/null; then
        echo "❌ FAIL: Found local formatter in $file"
        grep -n "$pattern" "$file" | head -5
        ERRORS=$((ERRORS + 1))
    else
        echo "✅ PASS: No local formatters in $name"
    fi
}

# Check fitbit.html
check_file "app/web/templates/fitbit.html" \
    "^\s*formatNumber(value)" \
    "fitbit.html (formatNumber)"

check_file "app/web/templates/fitbit.html" \
    "^\s*formatDecimal(value)" \
    "fitbit.html (formatDecimal)"

check_file "app/web/templates/fitbit.html" \
    "^\s*formatSleepHours(minutes)" \
    "fitbit.html (formatSleepHours)"

check_file "app/web/templates/fitbit.html" \
    "^\s*formatDateLocal(date)" \
    "fitbit.html (formatDateLocal)"

# Check index.html
check_file "app/web/templates/index.html" \
    "^\s*formatDueDate(dueDate)" \
    "index.html (formatDueDate)"

check_file "app/web/templates/index.html" \
    "^\s*formatCompletedDate(completedAt)" \
    "index.html (formatCompletedDate)"

check_file "app/web/templates/index.html" \
    "^\s*formatFitbitProgress(task)" \
    "index.html (formatFitbitProgress)"

check_file "app/web/templates/index.html" \
    "^\s*getStreakBadgeClass(streak)" \
    "index.html (getStreakBadgeClass)"

# Check household.html
check_file "app/web/templates/household.html" \
    "^\s*formatDueDate(dueDateStr)" \
    "household.html (formatDueDate)"

check_file "app/web/templates/household.html" \
    "^\s*formatFrequency(frequency)" \
    "household.html (formatFrequency)"

# Check settings.html
check_file "app/web/templates/settings.html" \
    "^\s*formatSyncTime(timestamp)" \
    "settings.html (formatSyncTime)"

check_file "app/web/templates/settings.html" \
    "^\s*formatHours(minutes)" \
    "settings.html (formatHours)"

echo ""
echo "2. Checking for this.format* calls (should use global)..."
echo ""

# Check for lingering this.format* calls
check_this_calls() {
    local file=$1
    local name=$2

    if grep -q "this\.format[A-Z]" "$file" 2>/dev/null; then
        echo "❌ FAIL: Found this.format* calls in $file"
        grep -n "this\.format[A-Z]" "$file" | head -5
        ERRORS=$((ERRORS + 1))
    else
        echo "✅ PASS: No this.format* calls in $name"
    fi
}

check_this_calls "app/web/templates/fitbit.html" "fitbit.html"
check_this_calls "app/web/templates/index.html" "index.html"
check_this_calls "app/web/templates/household.html" "household.html"
check_this_calls "app/web/templates/settings.html" "settings.html"

echo ""
echo "3. Verifying utils.js exists and is loaded..."
echo ""

if [ -f "app/web/static/js/utils.js" ]; then
    echo "✅ PASS: utils.js exists"
else
    echo "❌ FAIL: utils.js not found"
    ERRORS=$((ERRORS + 1))
fi

if grep -q "utils.js" "app/web/templates/base.html"; then
    echo "✅ PASS: utils.js loaded in base.html"
else
    echo "❌ FAIL: utils.js not loaded in base.html"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "==================================="
echo "Verification Summary"
echo "==================================="
echo ""

if [ $ERRORS -eq 0 ]; then
    echo "✅ ALL CHECKS PASSED!"
    echo ""
    echo "Phase 2 migration is complete and verified."
    echo "All templates now use global utilities from utils.js."
    exit 0
else
    echo "❌ FOUND $ERRORS ERROR(S)"
    echo ""
    echo "Please review and fix the issues above."
    exit 1
fi
