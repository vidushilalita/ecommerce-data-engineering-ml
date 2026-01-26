# Kafka Consumer for Real-time Transaction Processing
import sys
import json
import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from kafka import KafkaConsumer

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.logger import get_logger
from src.utils.storage import DataLakeStorage

logger = get_logger(__name__)


class TransactionConsumer:
    """Kafka consumer for dual-stream (users and transactions)"""
    
    def __init__(
        self,
        bootstrap_servers: str = 'localhost:9092',
        group_id: str = 'recomart-consumer-group',
        api_base_url: str = 'http://localhost:8000'
    ):
        """
        Initialize Kafka consumer
        
        Args:
            bootstrap_servers: Kafka broker address
            group_id: Consumer group ID
        """
        self.topics = ['recomart-users', 'recomart-transactions']
        self.api_base_url = api_base_url
        self.storage = DataLakeStorage()
        
        self.consumer = KafkaConsumer(
            *self.topics,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            enable_auto_commit=True
        )
        
        logger.info(f"Initialized Kafka consumer for topics {self.topics}")
    
    def forward_to_api(self, event: Dict[str, Any], topic: str):
        """Forward event to internal API endpoint"""
        endpoint = ""
        if topic == 'recomart-users':
            endpoint = "/internal/ingest-user"
        elif topic == 'recomart-transactions':
            endpoint = "/internal/ingest-transaction"
        
        if not endpoint:
            return

        url = f"{self.api_base_url}{endpoint}"
        try:
            response = requests.post(url, json=event, timeout=5)
            if response.status_code == 200:
                logger.info(f"Forwarded {topic} event to API successfully")
            else:
                logger.error(f"Failed to forward {topic} event. API Status: {response.status_code}")
        except Exception as e:
            logger.error(f"Error calling internal API: {str(e)}")

    def consume_stream(self):
        """Consume messages and forward to API"""
        logger.info("=" * 60)
        logger.info("Starting Dual-Stream Kafka Consumer")
        logger.info("=" * 60)
        
        try:
            for message in self.consumer:
                topic = message.topic
                event = message.value
                logger.info(f"Consumed message from {topic}")
                
                # Forward to API
                self.forward_to_api(event, topic)
                
                # Also optionally archive to data lake (streaming layer)
                # (Removing buffer logic for simplicity/direct streaming as requested)
                
        except KeyboardInterrupt:
            logger.info("Consumer interrupted by user")
        except Exception as e:
            logger.error(f"Consumer error: {str(e)}", exc_info=True)
    
    def close(self):
        """Close consumer connection"""
        self.consumer.close()
        logger.info("Kafka consumer closed")


def main():
    """Main execution"""
    try:
        consumer = TransactionConsumer()
        consumer.consume_stream()
        consumer.close()
        return 0
    except Exception as e:
        logger.critical(f"Consumer failed: {str(e)}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
