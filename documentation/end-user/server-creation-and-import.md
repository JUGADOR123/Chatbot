# Creating and Importing Servers

**Audience:** people managing servers through the prebuilt application

## Create a server

From the main menu, choose the option to create a new server. An instant template is recommended for a first setup. For a customized server, choose the desired Minecraft version and distribution, then adjust the available settings before creation.

auto-mcs supports common distributions including Vanilla, Paper, Fabric, Forge, CraftBukkit, and Spigot. The available choices depend on the selected version and the server type.

You can also create a server from a modpack using the built-in browser or by importing a supported ZIP or `.mrpack` file.

## Import a server

Choose the import option and select the root folder of an existing server. auto-mcs copies the server into its managed server directory, detects its metadata, and creates a backup as part of the import process. The original folder is left untouched.

Importing a server can require internet access and Java initialization. If importing fails, keep the generated error report and check that the selected folder is the server root rather than a parent folder or a single world folder.