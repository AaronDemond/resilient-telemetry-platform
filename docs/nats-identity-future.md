# NATS Phase 1 identity and authorization note

## Status

The current Phase 1 local NATS configuration is intentionally minimal and is not release-authentication evidence. It enables JetStream persistence and local loopback access for development, but it does not verify the eventual service identity and authorization model that the v1 system will require.

## Current local configuration

The configured server at [infra/nats/nats-server.conf](../infra/nats/nats-server.conf) exposes the loopback ports and keeps JetStream data under /data/jetstream. This is useful for local development and a clean bootstrap path, but it is not a production-ready identity boundary.

## Future requirement before v1 acceptance

Before application traffic is accepted as verified, NATS should be configured with a controlled identity model that includes:

- per-unit or per-service NKey identities
- no anonymous client access
- explicit authorization rules for allowed subjects or action groups
- a managed seed/credential distribution process kept outside tracked source control
- integration verification that the application can start, publish, and consume only with valid identities

## Why this matters

A JetStream-enabled NATS instance without identity enforcement is suitable for local bootstrap only. It does not establish trust boundaries, does not prove that services are authenticated, and does not satisfy the requirements for a production or release-quality telemetry transport.

## Recommended next step

When the project reaches the next integration milestone, define the NATS auth plan as a first-class deployment artifact and make the identity model part of the release evidence. The local Phase 1 config should remain a development placeholder until the NKey model is verified and recorded.
