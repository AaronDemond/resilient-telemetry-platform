# Step 1 — Review the data each component needs

Before writing any `.proto` code, list out what flows through the system. The main note and [Concept of Operations](Concept of Operations) already described this:

## What a unit reports in every telemetry message

From the main note, section [Scenario](01-resilient-telemetry-platform#Scenario):

- Unit identity: `unit_id`, `boot_id` (session ID), software version
- Source timestamp and sequence number
- Position: latitude, longitude (or a local coordinate pair)
- Battery/fuel estimate
- Equipment temperature
- Connectivity quality
- Health flags
- Mission-neutral status: `AVAILABLE`, `EN_ROUTE`, or `RETURNING`

## What an operator can request

From the same section:

- Change telemetry sampling interval
- Request an immediate health report
- Enable or disable a simulated diagnostic channel
- Acknowledge a maintenance alert

## What the unit sends back when it handles a request

- Whether the request was applied
- The specific fields it confirmed (interval value, channel name, alert ID)
- A correlation ID matching the original request

## What errors look like

- A numeric error code
- A human-readable description
- Optional metadata (which field failed, what value was invalid)

