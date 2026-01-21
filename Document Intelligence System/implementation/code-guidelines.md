# Code Guidelines - Document Intelligence System

## Python Project Structure

```
document-intelligence/
├── src/
│   ├── api/                   # FastAPI endpoints
│   │   ├── __init__.py
│   │   ├── documents.py
│   │   └── extractions.py
│   ├── ai/                    # AI/ML components
│   │   ├── __init__.py
│   │   ├── ocr.py
│   │   ├── classifier.py
│   │   ├── ner.py
│   │   └── key_value.py
│   ├── workers/               # Celery workers
│   │   ├── __init__.py
│   │   └── processor.py
│   ├── models/                # Data models
│   │   ├── __init__.py
│   │   └── entities.py
│   └── utils/
├── tests/
├── requirements.txt
└── README.md
```

## OCR Implementation

```python
from abc import ABC, abstractmethod
import pytesseract
from PIL import Image

class OCREngine(ABC):
    """Abstract base for OCR implementations"""
    
    @abstractmethod
    def extract_text(self, image_path: str) -> dict:
        pass

class TesseractOCR(OCREngine):
    """Open-source Tesseract OCR"""
    
    def __init__(self, language='eng'):
        self.language = language
        
    def extract_text(self, image_path: str) -> dict:
        image = Image.open(image_path)
        
        # Get OCR data with confidence
        ocr_data = pytesseract.image_to_data(
            image,
            lang=self.language,
            output_type=pytesseract.Output.DICT
        )
        
        # Extract text and calculate avg confidence
        text = pytesseract.image_to_string(image, lang=self.language)
        confidences = [c for c in ocr_data['conf'] if c != -1]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return {
            'text': text.strip(),
            'confidence': avg_confidence / 100,  # Normalize to 0-1
            'metadata': ocr_data
        }
```

## NER Pipeline

```python
import spacy
from typing import List, Dict

class NERPipeline:
    """Named Entity Recognition using spaCy"""
    
    def __init__(self, model_name='en_core_web_sm'):
        self.nlp = spacy.load(model_name)
        
    def extract_entities(self, text: str, doc_type: str = None) -> List[Dict]:
        doc = self.nlp(text)
        
        entities = []
        for ent in doc.ents:
            entities.append({
                'type': ent.label_,
                'value': ent.text,
                'start': ent.start_char,
                'end': ent.end_char,
                'confidence': self._calculate_confidence(ent)
            })
            
        # Apply domain-specific post-processing
        if doc_type:
            entities = self._postprocess(entities, doc_type)
            
        return entities
        
    def _calculate_confidence(self, entity) -> float:
        # Simple heuristic: longer entities are more confident
        return min(1.0, 0.7 + len(entity.text.split()) * 0.1)
        
    def _postprocess(self, entities: List[Dict], doc_type: str) -> List[Dict]:
        # Domain-specific entity filtering/normalization
        if doc_type == 'invoice':
            # Keep only invoice-relevant entities
            relevant_types = ['PERSON', 'ORG', 'MONEY', 'DATE']
            entities = [e for e in entities if e['type'] in relevant_types]
            
        return entities
```

## Document Classifier

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
import joblib

class DocumentClassifier:
    """ML-based document classification"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000)
        self.model = RandomForestClassifier(n_estimators=100)
        
    def train(self, texts: List[str], labels: List[str]):
        X = self.vectorizer.fit_transform(texts)
        self.model.fit(X, labels)
        
    def classify(self, text: str) -> tuple:
        X = self.vectorizer.transform([text])
        
        # Get prediction and confidence
        prediction = self.model.predict(X)[0]
        probabilities = self.model.predict_proba(X)[0]
        confidence = max(probabilities)
        
        return prediction, confidence
        
    def save(self, path: str):
        joblib.dump({
            'vectorizer': self.vectorizer,
            'model': self.model
        }, path)
        
    def load(self, path: str):
        data = joblib.load(path)
        self.vectorizer = data['vectorizer']
        self.model = data['model']
```

## FastAPI Endpoint

```python
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import uuid

app = FastAPI()

class ExtractionResult(BaseModel):
    documentId: str
    documentType: str
    entities: list
    keyValues: list
    avgConfidence: float

@app.post("/documents", status_code=202)
async def upload_document(file: UploadFile = File(...)):
    # Validate file type
    if not file.filename.endswith(('.pdf', '.jpg', '.png','.jpeg')):
        raise HTTPException(400, "Invalid file type")
        
    # Save to storage
    document_id = str(uuid.uuid4())
    file_path = await save_to_storage(file, document_id)
    
    # Queue for processing
    await queue_processing_job(document_id, file_path)
    
    return {
        "documentId": document_id,
        "status": "queued",
        "estimatedTime": "30 seconds"
    }

@app.get("/documents/{document_id}/extraction")
async def get_extraction(document_id: str):
    extraction = await get_from_database(document_id)
    
    if not extraction:
        raise HTTPException(404, "Document not found")
        
    return extraction
```

## Dependencies

```txt
# Core
fastapi>=0.95.0
uvicorn>=0.21.0
celery>=5.2.0
pydantic>=1.10.0

# AI/ML
pytesseract>=0.3.10
spacy>=3.5.0
scikit-learn>=1.2.0
tensorflow>=2.11.0  # optional

# Image Processing
Pillow>=9.4.0
opencv-python>=4.7.0
pdf2image>=1.16.3

# Database
psycopg2-binary>=2.9.5
sqlalchemy>=2.0.0

# Storage
boto3>=1.26.0  # for S3
```
