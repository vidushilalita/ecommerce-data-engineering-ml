# Kafka Producer for Streaming Transaction Data
import sys
import json
import time
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from kafka import KafkaProducer

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.logger import get_logger

logger = get_logger(__name__)


class TransactionProducer:
    """Kafka producer for data streaming (users and transactions)"""
    
    def __init__(
        self,
        bootstrap_servers: str = 'localhost:9092'
    ):
        """
        Initialize Kafka producer
        
        Args:
            bootstrap_servers: Kafka broker address
        """
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            acks='all',
            retries=3,
            max_in_flight_requests_per_connection=1
        )
        logger.info(f"Initialized Kafka producer for servers '{bootstrap_servers}'")
    
    def create_transaction_event(
        self,
        user_id: int,
        item_id: int,
        view_mode: str,
        rating: int = None
    ) -> Dict[str, Any]:
        """Create a transaction event"""
        event = {
            'user_id': user_id,
            'item_id': item_id,
            'view_mode': view_mode,
            'rating': rating if rating else random.randint(1, 5),
            'timestamp': datetime.now().isoformat(),
            'event_id': f"{user_id}_{item_id}_{int(time.time() * 1000)}"
        }
        return event

    def create_user_event(self, user_id: int) -> Dict[str, Any]:
        """Create a new user registration event"""
        event = {
            'user_id': user_id,
            'age': random.randint(18, 100),
            'gender': random.choice(['M', 'F']),
            'device': random.choice(['Mobile', 'Desktop', 'Tablet']),
            'timestamp': datetime.now().isoformat()
        }
        return event
    
    def send_event(self, event: Dict[str, Any], topic: str) -> bool:
        """Send event to a specific Kafka topic"""
        try:
            future = self.producer.send(topic, value=event)
            record_metadata = future.get(timeout=10)
            
            logger.info(
                f"Sent event to {record_metadata.topic} "
                f"partition {record_metadata.partition} offset {record_metadata.offset}"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to send event to {topic}: {str(e)}")
            return False
    
    def simulate_transaction_stream(
        self,
        num_events: int = 100,
        delay_seconds: float = 0.5,
        user_ids: list = None,
        item_ids: list = None
    ):
        """Simulate a stream of transaction events"""
        logger.info(f"Starting transaction stream simulation ({num_events} events)")
        
        if user_ids is None: user_ids = list(range(1, 1501))
        if item_ids is None: item_ids = list(range(100, 201))
        
        view_modes = ['view', 'add_to_cart', 'purchase']
        view_mode_weights = [0.7, 0.2, 0.1]
        
        for i in range(num_events):
            user_id = random.choice(user_ids)
            item_id = random.choice(item_ids)
            view_mode = random.choices(view_modes, weights=view_mode_weights)[0]
            
            event = self.create_transaction_event(user_id, item_id, view_mode)
            self.send_event(event, topic='recomart-transactions')
            time.sleep(delay_seconds)

    def simulate_user_stream(self, num_users: int = 50, delay_seconds: float = 0.75):
        """Simulate a stream of new user registration events"""
        logger.info(f"Starting user stream simulation ({num_users} events)")
        
        for i in range(num_users):
            user_id = random.randint(1, 1501)
            event = self.create_user_event(user_id)
            self.send_event(event, topic='recomart-users')
            time.sleep(delay_seconds)
    
    def close(self):
        """Close producer connection"""
        self.producer.flush()
        self.producer.close()
        logger.info("Kafka producer closed")


def main():
    """Main execution for testing both streams"""
    try:
        producer = TransactionProducer()
        
        # Simulate Users
        producer.simulate_user_stream(num_users=random.randint(1, 50), delay_seconds=random.uniform(0.1, 0.5))
        
        # Simulate Transactions
        producer.simulate_transaction_stream(num_events=random.randint(1, 100), delay_seconds=random.uniform(0.1, 0.5))
        
        producer.close()
        return 0
    except Exception as e:
        logger.critical(f"Producer failed: {str(e)}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
