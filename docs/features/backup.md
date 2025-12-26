# Backup & Restore

Streaklet provides built-in backup and restore functionality to safeguard your habit tracking data.

## Overview

Backup features:

- **Export profile data** - JSON format for easy portability
- **Import data** - Restore or merge backups
- **Multiple profiles** - Export all or specific profiles
- **Complete history** - Includes tasks, completions, and settings

## Exporting Data

### Via Web Interface

1. Navigate to **Settings**
2. Scroll to **Backup & Restore** section
3. Click **"Export Profile Data"**
4. A JSON file will download: `streaklet-backup-YYYY-MM-DD.json`

### Via API

**Export single profile:**
```bash
curl -H "X-Profile-Id: 1" \
  http://localhost:8080/api/backup/profile/1 \
  > profile-1-backup.json
```

**Export all profiles:**
```bash
curl http://localhost:8080/api/backup/all \
  > all-profiles-backup.json
```

## Backup Contents

A backup JSON file contains:

```json
{
  "version": "1.0",
  "exported_at": "2025-12-25T10:30:00Z",
  "profiles": [
    {
      "profile": {
        "name": "Mom",
        "color": "#3b82f6"
      },
      "tasks": [
        {
          "title": "Morning run",
          "description": "30 minute jog",
          "required": true,
          "active": true,
          "fitbit_auto_check": false
        }
      ],
      "task_checks": [
        {
          "task_title": "Morning run",
          "date": "2025-12-20",
          "checked": true
        }
      ],
      "daily_status": [
        {
          "date": "2025-12-20",
          "completed_at": "2025-12-20T19:45:00Z"
        }
      ]
    }
  ]
}
```

## Importing Data

### Import Modes

**Replace Mode** (default):
- Deletes existing profile data
- Replaces with imported data
- **Warning:** This is destructive!

**Merge Mode**:
- Preserves existing data
- Adds new items from backup
- Skips duplicates (by title/date)
- Safer option for restoring partial data

### Via Web Interface

1. Navigate to **Settings**
2. Scroll to **Backup & Restore** section
3. Click **"Import Profile Data"**
4. Select your backup JSON file
5. Choose **Replace** or **Merge** mode
6. Click **Import**

### Via API

**Replace mode:**
```bash
curl -X POST \
  -H "X-Profile-Id: 1" \
  -H "Content-Type: application/json" \
  -d @backup.json \
  http://localhost:8080/api/backup/profile/1?mode=replace
```

**Merge mode:**
```bash
curl -X POST \
  -H "X-Profile-Id: 1" \
  -H "Content-Type: application/json" \
  -d @backup.json \
  http://localhost:8080/api/backup/profile/1?mode=merge
```

**Import all profiles:**
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d @all-profiles-backup.json \
  http://localhost:8080/api/backup/all
```

## Use Cases

### Regular Backups

Schedule regular exports to protect against data loss:

```bash
# Cron job: Daily backup at 2 AM
0 2 * * * curl http://localhost:8080/api/backup/all > /backups/streaklet-$(date +\%Y-\%m-\%d).json
```

### Migration

Moving to a new server or device:

1. Export data from old instance
2. Set up new Streaklet instance
3. Import the backup (replace mode)
4. Verify data integrity

### Data Recovery

If you accidentally delete tasks or profiles:

1. Export current state (just in case)
2. Import previous backup (merge mode to preserve any new data)
3. Verify restoration

### Sharing Data

Share tasks with another user:

1. Export your profile
2. Send JSON to another user
3. They import using merge mode
4. Tasks are added without affecting their existing data

## Best Practices

### Backup Schedule

- **Daily**: If actively tracking habits
- **Weekly**: For casual use
- **Before major changes**: Always backup before:
  - Upgrading Streaklet
  - Deleting profiles
  - Bulk task changes

### Backup Storage

- Keep backups in multiple locations:
  - Local filesystem
  - Cloud storage (Google Drive, Dropbox, etc.)
  - Version control (Git) for change tracking
- Rotate old backups (keep last 30 days)

### Verification

Periodically verify backups are valid:

```bash
# Check JSON is valid
cat backup.json | jq . > /dev/null && echo "Valid JSON"

# Check version field exists
cat backup.json | jq -r .version
```

## Database-Level Backup

For advanced users, you can also backup the SQLite database directly:

### Stop Container

```bash
docker stop streaklet
```

### Copy Database

```bash
# Using volume
docker cp streaklet:/data/app.db ./backup-app.db

# Or from host volume
cp ./data/app.db ./backup-app.db
```

### Restore Database

```bash
# Stop container first
docker stop streaklet

# Replace database
cp ./backup-app.db ./data/app.db

# Ensure proper ownership (non-root container)
chown 1000:1000 ./data/app.db

# Start container
docker start streaklet
```

### Database Backup Advantages

- **Complete snapshot**: Includes all data and metadata
- **Fast**: No JSON processing
- **Reliable**: Direct file copy

### Database Backup Disadvantages

- **Binary format**: Not human-readable
- **Version-specific**: May not work across Streaklet versions
- **All-or-nothing**: Can't selectively restore profiles

## Validation

Backups are validated on import:

- **Version check**: Ensures compatibility
- **Schema validation**: Required fields present
- **Data types**: Correct types for all values
- **Foreign keys**: Tasks referenced in checks exist

Invalid backups are rejected with detailed error messages.

## Troubleshooting

### Import fails: "Invalid version"

Your backup is from an incompatible Streaklet version. Check release notes for migration instructions.

### Import fails: "Invalid profile data"

The JSON structure is invalid. Verify:
- File is valid JSON
- Contains required fields: `version`, `profiles`
- Task titles are unique within each profile

### Merge creates duplicate tasks

Tasks are matched by title. Ensure:
- Titles are exactly the same (case-sensitive)
- No extra whitespace

### Backup file is huge

Large backup files are normal if you have:
- Many profiles
- Months/years of completion history
- Lots of tasks

Consider exporting individual profiles or archiving old data.

## API Reference

See the [Backup & Import API documentation](../api/endpoints.md#backup-import) for complete endpoint details.
