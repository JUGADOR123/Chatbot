# Troubleshooting Common Problems

**Audience:** people using a prebuilt auto-mcs release

## Server will not start

Check the custom console and crash report first. Confirm that Java finished installing or updating, that the selected distribution supports the Minecraft version, and that the machine has enough free disk space and memory. Temporarily disable recently installed add-ons and retry.

## Players cannot join

Confirm that the server is fully running, the address and port are correct, and firewall rules allow the application. For remote friends, check the playit integration or other external networking configuration. For a private server, also check access control and whitelist settings.

## Import fails

Select the root folder of the server, not only its world folder. Confirm that the folder contains the expected server files and that there is enough disk space for auto-mcs to copy the server and create a backup. Preserve the original folder until the import has been verified.

## An add-on caused a crash

Disable the newest mod or plugin, confirm that it matches the Minecraft version and server distribution, then start the server again. Restore a recent backup if the server configuration or world was changed at the same time.

When asking for help, include the operating system, Minecraft version, server distribution, the exact error text, and the relevant crash-report section. Do not include passwords, tokens, or private pairing data.