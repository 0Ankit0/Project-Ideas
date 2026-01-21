# Code Guidelines - Anomaly Detection System

## Python Project Structure

```
anomaly-detection/
├── src/
│   ├── api/                   # FastAPI endpoints
│   │   ├── __init__.py
│   │   ├── anomalies.py
│   │   └── models.py
│   ├── detectors/             # ML detection algorithms
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── isolation_forest.py
│   │   ├── autoencoder.py
│   │   └── statistical.py
│   ├── features/              # Feature engineering
│   │   ├── __init__.py
│   │   └── engine.py
│   ├── alerting/              # Alert routing
│   │   ├── __init__.py
│   │   ├── router.py
│   │   └── channels.py
│   ├── streaming/             # Stream processing
│   │   └── consumer.py
│   └── training/              # Model training
│       └── trainer.py
├── tests/
├── requirements.txt
└── README.md
```

## Anomaly Detector Base Class

```python
from abc import ABC, abstractmethod
from typing import Dict, List
import numpy as np

class AnomalyDetector(ABC):
    """Abstract base class for anomaly detectors"""
    
    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold
        self.is_trained = False
        
    @abstractmethod
    def train(self, data: np.ndarray) -> None:
        """Train the detector on historical data"""
        pass
        
    @abstractmethod
    def score(self, data_point: np.ndarray) -> float:
        """Return anomaly score between 0 and 1"""
        pass
        
    def detect(self, data_point: np.ndarray) -> bool:
        """Return True if anomaly detected"""
        return self.score(data_point) > self.threshold
```

## Isolation Forest Detector

```python
from sklearn.ensemble import IsolationForest
import numpy as np

class IsolationForestDetector(AnomalyDetector):
    """Isolation Forest-based anomaly detection"""
    
    def __init__(self, contamination: float = 0.01, n_estimators: int = 100):
        super().__init__()
        self.model = IsolationForest(
            contamination=contamination,
            n_estimators=n_estimators,
            random_state=42
        )
        
    def train(self, data: np.ndarray) -> None:
        self.model.fit(data)
        self.is_trained = True
        
    def score(self, data_point: np.ndarray) -> float:
        # Convert decision function to 0-1 score
        raw_score = self.model.decision_function(data_point.reshape(1, -1))[0]
        # Negative scores = anomaly in sklearn
        return 1 / (1 + np.exp(raw_score))  # Sigmoid transform
```

## Autoencoder Detector

```python
import tensorflow as tf
from tensorflow.keras.layers import Dense, Input
from tensorflow.keras.models import Model
import numpy as np

class AutoencoderDetector(AnomalyDetector):
    """Autoencoder-based anomaly detection"""
    
    def __init__(self, input_dim: int, encoding_dim: int = 8):
        super().__init__()
        self.input_dim = input_dim
        self.encoding_dim = encoding_dim
        self.model = self._build_model()
        
    def _build_model(self) -> Model:
        input_layer = Input(shape=(self.input_dim,))
        encoded = Dense(32, activation='relu')(input_layer)
        encoded = Dense(self.encoding_dim, activation='relu')(encoded)
        decoded = Dense(32, activation='relu')(encoded)
        decoded = Dense(self.input_dim, activation='linear')(decoded)
        
        autoencoder = Model(input_layer, decoded)
        autoencoder.compile(optimizer='adam', loss='mse')
        return autoencoder
        
    def train(self, data: np.ndarray, epochs: int = 50) -> None:
        self.model.fit(data, data, epochs=epochs, batch_size=32, verbose=0)
        # Calculate threshold based on training data
        reconstructed = self.model.predict(data)
        mse = np.mean(np.power(data - reconstructed, 2), axis=1)
        self.threshold = np.percentile(mse, 95)
        self.is_trained = True
        
    def score(self, data_point: np.ndarray) -> float:
        reconstructed = self.model.predict(data_point.reshape(1, -1))
        mse = np.mean(np.power(data_point - reconstructed, 2))
        return min(1.0, mse / self.threshold)
```

## Feature Engine

```python
from typing import Dict, List
import numpy as np
from collections import deque

class FeatureEngine:
    """Extract features from streaming data"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.windows: Dict[str, deque] = {}
        
    def extract_features(self, source_id: str, value: float) -> Dict:
        # Initialize window if needed
        if source_id not in self.windows:
            self.windows[source_id] = deque(maxlen=self.window_size)
            
        window = self.windows[source_id]
        window.append(value)
        
        if len(window) < 10:
            return {'value': value, 'has_history': False}
            
        data = np.array(window)
        return {
            'value': value,
            'mean': np.mean(data),
            'std': np.std(data),
            'min': np.min(data),
            'max': np.max(data),
            'z_score': (value - np.mean(data)) / (np.std(data) + 1e-7),
            'percentile': np.percentile(data, 50),
            'has_history': True
        }
```

## FastAPI Endpoint

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional

app = FastAPI()

class DataPoint(BaseModel):
    sourceId: str
    values: Dict[str, float]
    timestamp: Optional[str] = None

class AnomalyResponse(BaseModel):
    dataPointId: str
    anomalyScore: float
    isAnomaly: bool
    severity: str

@app.post("/data", response_model=AnomalyResponse)
async def push_data(data: DataPoint):
    # Extract features
    features = feature_engine.extract_features(
        data.sourceId, 
        data.values
    )
    
    # Score with detector
    score = detector.score(features)
    is_anomaly = score > 0.8
    
    # Determine severity
    if score > 0.95:
        severity = "critical"
    elif score > 0.9:
        severity = "high"
    elif score > 0.8:
        severity = "medium"
    else:
        severity = "low"
        
    return AnomalyResponse(
        dataPointId=str(uuid.uuid4()),
        anomalyScore=score,
        isAnomaly=is_anomaly,
        severity=severity
    )
```

## Dependencies

```txt
# Core
fastapi>=0.95.0
uvicorn>=0.21.0
pydantic>=1.10.0

# ML
scikit-learn>=1.2.0
tensorflow>=2.11.0
numpy>=1.24.0

# Stream Processing
kafka-python>=2.0.0
faust>=1.10.0

# Storage
influxdb-client>=1.36.0
psycopg2-binary>=2.9.5
redis>=4.5.0

# ML Infrastructure
mlflow>=2.2.0

# Alerting
slack-sdk>=3.20.0
sendgrid>=6.9.0
```
