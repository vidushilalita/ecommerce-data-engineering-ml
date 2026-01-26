"""
Kafka Consumer for Real-time Transaction Processing

Consumes transaction events from Kafka, processes them, and stores in data lake.
Enables near real-time feature updates and model serving.
"""

import sys
import json
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
    """Kafka consumer for transaction streaming"""
    
    def __init__(
        self,
        bootstrap_servers: str = 'localhost:9092',
        topic: str = 'recomart-transactions',
        group_id: str = 'recomart-consumer-group'
    ):
        """
        Initialize Kafka consumer
        
        Args:
            bootstrap_servers: Kafka broker address
            topic: Kafka topic to consume from
            group_id: Consumer group ID
        """
        self.topic = topic
        self.storage = DataLakeStorage()
        self.buffer = []
        self.buffer_size = 100  # Batch size for storage
        
        self.consumer = KafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=True
        )
        
        logger.info(f"Initialized Kafka consumer for topic '{topic}', group '{group_id}'")
    
    def process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process individual event
        
        Args:
            event: Transaction event
            
        Returns:
            Processed event
        """
        # Add processing timestamp
        event['processed_at'] = datetime.now().isoformat()
        
        # Convert timestamp to datetime
        if 'timestamp' in event:
            event['timestamp'] = pd.to_datetime(event['timestamp'])
        
        # Add implicit score
        view_mode_scores = {'view': 1, 'add_to_cart': 2, 'purchase': 3}
        event['implicit_score'] = view_mode_scores.get(event['view_mode'], 1)
        
        logger.debug(f"Processed event {event['event_id']}")
        return event
    
    def add_to_buffer(self, event: Dict[str, Any]):
        """Add processed event to buffer"""
        self.buffer.append(event)
        
        # Flush buffer if full
        if len(self.buffer) >= self.buffer_size:
            self.flush_buffer()
    
    def flush_buffer(self):
        """Flush buffer to storage"""
        if not self.buffer:
            return
        
        logger.info(f"Flushing {len(self.buffer)} events to storage...")
        
        # Convert to DataFrame
        df = pd.DataFrame(self.buffer)
        
        # Save to data lake (streaming layer)
        self.storage.save_dataframe(
            df=df,
            source='transactions',
            data_type='streaming',
            filename=f'transactions_stream_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            format='parquet'
        )
        
        logger.info(f" Flushed {len(self.buffer)} events to storage")
        
        # Clear buffer
        self.buffer = []
    
    def consume_stream(self, max_messages: int = None, timeout_ms: int = 1000):
        """
        Consume messages from Kafka topic
        
        Args:
            max_messages: Maximum number of messages to consume (None = infinite)
            timeout_ms: Consumer poll timeout
        """
        logger.info("=" * 60)
        logger.info("Starting Kafka Consumer")
        logger.info("=" * 60)
        
        message_count = 0
        
        try:
            for message in self.consumer:
                # Process event
                event = self.process_event(message.value)
                
                # Add to buffer
                self.add_to_buffer(event)
                
                message_count += 1
                
                # Log progress
                if message_count % 10 == 0:
                    logger.info(f"Consumed {message_count} messages")
                
                # Check max messages
                if max_messages and message_count >= max_messages:
                    logger.info(f"Reached max messages limit: {max_messages}")
                    break
            
            # Flush any remaining events
            self.flush_buffer()
            
            logger.info("=" * 60)
            logger.info(f" Consumed {message_count} total messages")
            logger.info("=" * 60)
            
        except KeyboardInterrupt:
            logger.info("Consumer interrupted by user")
            self.flush_buffer()
        
        except Exception as e:
            logger.error(f"Consumer error: {str(e)}", exc_info=True)
            self.flush_buffer()
    
    def close(self):
        """Close consumer connection"""
        self.flush_buffer()
        self.consumer.close()
        logger.info("Kafka consumer closed")


def main():
    """Main execution"""
    try:
        logger.info("Starting transaction consumer...")
        
        # Initialize consumer
        consumer = TransactionConsumer()
        
        # Consume messages (limit for testing)
        consumer.consume_stream(max_messages=50)
        
        # Close
        consumer.close()
        
        return 0
    
    except Exception as e:
        logger.critical(f"Consumer failed: {str(e)}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
