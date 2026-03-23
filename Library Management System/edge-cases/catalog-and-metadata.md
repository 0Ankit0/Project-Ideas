# Edge Cases - Catalog and Metadata

| Scenario | Impact | Mitigation |
|----------|--------|------------|
| Duplicate bibliographic records created by different staff | Search confusion and split availability | Add duplicate-detection, merge workflow, and canonical-record controls |
| Same title has multiple editions or formats | Patrons place wrong holds or staff check wrong item | Separate work/expression/format metadata clearly in catalog views |
| Barcode assigned twice by mistake | Inventory integrity breaks | Enforce global uniqueness and require supervised override paths |
| Cataloging incomplete when stock arrives | Items exist physically but not discoverably | Support pre-catalog holding states and accession queues |
| Subject or classification changes ripple inconsistently | Search relevance and shelfing degrade | Version metadata changes and reindex affected records |
