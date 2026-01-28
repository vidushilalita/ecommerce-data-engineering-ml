# Feature Store SQL Schema Documentation

## Overview

The feature store uses **SQLite** as the backend database for storing and managing features for the recommendation system. This lightweight implementation provides feature store functionality for local development and can be extended to production-grade systems like PostgreSQL or Feast.

**Database File**: `feature_store.db`

---

## Database Schema

### 1. User Features Table

Stores computed features for each user in the system.

```sql
CREATE TABLE IF NOT EXISTS user_features (
    user_id INTEGER PRIMARY KEY,
    user_activity_count INTEGER,
    avg_rating_given REAL,
    purchase_ratio REAL,
    preferred_category TEXT,
    age INTEGER,
    gender TEXT,
    device TEXT,
    gender_encoded INTEGER,
    device_encoded INTEGER,
    age_normalized REAL,
    updated_at TIMESTAMP
);
```

#### Column Descriptions

| Column Name | Data Type | Description | Computation Logic |
|------------|-----------|-------------|-------------------|
| `user_id` | INTEGER | Primary key, unique user identifier | - |
| `user_activity_count` | INTEGER | Total number of user interactions | `COUNT(transactions WHERE user_id = X)` |
| `avg_rating_given` | REAL | Average rating given by user | `AVG(rating WHERE user_id = X)` |
| `purchase_ratio` | REAL | Proportion of interactions that are purchases | `COUNT(purchases) / COUNT(total_interactions)` |
| `preferred_category` | TEXT | Most frequently browsed category | `MODE(category WHERE user_id = X)` |
| `age` | INTEGER | User age from profile | Source: `users` table |
| `gender` | TEXT | User gender (M/F) | Source: `users` table |
| `device` | TEXT | Preferred device (mobile/desktop/tablet) | Source: `users` table |
| `gender_encoded` | INTEGER | Encoded gender for ML models | Label encoding: {M: 0, F: 1} |
| `device_encoded` | INTEGER | Encoded device for ML models | Label encoding: {mobile: 0, desktop: 1, tablet: 2} |
| `age_normalized` | REAL | Normalized age (0-1 scale) | MinMax normalization |
| `updated_at` | TIMESTAMP | Last update timestamp | `CURRENT_TIMESTAMP` |

#### Example Query

```sql
-- Get user features for specific users
SELECT * FROM user_features 
WHERE user_id IN (1, 2, 3);

-- Get highly active users
SELECT user_id, user_activity_count, avg_rating_given
FROM user_features 
WHERE user_activity_count > 50
ORDER BY user_activity_count DESC;
```

---

### 2. Item Features Table

Stores computed features for each product/item in the catalog.

```sql
CREATE TABLE IF NOT EXISTS item_features (
    item_id INTEGER PRIMARY KEY,
    price REAL,
    brand TEXT,
    category TEXT,
    rating REAL,
    in_stock BOOLEAN,
    popularity_score INTEGER,
    avg_item_rating REAL,
    view_to_purchase_rate REAL,
    price_tier TEXT,
    category_encoded INTEGER,
    brand_encoded INTEGER,
    price_normalized REAL,
    updated_at TIMESTAMP
);
```

#### Column Descriptions

| Column Name | Data Type | Description | Computation Logic |
|------------|-----------|-------------|-------------------|
| `item_id` | INTEGER | Primary key, unique item identifier | - |
| `price` | REAL | Product price | Source: `products` table |
| `brand` | TEXT | Product brand name | Source: `products` table |
| `category` | TEXT | Product category | Source: `products` table |
| `rating` | REAL | Base product rating | Source: `products` table |
| `in_stock` | BOOLEAN | Stock availability (0/1) | Source: `products` table |
| `popularity_score` | INTEGER | Number of interactions the item received | `COUNT(interactions WHERE item_id = Y)` |
| `avg_item_rating` | REAL | Average rating received by item | `AVG(rating WHERE item_id = Y)` |
| `view_to_purchase_rate` | REAL | Conversion rate from views to purchases | `COUNT(purchases) / COUNT(views)` |
| `price_tier` | TEXT | Price category (low/medium/high) | Quantile-based binning |
| `category_encoded` | INTEGER | Encoded category for ML models | Label encoding |
| `brand_encoded` | INTEGER | Encoded brand for ML models | Label encoding |
| `price_normalized` | REAL | Normalized price (0-1 scale) | MinMax normalization |
| `updated_at` | TIMESTAMP | Last update timestamp | `CURRENT_TIMESTAMP` |

