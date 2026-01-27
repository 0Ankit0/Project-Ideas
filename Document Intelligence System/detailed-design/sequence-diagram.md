# Sequence Diagram - Document Intelligence System

## SD-01: Complete Document Processing

```mermaid
sequenceDiagram
    participant Worker as Processing Worker
    participant OCR as OCR Engine
    participant CLS as Classifier
    participant NER as NER Pipeline
    participant KV as KeyValue Extractor
    participant VAL as Validator
    participant DB as Database
    
    Worker->>Worker: dequeueDocument()
    Worker->>+OCR: extractText(documentPath)
    OCR-->>-Worker: ocrResult{text, confidence}
    
    Worker->>+CLS: classify(text)
    CLS-->>-Worker: docType, confidence
    
    Worker->>+NER: extractEntities(text, docType)
    NER-->>-Worker: entities[]
    
    Worker->>+KV: extractPairs(text, docType)
    KV-->>-Worker: keyValues[]
    
    Worker->>+VAL: validate(extraction)
    VAL-->>-Worker: validationResult
    
    Worker->>+DB: saveExtraction(result)
    DB-->>-Worker: saved
    
    Worker->>Worker: notifyComplete()
```

## SD-04: Review & Correction

```mermaid
sequenceDiagram
    participant Reviewer
    participant API as Review API
    participant Review as Review Service
    participant DB as Database
    participant Audit as Audit Logger
    
    Reviewer->>+API: openReviewTask(documentId)
    API->>+Review: getExtraction(documentId)
    Review->>+DB: SELECT extraction
    DB-->>-Review: data
    Review-->>-API: extraction
    API-->>-Reviewer: showReviewUI
    
    Reviewer->>+API: submitCorrections(edits)
    API->>+Review: saveCorrections(edits)
    Review->>+DB: INSERT corrections
    DB-->>-Review: saved
    Review->>+Audit: record("review.completed", documentId)
    Audit-->>-Review: logged
    Review-->>-API: ok
    API-->>-Reviewer: 200 OK
```

## SD-05: Export Extracted Data

```mermaid
sequenceDiagram
    participant Analyst
    participant API as Export API
    participant Export as Export Service
    participant DB as Database
    participant Notify as Notification Service
    
    Analyst->>+API: requestExport(documentIds, format)
    API->>+Export: createExportJob()
    Export->>+DB: INSERT export_job
    DB-->>-Export: jobId
    Export-->>-API: jobQueued
    API-->>-Analyst: 202 Accepted
    
    Export->>+DB: fetchExtractions(documentIds)
    DB-->>-Export: data
    Export->>Export: generateFile()
    Export->>+Notify: exportReady(userId, link)
    Notify-->>-Export: sent
```

## SD-02: NER Entity Extraction

```mermaid
sequenceDiagram
    participant NER as NER Pipeline
    participant Tokenizer
    participant Model as spaCy Model
    participant Rules as Custom Rules
    participant Post as Post-Processor
    
    NER->>+Tokenizer: tokenize(text)
    Tokenizer-->>-NER: tokens[]
    
    NER->>+Model: predict(tokens)
    Model-->>-NER: rawEntities[]
    
    NER->>+Rules: applyCustomRules(text, docType)
    Rules-->>-NER: ruleBasedEntities[]
    
    NER->>NER: mergeEntities()
    NER->>+Post: normalize(entities)
    Post-->>-NER: normalizedEntities[]
```

## SD-03: Table Extraction

```mermaid
sequenceDiagram
    participant TD as Table Detector
    participant CV as CV Model
    participant Parser as Table Parser
    
    TD->>+CV: detectRegions(image)
    CV-->>-TD: tableRegions[]
    
    loop For each table region
        TD->>+Parser: extractData(region)
        Parser-->>Parser: detectRows()
        Parser-->>Parser: detectColumns()
        Parser-->>+Parser: parseCell()
        Parser-->>-TD: {headers, rows}
    end
```
