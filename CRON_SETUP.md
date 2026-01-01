# Cron Setup Instructions for Music Organizer

This guide will help you set up the Music Organizer to run automatically every night via cron.

## Your Configuration

- **Wrapper script**: `/mnt/filesvolume/programs/music_organizer_tool/run_music_organizer.sh`
- **Configuration file**: `/mnt/filesvolume/programs/music_organizer_tool/.env`
- **Mode**: In-place reorganization (files are moved, not copied)
- **Logs**: Saved to `~/logs/music_organizer/`

## Step 0: Configure the .env File

The wrapper script loads configuration from a `.env` file to keep sensitive information like API keys separate from the code.

### Create Your .env File

If you haven't already, create your `.env` file from the template:

```bash
cd /mnt/filesvolume/programs/music_organizer_tool
cp .env.example .env
```

### Edit the Configuration

Open the `.env` file and update the values:

```bash
nano .env
```

Update these settings:

```bash
# Path to the music organizer script directory
SCRIPT_DIR="/mnt/filesvolume/programs/music_organizer_tool"

# Path to the music directory (source and destination for in-place reorganization)
MUSIC_DIR="/path/to/your/music"

# AcoustID API key for audio fingerprinting
ACOUSTID_KEY="your_actual_api_key_here"
```

Save and exit (Ctrl+X, Y, Enter).

**Important**: The `.env` file is automatically excluded from version control (via `.gitignore`) to protect your API keys and configuration.

## Step 1: Test the Wrapper Script Manually

Before setting up cron, **test the script manually** to ensure it works correctly.

### Option A: Test with Dry Run (Recommended First)

Temporarily add `--dryrun` flag to preview changes:

```bash
# Edit the wrapper script
nano /mnt/filesvolume/programs/music_organizer_tool/run_music_organizer.sh

# Find the line:
# python music_organizer.py "$MUSIC_DIR" "$MUSIC_DIR" --move --acoustid-key "$ACOUSTID_KEY"

# Change it to:
# python music_organizer.py "$MUSIC_DIR" "$MUSIC_DIR" --move --acoustid-key "$ACOUSTID_KEY" --dryrun

# Save and exit (Ctrl+X, Y, Enter)
```

Then run the script:

```bash
/mnt/filesvolume/programs/music_organizer_tool/run_music_organizer.sh
```

Check the log file to review what would happen:

```bash
# List log files (newest first)
ls -lht ~/logs/music_organizer/

# View the latest log
cat ~/logs/music_organizer/cron_*.log | tail -n 100
```

### Option B: Run for Real

If you're confident and want to organize files immediately:

```bash
/mnt/filesvolume/programs/music_organizer_tool/run_music_organizer.sh
```

Check the results in the log:

```bash
cat ~/logs/music_organizer/cron_*.log | tail -n 100
```

## Step 2: Set Up Cron Job

Once you've verified the script works, set up the cron job.

### Open Crontab Editor

```bash
crontab -e
```

If prompted to choose an editor, select `nano` (usually option 1).

### Add the Cron Entry

Add this line at the end of the file to run nightly at 2:00 AM:

```cron
# Run Music Organizer every night at 2:00 AM
0 2 * * * /mnt/filesvolume/programs/music_organizer_tool/run_music_organizer.sh
```

**Other schedule options:**

```cron
# Every night at midnight
0 0 * * * /mnt/filesvolume/programs/music_organizer_tool/run_music_organizer.sh

# Every night at 3:30 AM
30 3 * * * /mnt/filesvolume/programs/music_organizer_tool/run_music_organizer.sh

# Every 6 hours
0 */6 * * * /mnt/filesvolume/programs/music_organizer_tool/run_music_organizer.sh

# Twice daily (6 AM and 6 PM)
0 6,18 * * * /mnt/filesvolume/programs/music_organizer_tool/run_music_organizer.sh
```

### Save and Exit

- In nano: Press `Ctrl+X`, then `Y`, then `Enter`
- In vi/vim: Press `Esc`, type `:wq`, press `Enter`

## Step 3: Verify Cron Entry

Check that your cron job was added successfully:

```bash
crontab -l
```

You should see your entry listed.

## Step 4: Test the Cron Job (Optional)

To test if cron will actually run your script, set it to run in a few minutes:

```bash
# Check current time
date

# Edit crontab
crontab -e

# If current time is 14:23, set it to run at 14:28
# Add this line temporarily:
28 14 * * * /mnt/filesvolume/programs/music_organizer_tool/run_music_organizer.sh

# Save and exit
```