#### Example Query

```sql
-- Get item features for specific items
SELECT * FROM item_features 
WHERE item_id IN (101, 102, 103);

-- Get popular items with high conversion
SELECT item_id, brand, category, popularity_score, view_to_purchase_rate
FROM item_features 
WHERE popularity_score > 100 
  AND view_to_purchase_rate > 0.3
ORDER BY popularity_score DESC;

-- Get items in specific category
SELECT item_id, brand, price, avg_item_rating
FROM item_features 
WHERE category = 'Electronics'
  AND in_stock = 1
ORDER BY avg_item_rating DESC;
```

---

### 3. Feature Metadata Table

Stores metadata and documentation for all features in the feature store.

```sql
CREATE TABLE IF NOT EXISTS feature_metadata (
    feature_name TEXT PRIMARY KEY,
    feature_type TEXT,
    description TEXT,
    data_type TEXT,
    source_table TEXT,
    computation_logic TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### Column Descriptions

| Column Name | Data Type | Description |
|------------|-----------|-------------|
| `feature_name` | TEXT | Primary key, unique feature identifier |
| `feature_type` | TEXT | Type of feature ('user' or 'item') |
| `description` | TEXT | Human-readable feature description |
| `data_type` | TEXT | SQL data type (INTEGER, REAL, TEXT, BOOLEAN) |
| `source_table` | TEXT | Original source table(s) |
| `computation_logic` | TEXT | How the feature is computed |
| `created_at` | TIMESTAMP | Feature creation timestamp |
| `updated_at` | TIMESTAMP | Last update timestamp |

#### Example Query

```sql
-- Get all user features metadata
SELECT * FROM feature_metadata 
WHERE feature_type = 'user';

-- Search for specific feature
SELECT * FROM feature_metadata 
WHERE feature_name = 'popularity_score';

-- List all available features
SELECT feature_name, feature_type, description 
FROM feature_metadata
ORDER BY feature_type, feature_name;
```

---

## Feature Categories

### User Features (Demographics + Behavioral)

**Demographics:**
- `age`: User age
- `gender`: User gender
- `device`: Preferred device

**Behavioral:**
- `user_activity_count`: Interaction frequency
- `avg_rating_given`: Rating behavior
- `purchase_ratio`: Purchase propensity
- `preferred_category`: Category preference

**Encoded/Normalized:**
- `gender_encoded`, `device_encoded`: Categorical encoding
- `age_normalized`, `price_normalized`: Numerical normalization

### Item Features (Product Attributes + Popularity)

**Product Attributes:**
- `price`: Product price
- `brand`: Brand name
- `category`: Product category
- `rating`: Base rating
- `in_stock`: Availability

**Popularity Metrics:**
- `popularity_score`: Interaction count
- `avg_item_rating`: Average user rating
- `view_to_purchase_rate`: Conversion rate

**Derived:**
- `price_tier`: Price segmentation
- `category_encoded`, `brand_encoded`: Categorical encoding

---

## Indexes and Performance

### Recommended Indexes

```sql
-- User features
CREATE INDEX idx_user_activity ON user_features(user_activity_count DESC);
CREATE INDEX idx_user_category ON user_features(preferred_category);

-- Item features
CREATE INDEX idx_item_popularity ON item_features(popularity_score DESC);
CREATE INDEX idx_item_category ON item_features(category);
CREATE INDEX idx_item_brand ON item_features(brand);
CREATE INDEX idx_item_stock ON item_features(in_stock);
CREATE INDEX idx_item_rating ON item_features(avg_item_rating DESC);

-- Metadata
CREATE INDEX idx_meta_type ON feature_metadata(feature_type);
```

---

## Data Operations

### Insert/Update Operations

```sql
-- Insert user features (performed by Python code)
INSERT OR REPLACE INTO user_features 
(user_id, user_activity_count, avg_rating_given, purchase_ratio, 
 preferred_category, age, gender, device, gender_encoded, device_encoded, 
 age_normalized, updated_at)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP);

-- Insert item features
INSERT OR REPLACE INTO item_features 
(item_id, price, brand, category, rating, in_stock, popularity_score, 
 avg_item_rating, view_to_purchase_rate, price_tier, category_encoded, 
 brand_encoded, price_normalized, updated_at)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP);

