# Field length recommendations

| Field | Suggested maximum | Reason |
| --- | --- | --- |
| `unit_id` | 64 chars | stable unit identifier |
| `boot_id` | 128 chars | session or boot identifier |
| `software_version` | 32 chars | semantic version string |
| `correlation_id` | 128 chars | request tracking across pipeline |
| `request_type` or command name | 64 chars | compact operational value |
| `error_message` | 512 chars | readable but bounded for logs |

These limits are design guidance for future validation and storage decisions. They help keep message sizes predictable without making the wire format unnecessarily restrictive.