Wait for the scheduled time and check if a new log file appears:

```bash
# Watch for new log files
watch -n 5 'ls -lht ~/logs/music_organizer/ | head -n 5'

# Or check manually
ls -lht ~/logs/music_organizer/
```

Once verified, change the cron entry back to your desired schedule (e.g., nightly at 2 AM).

## Monitoring and Logs

### View Recent Logs

```bash
# List all log files (newest first)
ls -lht ~/logs/music_organizer/

# View the latest log file
cat ~/logs/music_organizer/cron_*.log | tail -n 100

# View a specific log file
cat ~/logs/music_organizer/cron_20260101_020000.log

# Search for errors in logs
grep -i error ~/logs/music_organizer/cron_*.log

# See summary of last run
grep "ORGANIZATION SUMMARY" ~/logs/music_organizer/cron_*.log -A 10 | tail -n 12
```

### What to Look For in Logs

A successful run will show:
- Virtual environment activation
- Python version being used
- Files processed
- Organization summary with counts
- Exit code: 0 (success)

### Log File Retention

The wrapper script automatically deletes log files older than 30 days to save disk space.

## Troubleshooting

### Cron Job Not Running

1. **Check if cron service is running:**
   ```bash
   sudo systemctl status cron
   ```

2. **Check system cron logs:**
   ```bash
   grep CRON /var/log/syslog | tail -n 20
   ```

3. **Verify crontab entry:**
   ```bash
   crontab -l
   ```

### Script Runs But Fails

1. **Check the log files:**
   ```bash
   cat ~/logs/music_organizer/cron_*.log
   ```

2. **Common issues:**
   - Virtual environment not activated: Check if `.venv` exists in script directory
   - Dependencies not installed: Run `uv pip install -r requirements.txt`
   - Music directory doesn't exist: Verify `/mnt/filesvolume/photos` exists
   - Permission issues: Check read/write permissions on music directory

### No Log Files Created

1. **Test wrapper script manually:**
   ```bash
   /mnt/filesvolume/programs/music_organizer_tool/run_music_organizer.sh
   ```

2. **Check log directory exists:**
   ```bash
   ls -ld ~/logs/music_organizer/
   ```

3. **Check script permissions:**
   ```bash
   ls -l /mnt/filesvolume/programs/music_organizer_tool/run_music_organizer.sh
   ```
   Should show `-rwx` (executable).

## Modifying the Configuration

To change settings like the music directory, AcoustID key, or other options, edit the `.env` file:

```bash
nano /mnt/filesvolume/programs/music_organizer_tool/.env
```

Update the values as needed:

```bash
# Configuration
SCRIPT_DIR="/mnt/filesvolume/programs/music_organizer_tool"
MUSIC_DIR="/path/to/your/music"
ACOUSTID_KEY="your_api_key"
```

Make your changes, save, and exit. The changes will take effect the next time the script runs.

## Disabling the Cron Job

To temporarily disable the cron job without deleting it:

```bash
crontab -e

# Add a # at the beginning of the line to comment it out:
# 0 2 * * * /mnt/filesvolume/programs/music_organizer_tool/run_music_organizer.sh
```

To completely remove the cron job:

```bash
crontab -e

# Delete the entire line, save, and exit
```

## Summary Checklist

- [ ] Installed uv (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- [ ] Virtual environment created with `uv venv`
- [ ] Dependencies installed with `uv pip install -r requirements.txt`
- [ ] Created `.env` file from `.env.example` template
- [ ] Configured `.env` with correct paths and AcoustID API key
- [ ] Wrapper script created and executable
- [ ] Tested wrapper script manually (with `--dryrun` first)
- [ ] Verified log files are created in `~/logs/music_organizer/`
- [ ] Added cron entry with `crontab -e`
- [ ] Verified cron entry with `crontab -l`
- [ ] Checked cron service is running
- [ ] Tested cron job with near-future time (optional)
- [ ] Set final schedule (e.g., nightly at 2 AM)
- [ ] Know how to check logs and monitor runs

## Need Help?

- View detailed cron documentation: `man crontab`
- Test cron expressions: https://crontab.guru/
- Check wrapper script: `cat /mnt/filesvolume/programs/music_organizer_tool/run_music_organizer.sh`
- View recent logs: `ls -lht ~/logs/music_organizer/ | head -n 5`