-- Insert feature metadata
INSERT OR REPLACE INTO feature_metadata 
(feature_name, feature_type, description, data_type, source_table, 
 computation_logic, created_at, updated_at)
VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
```

### Retrieval Operations

```sql
-- Get all user features
SELECT * FROM user_features;

-- Get specific user features
SELECT * FROM user_features WHERE user_id IN (1, 2, 3);

-- Get all item features
SELECT * FROM item_features;

-- Get specific item features
SELECT * FROM item_features WHERE item_id IN (101, 102, 103);

-- Get feature metadata
SELECT * FROM feature_metadata WHERE feature_type = 'user';
```

---

## Data Freshness

### Update Strategy

Features are updated periodically when:
1. New transaction data is ingested
2. User profiles are updated
3. Product catalog changes
4. Scheduled feature engineering pipeline runs

The `updated_at` timestamp tracks the last feature update time.

```sql
-- Check feature freshness
SELECT 
    'user_features' as table_name,
    COUNT(*) as record_count,
    MAX(updated_at) as last_updated
FROM user_features

UNION ALL

SELECT 
    'item_features' as table_name,
    COUNT(*) as record_count,
    MAX(updated_at) as last_updated
FROM item_features;
```

---

## Integration with ML Pipeline

### Feature Retrieval for Training

```python
# Python code example
from src.features.feature_store import SimpleFeatureStore

# Initialize feature store
feature_store = SimpleFeatureStore('feature_store.db')

# Get features for training
user_features_df = feature_store.get_user_features()
item_features_df = feature_store.get_item_features()

# Get specific features for inference
user_features_df = feature_store.get_user_features(user_ids=[1, 2, 3])
item_features_df = feature_store.get_item_features(item_ids=[101, 102, 103])
```

### Feature Store API Methods

| Method | Description | SQL Equivalent |
|--------|-------------|----------------|
| `register_user_features()` | Store user features | `INSERT OR REPLACE INTO user_features` |
| `register_item_features()` | Store item features | `INSERT OR REPLACE INTO item_features` |
| `get_user_features()` | Retrieve user features | `SELECT * FROM user_features WHERE ...` |
| `get_item_features()` | Retrieve item features | `SELECT * FROM item_features WHERE ...` |
| `get_feature_metadata()` | Get feature documentation | `SELECT * FROM feature_metadata` |

---

## Data Quality Constraints

### Constraints and Validations

```sql
-- User features constraints
ALTER TABLE user_features ADD CONSTRAINT chk_activity_positive 
    CHECK (user_activity_count >= 0);

ALTER TABLE user_features ADD CONSTRAINT chk_rating_range 
    CHECK (avg_rating_given BETWEEN 0 AND 5);

ALTER TABLE user_features ADD CONSTRAINT chk_purchase_ratio 
    CHECK (purchase_ratio BETWEEN 0 AND 1);

-- Item features constraints
ALTER TABLE item_features ADD CONSTRAINT chk_price_positive 
    CHECK (price >= 0);

ALTER TABLE item_features ADD CONSTRAINT chk_popularity_positive 
    CHECK (popularity_score >= 0);

ALTER TABLE item_features ADD CONSTRAINT chk_conversion_rate 
    CHECK (view_to_purchase_rate BETWEEN 0 AND 1);
```

---

## Migration to Production

### Scaling Considerations

For production deployment, consider:

1. **PostgreSQL/MySQL Migration**
   ```sql
   -- PostgreSQL schema with partitioning
   CREATE TABLE user_features (
       user_id BIGINT PRIMARY KEY,
       -- ... other columns ...
       updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   ) PARTITION BY RANGE (updated_at);
   ```

2. **Feature Store Solutions**
   - **Feast**: Open-source feature store
   - **Tecton**: Managed feature platform
   - **AWS SageMaker Feature Store**
   - **Azure ML Feature Store**

3. **Caching Layer**
   - Redis for hot feature caching
   - Reduce database load for real-time serving

4. **Feature Versioning**
   - Track feature versions
   - Enable A/B testing
   - Support rollback

---

## References

- **Implementation**: `src/features/feature_store.py`
- **Feature Engineering**: `src/features/engineer_features.py`
- **Feature Logic Documentation**: `docs/FEATURE_LOGIC.md`
- **Storage Structure**: `docs/STORAGE_STRUCTURE.md`

---

**Last Updated**: January 27, 2026
