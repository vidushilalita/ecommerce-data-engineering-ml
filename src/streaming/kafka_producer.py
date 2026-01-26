"""
Kafka Producer for Streaming Transaction Data

Simulates real-time transaction events and publishes them to Kafka topic.
In production, this would receive events from web/mobile applications.
"""

import sys
import json
import time
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from kafka import KafkaProducer

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.logger import get_logger

logger = get_logger(__name__)


class TransactionProducer:
    """Kafka producer for transaction streaming"""
    
    def __init__(
        self,
        bootstrap_servers: str = 'localhost:9092',
        topic: str = 'recomart-transactions'
    ):
        """
        Initialize Kafka producer
        
        Args:
            bootstrap_servers: Kafka broker address
            topic: Kafka topic name
        """
        self.topic = topic
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            acks='all',  # Wait for all replicas
            retries=3,
            max_in_flight_requests_per_connection=1
        )
        logger.info(f"Initialized Kafka producer for topic '{topic}'")
    
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
    
    def send_event(self, event: Dict[str, Any]) -> bool:
        """Send event to Kafka topic"""
        try:
            future = self.producer.send(self.topic, value=event)
            record_metadata = future.get(timeout=10)
            
            logger.info(
                f"Sent event {event['event_id']} to {record_metadata.topic} "
                f"partition {record_metadata.partition} offset {record_metadata.offset}"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to send event: {str(e)}")
            return False
    
    def simulate_transaction_stream(
        self,
        num_events: int = 100,
        delay_seconds: float = 0.5,
        user_ids: list = None,
        item_ids: list = None
    ):
        """
        Simulate a stream of transaction events
        
        Args:
            num_events: Number of events to generate
            delay_seconds: Delay between events
            user_ids: List of user IDs to sample from
            item_ids: List of item IDs to sample from
        """
        logger.info(f"Starting transaction stream simulation ({num_events} events)")
        
        # Default sample IDs
        if user_ids is None:
            user_ids = list(range(1, 101))
        if item_ids is None:
            item_ids = list(range(100, 201))
        
        view_modes = ['view', 'add_to_cart', 'purchase']
        view_mode_weights = [0.7, 0.2, 0.1]  # More views than purchases
        
        sent_count = 0
        failed_count = 0
        
        for i in range(num_events):
            # Sample random transaction
            user_id = random.choice(user_ids)
            item_id = random.choice(item_ids)
            view_mode = random.choices(view_modes, weights=view_mode_weights)[0]
            
            # Create and send event
            event = self.create_transaction_event(user_id, item_id, view_mode)
            
            if self.send_event(event):
                sent_count += 1
            else:
                failed_count += 1
            
            # Log progress
            if (i + 1) % 10 == 0:
                logger.info(f"Progress: {i + 1}/{num_events} events sent")
            
            # Delay between events
            time.sleep(delay_seconds)
        
        logger.info(
            f"Stream simulation complete: {sent_count} sent, {failed_count} failed"
        )
    
    def close(self):
        """Close producer connection"""
        self.producer.flush()
        self.producer.close()
        logger.info("Kafka producer closed")


def main():
    """Main execution for testing"""
    try:
        logger.info("=" * 60)
        logger.info("Kafka Transaction Producer")
        logger.info("=" * 60)
        
        # Initialize producer
        producer = TransactionProducer()
        
        # Simulate stream
        producer.simulate_transaction_stream(
            num_events=50,
            delay_seconds=0.5
        )
        
        # Close
        producer.close()
        
        logger.info("=" * 60)
        logger.info(" Producer test complete")
        logger.info("=" * 60)
        
        return 0
    
    except Exception as e:
        logger.critical(f"Producer failed: {str(e)}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
