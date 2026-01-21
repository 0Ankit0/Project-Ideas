# C4 Code Diagram - Anomaly Detection System

## Detection Pipeline Implementation

```python
# pipeline.py - Complete detection pipeline

from typing import Dict, List, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)

class DetectionPipeline:
    """Orchestrates the anomaly detection process"""
    
    def __init__(
        self,
        feature_engine: FeatureEngine,
        detector: AnomalyDetector,
        alert_service: AlertService,
        threshold: float = 0.8
    ):
        self.feature_engine = feature_engine
        self.detector = detector
        self.alert_service = alert_service
        self.threshold = threshold
        
    def process(self, data_point: Dict) -> Dict:
        """Process a single data point through the pipeline"""
        source_id = data_point['sourceId']
        values = data_point['values']
        
        # Step 1: Feature extraction
        logger.info(f"Extracting features for {source_id}")
        features = self.feature_engine.extract_features(source_id, values)
        
        if not features.get('has_history'):
            logger.debug(f"Insufficient history for {source_id}")
            return {'status': 'skipped', 'reason': 'insufficient_history'}
        
        # Step 2: Anomaly scoring
        feature_vector = self._to_vector(features)
        score = self.detector.score(feature_vector)
        logger.info(f"Anomaly score for {source_id}: {score:.3f}")
        
        # Step 3: Determine if anomaly
        is_anomaly = score > self.threshold
        severity = self._calculate_severity(score)
        
        result = {
            'sourceId': source_id,
            'score': score,
            'isAnomaly': is_anomaly,
            'severity': severity,
            'features': features
        }
        
        # Step 4: Alert if anomaly
        if is_anomaly:
            logger.warning(f"Anomaly detected: {source_id} (severity: {severity})")
            anomaly = self._create_anomaly_record(result)
            self.alert_service.trigger_alert(anomaly)
            
        return result
        
    def _to_vector(self, features: Dict) -> np.ndarray:
        """Convert feature dict to numpy array"""
        keys = ['value', 'mean', 'std', 'z_score']
        return np.array([features.get(k, 0) for k in keys])
        
    def _calculate_severity(self, score: float) -> str:
        if score > 0.95:
            return 'critical'
        elif score > 0.9:
            return 'high'
        elif score > 0.8:
            return 'medium'
        return 'low'
        
    def _create_anomaly_record(self, result: Dict) -> Dict:
        return {
            'id': str(uuid.uuid4()),
            'sourceId': result['sourceId'],
            'score': result['score'],
            'severity': result['severity'],
            'explanation': self._generate_explanation(result),
            'detectedAt': datetime.utcnow().isoformat()
        }
        
    def _generate_explanation(self, result: Dict) -> str:
        features = result['features']
        z_score = features.get('z_score', 0)
        
        if abs(z_score) > 3:
            return f"Value is {abs(z_score):.1f} standard deviations from normal"
        return f"Anomaly score {result['score']:.2f} exceeds threshold"
```

## Alert Service Implementation

```python
# alerting/service.py - Alert routing and delivery

from typing import Dict, List
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class AlertChannel(ABC):
    @abstractmethod
    def send(self, alert: Dict) -> bool:
        pass

class SlackChannel(AlertChannel):
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        
    def send(self, alert: Dict) -> bool:
        from slack_sdk.webhook import WebhookClient
        client = WebhookClient(self.webhook_url)
        
        response = client.send(
            text=f"🚨 Anomaly Detected: {alert['sourceId']}",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Severity*: {alert['severity']}\n"
                                f"*Score*: {alert['score']:.2f}\n"
                                f"*Explanation*: {alert['explanation']}"
                    }
                }
            ]
        )
        return response.status_code == 200

class EmailChannel(AlertChannel):
    def __init__(self, smtp_config: Dict):
        self.smtp_config = smtp_config
        
    def send(self, alert: Dict) -> bool:
        # Implementation for email sending
        pass

class AlertService:
    def __init__(self, channels: List[AlertChannel], rules: List[Dict]):
        self.channels = channels
        self.rules = rules
        self.sent_alerts: Dict[str, datetime] = {}  # For deduplication
        
    def trigger_alert(self, anomaly: Dict) -> bool:
        # Check deduplication
        if self._is_duplicate(anomaly):
            logger.debug(f"Duplicate alert suppressed: {anomaly['sourceId']}")
            return False
            
        # Match rules
        matched_rules = self._match_rules(anomaly)
        
        if not matched_rules:
            logger.debug(f"No rules matched for {anomaly['sourceId']}")
            return False
            
        # Send to channels
        for rule in matched_rules:
            for channel_name in rule.get('channels', []):
                channel = self._get_channel(channel_name)
                if channel:
                    success = channel.send(anomaly)
                    logger.info(f"Alert sent to {channel_name}: {success}")
                    
        self.sent_alerts[anomaly['id']] = datetime.utcnow()
        return True
        
    def _is_duplicate(self, anomaly: Dict, window_seconds: int = 300) -> bool:
        key = f"{anomaly['sourceId']}_{anomaly['severity']}"
        if key in self.sent_alerts:
            elapsed = (datetime.utcnow() - self.sent_alerts[key]).seconds
            return elapsed < window_seconds
        return False
        
    def _match_rules(self, anomaly: Dict) -> List[Dict]:
        matched = []
        for rule in self.rules:
            if rule.get('severity') == anomaly['severity'] or rule.get('severity') == 'all':
                matched.append(rule)
        return matched
```

## Ensemble Detector

```python
# detectors/ensemble.py - Combine multiple detectors

from typing import List
import numpy as np

class EnsembleDetector(AnomalyDetector):
    """Combine multiple detectors for robust detection"""
    
    def __init__(
        self,
        detectors: List[AnomalyDetector],
        weights: List[float] = None,
        strategy: str = 'weighted_average'
    ):
        super().__init__()
        self.detectors = detectors
        self.weights = weights or [1.0] * len(detectors)
        self.strategy = strategy
        
    def train(self, data: np.ndarray) -> None:
        for detector in self.detectors:
            detector.train(data)
        self.is_trained = True
        
    def score(self, data_point: np.ndarray) -> float:
        scores = [d.score(data_point) for d in self.detectors]
        
        if self.strategy == 'weighted_average':
            return np.average(scores, weights=self.weights)
        elif self.strategy == 'max':
            return max(scores)
        elif self.strategy == 'majority_vote':
            votes = [1 if s > 0.5 else 0 for s in scores]
            return sum(votes) / len(votes)
            
        return np.mean(scores)
```

**Module Interaction**:
1. **DetectionPipeline** orchestrates the flow
2. **FeatureEngine** extracts statistical features
3. **AnomalyDetector** (Isolation Forest, Autoencoder, etc.) scores data
4. **EnsembleDetector** combines multiple detectors
5. **AlertService** routes alerts to channels (Slack, Email)
6. **AlertChannel** implementations handle delivery
