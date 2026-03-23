# Edge Cases - API and UI

| Scenario | Impact | Mitigation |
|----------|--------|------------|
| Client sees stale ticket status after internal update | Trust drops | Push timeline updates via polling or real-time channels with cache invalidation |
| Two users edit the same ticket at once | Last-write-wins causes data loss | Use version checks and conflict messaging |
| Long activity timelines load slowly | UI becomes unusable | Cursor pagination and incremental rendering |
| Search results leak unauthorized project names | Security issue | Enforce scope checks before indexing and before rendering results |
| Attachment preview fails in browser | Evidence appears missing | Provide download fallback and storage health alerting |
