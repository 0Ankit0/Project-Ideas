# C4 Code Diagram - Document Intelligence System

## Document Processing Worker

```python
# processor.py - Celery worker for document processing

from celery import Celery
from typing import Dict
import logging

app = Celery('document_processor')
logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Orchestrates the AI pipeline"""
    
    def __init__(self):
        self.ocr_engine = TesseractOCR()
        self.classifier = DocumentClassifier()
        self.classifier.load('models/classifier.pkl')
        self.ner_pipeline = NERPipeline()
        self.kv_extractor = KeyValueExtractor()
        self.validator = Validator()
        
    def process(self, document_id: str, file_path: str) -> Dict:
        logger.info(f"Processing document {document_id}")
        
        # Step 1: OCR
        ocr_result = self.ocr_engine.extract_text(file_path)
        logger.info(f"OCR confidence: {ocr_result['confidence']:.2f}")
        
        if ocr_result['confidence'] < 0.8:
            logger.warning("Low OCR confidence, flagging for review")
            
        # Step 2: Classify
        doc_type, cls_confidence = self.classifier.classify(ocr_result['text'])
        logger.info(f"Classified as {doc_type} ({cls_confidence:.2f})")
        
        # Step 3: Extract entities
        entities = self.ner_pipeline.extract_entities(
            ocr_result['text'],
            doc_type=doc_type
        )
        
        # Step 4: Extract key-values
        key_values = self.kv_extractor.extract_pairs(
            ocr_result['text'],
            doc_type=doc_type
        )
        
        # Step 5: Validate
        validation_result = self.validator.validate({
            'entities': entities,
            'keyValues': key_values
        })
        
        result = {
            'documentId': document_id,
            'documentType': doc_type,
            'entities': entities,
            'keyValues': key_values,
            'avgConfidence': self._calc_avg_confidence(entities, key_values),
            'validation': validation_result
        }
        
        # Save to database
        self._save_to_database(result)
        
        return result
        
    def _calc_avg_confidence(self, entities, key_values):
        all_confidences = []
        all_confidences.extend([e['confidence'] for e in entities])
        all_confidences.extend([kv['confidence'] for kv in key_values])
        return sum(all_confidences) / len(all_confidences) if all_confidences else 0
        
    def _save_to_database(self, result):
        # Database save logic
        pass

@app.task
def process_document(document_id: str, file_path: str):
    """Celery task for async processing"""
    processor = DocumentProcessor()
    return processor.process(document_id, file_path)
```

## Key-Value Extractor

```python
# key_value.py - Extract field-value pairs

import re
from typing import List, Dict

class KeyValueExtractor:
    """Extract key-value pairs from text"""
    
    def __init__(self):
        # Domain-specific patterns
        self.patterns = {
            'invoice': {
                'invoice_number': r'Invoice\s*#?\s*:?\s*(\w+)',
                'total': r'Total\s*:?\s*\$?\s*([\d,]+\.?\d*)',
                'date': r'Date\s*:?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
            },
            'resume': {
                'name': r'Name\s*:?\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',
                'email': r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                'phone': r'(\(\d{3}\)\s*\d{3}-\d{4}|\d{3}-\d{3}-\d{4})'
            }
        }
        
    def extract_pairs(self, text: str, doc_type: str) -> List[Dict]:
        if doc_type not in self.patterns:
            return []
            
        key_values = []
        patterns = self.patterns[doc_type]
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1)
                key_values.append({
                    'key': key,
                    'value': value,
                    'confidence': 0.9,  # Pattern-based = high confidence
                    'manuallyVerified': False
                })
                
        return key_values
        
    def add_pattern(self, doc_type: str, key: str, pattern: str):
        """Add custom extraction pattern"""
        if doc_type not in self.patterns:
            self.patterns[doc_type] = {}
        self.patterns[doc_type][key] = pattern
```

## Validator

```python
# validator.py - Validate extracted data

from typing import Dict, List

class Validator:
    """Validate extraction results"""
    
    def validate(self, extraction: Dict) -> Dict:
        errors = []
        warnings = []
        
        # Check confidence scores
        low_confidence_fields = []
        for kv in extraction.get('keyValues', []):
            if kv['confidence'] < 0.7:
                low_confidence_fields.append(kv['key'])
                
        if low_confidence_fields:
            warnings.append({
                'type': 'low_confidence',
                'fields': low_confidence_fields,
                'message': 'Some fields have low extraction confidence'
            })
            
        # Business rule validation
        if extraction.get('documentType') == 'invoice':
            errors.extend(self._validate_invoice(extraction))
            
        return {
            'isValid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
        
    def _validate_invoice(self, extraction: Dict) -> List[Dict]:
        errors = []
        kv_dict = {kv['key']: kv['value'] for kv in extraction.get('keyValues', [])}
        
        # Check required fields
        required = ['invoice_number', 'total', 'date']
        for field in required:
            if field not in kv_dict:
                errors.append({
                    'type': 'missing_field',
                    'field': field,
                    'message': f'Required field {field} not found'
                })
                
        return errors
```

**Module Interaction**:
1. **DocumentProcessor** orchestrates the pipeline
2. **OCREngine** extracts text from images
3. **DocumentClassifier** identifies document type
4. **NERPipeline** extracts named entities
5. **KeyValueExtractor** finds field-value pairs
6. **Validator** checks accuracy and completeness
