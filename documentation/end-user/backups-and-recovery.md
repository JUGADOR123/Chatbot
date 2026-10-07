# Backups and Recovery

**Audience:** server owners protecting worlds and configuration

auto-mcs provides backup management for managed servers. Create a backup before changing distributions, importing a modpack, installing a large add-on set, or editing important server settings.

Use the backup manager to save a backup, review available backups, restore a selected backup, and configure automatic backup behavior. A restore replaces the managed server state with the selected backup, so stop the server first and choose the backup carefully.

Keep at least one backup outside the active server directory when possible. If a server crashes after a recent change, restore the last known-good backup and reapply changes one at a time.