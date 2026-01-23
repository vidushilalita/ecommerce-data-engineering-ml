# Feature Logic Documentation

## Overview

This document describes all features engineered for the RecoMart recommendation system, including their formulas, business rationale, and example calculations.

---

## User Features

### 1. user_activity_count
**Description**: Total number of interactions (views, carts, purchases) by the user

**Formula**:
```
user_activity_count = COUNT(transactions WHERE user_id = X)
```

**Business Rationale**: Active users provide more reliable signals for recommendations. High activity indicates engagement.

**Example**:
- User 101 has 15 interactions → user_activity_count = 15

---

### 2. avg_rating_given
**Description**: Average rating given by the user across all interactions

**Formula**:
```
avg_rating_given = AVG(rating WHERE user_id = X)
```

**Business Rationale**: Indicates user's general satisfaction level. High-rating users may be more enthusiastic.

**Example**:
- User 101 ratings: [4, 5, 3, 4, 5] → avg_rating_given = 4.2

---

### 3. purchase_ratio
**Description**: Proportion of interactions that resulted in purchases

**Formula**:
```
purchase_ratio = COUNT(purchases) / COUNT(total_interactions)
```

**Business Rationale**: Indicates buying intent. High purchase ratio suggests decisive, high-intent users.

**Example**:
- User 101: 3 purchases out of 15 interactions → purchase_ratio = 0.20 (20%)

---

### 4. preferred_category
**Description**: Most frequently interacted product category

**Formula**:
```
preferred_category = MODE(category WHERE user_id = X)
```

**Business Rationale**: Enables content-based filtering. Users tend to stay within preferred categories.

**Example**:
- User 101 interactions: Electronics(8), Sports(4), Fashion(3) → preferred_category = "Electronics"

---

### 5. device_type_encoded / gender_encoded / age_normalized
**Description**: Encoded demographic features

**Encoding**:
- **gender**: M=0, F=1 (Label Encoding)
- **device**: Desktop=0, Mobile=1, Tablet=2 (Label Encoding)
- **age**: Normalized to [0, 1] range using Min-Max scaling

**Business Rationale**: Demographic signals for cold-start and content-based filtering.

---

## Item Features

### 1. popularity_score
**Description**: Number of interactions the item received

**Formula**:
```
popularity_score = COUNT(interactions WHERE item_id = Y)
```

**Business Rationale**: Popular items are safer recommendations. Avoids cold-start items initially.

**Example**:
- Item 501: 120 interactions → popularity_score = 120

---

### 2. avg_item_rating
**Description**: Average rating received by the item

**Formula**:
```
avg_item_rating = AVG(rating WHERE item_id = Y)
```

**Business Rationale**: Quality signal. High-rated items should be recommended more.

**Example**:
- Item 501 ratings: [5, 4, 5, 4, 5] → avg_item_rating = 4.6

---

### 3. price_tier
**Description**: Binned price category (low, medium, high)

**Formula**:
```
price_tier = QCUT(price, q=3, labels=['low', 'medium', 'high'])
```

**Tiers**:
- Low: 0-33rd percentile
- Medium: 33rd-67th percentile  
- High: 67th-100th percentile

**Business Rationale**: Users have price preferences. Match recommendations to user's price tier.

**Example**:
- Item with $50 price in $10-$200 range → price_tier = "low"

---

### 4. view_to_purchase_rate
**Description**: Conversion rate from views to purchases

**Formula**:
```
view_to_purchase_rate = COUNT(purchases) / COUNT(views)
```

**Business Rationale**: High-converting items are effective recommendations.

**Example**:
- Item 501: 10 purchases, 50 views → view_to_purchase_rate = 0.20 (20%)

---

### 5. category_encoded / brand_encoded
**Description**: Encoded categorical features

**Encoding**: Label Encoding (each category gets unique integer)

**Business Rationale**: Enable machine learning algorithms to use categorical data.

---

## Interaction Features

### 1. implicit_score
**Description**: Weighted score based on interaction type

**Formula**:
```
implicit_score = {
    'view': 1,
    'add_to_cart': 2,
    'purchase': 3
}
```

**Business Rationale**: Different actions signal different intent levels. Purchases > Carts > Views.

**Example**:
- Purchase action → implicit_score = 3

---

### 2. recency_weight
**Description**: Time-decay factor for interaction recency

**Formula**:
```
days_since = (current_date - interaction_date).days
recency_weight = exp(-days_since / 30.0)
```

**Decay**: Exponential with 30-day half-life

**Business Rationale**: Recent interactions are more relevant to current preferences.

**Example**:
- Interaction 5 days ago → recency_weight = exp(-5/30) = 0.846
- Interaction 60 days ago → recency_weight = exp(-60/30) = 0.135

---

### 3. user_item_affinity
**Description**: Combined affinity score

**Formula**:
```
rating_normalized = (rating - 1) / 4.0
user_item_affinity = (implicit_score/3 * 0.3) + 
                     (rating_normalized * 0.5) + 
                     (recency_weight * 0.2)
```

**Weights**:
- Implicit signal: 30%
- Explicit rating: 50%
- Recency: 20%

**Business Rationale**: Combines multiple signals into unified affinity metric for hybrid recommendations.

**Example**:
- View (implicit=1), rating=4, recency=0.9
- user_item_affinity = (1/3 * 0.3) + (0.75 * 0.5) + (0.9 * 0.2) = 0.655

---

## Feature Summary Table

| Feature | Type | Range | Purpose |
|---------|------|-------|---------|
| user_activity_count | Numeric | [0, ∞) | User engagement |
| avg_rating_given | Numeric | [1.0, 5.0] | User satisfaction |
| purchase_ratio | Numeric | [0.0, 1.0] | Buying intent |
| preferred_category | Categorical | - | Content filtering |
| popularity_score | Numeric | [0, ∞) | Item popularity |
| avg_item_rating | Numeric | [1.0, 5.0] | Item quality |
| price_tier | Categorical | {low, med, high} | Price matching |
| view_to_purchase_rate | Numeric | [0.0, 1.0] | Item conversion |
| implicit_score | Numeric | [1, 2, 3] | Interaction intent |
| recency_weight | Numeric | [0.0, 1.0] | Temporal relevance |
| user_item_affinity | Numeric | [0.0, 1.0] | Combined score |

---

## Feature Usage

### Collaborative Filtering
- Uses: user-item interaction matrix with user_item_affinity as rating

### Content-Based Filtering
- User side: preferred_category, device_type, age
- Item side: category, brand, price_tier

### Hybrid Model
- Combines CF predictions with content-based features
- Weights based on user activity level (cold-start handling)
