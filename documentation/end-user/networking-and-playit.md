# Connecting Friends and Networking

**Audience:** people trying to let friends join a server

auto-mcs includes a playit.gg integration intended to provide remote access without requiring traditional router port forwarding. Follow the playit setup flow shown by the application and use the generated address when sharing the server with friends.

If players are connecting on the same local network, use the host computer's local address and the server port shown by the application. If players are connecting from outside the network, verify that the server is running and use the external address or playit address rather than a local-only address.

When nobody can connect, check these in order:

1. Confirm the server is running and has finished starting.
2. Confirm players are using the correct address and port.
3. Check firewall rules for the application and server port.
4. Confirm the selected network and playit integration are enabled.
5. Check the console for a bind, port, or startup error.

Do not expose administrative credentials or Telepath pairing information in public chat.