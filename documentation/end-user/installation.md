# Installation and First Launch

**Audience:** people using the prebuilt auto-mcs application

Download the latest auto-mcs release from the [official download page](https://www.auto-mcs.com/download) or the [latest GitHub release](https://github.com/macarooni-man/auto-mcs/releases/latest). Extract the ZIP archive to a folder you control and launch the application. The prebuilt release does not require a traditional installer.

On Linux, the binary may need executable permission:

```text
chmod +x auto-mcs
```

On the first server operation, auto-mcs may initialize Java internally. Allow that operation to finish before retrying. Keep the application folder writable because auto-mcs stores server data, backups, tools, and configuration alongside its user data.

For a first server, use an instant template. Templates are the simplest route to a working server and avoid making advanced distribution settings before the first launch.