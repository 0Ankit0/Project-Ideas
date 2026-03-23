# Edge Cases - Ticket Intake and Attachments

| Scenario | Impact | Mitigation |
|----------|--------|------------|
| Client uploads unsupported image type | Ticket evidence is unusable | Reject early with supported-format guidance |
| Screenshot exceeds size limit | Upload stalls or degrades UX | Compress client-side when possible and show size rules before upload |
| Malware detected in attachment | Evidence becomes unsafe to open | Quarantine file, notify internal users, keep ticket open for replacement evidence |
| Duplicate ticket created by multiple client contacts | Fragmented communication and duplicate work | Suggest similar tickets during submission and allow merge/link during triage |
| Ticket created without enough reproduction detail | Triage slows and SLA risk rises | Require minimum description fields and a structured clarification workflow |
