# Task 4: Data Profiling and Validation

## Overview

This document describes the data validation framework implemented for the RecoMart recommendation system, ensuring data quality and completeness across all datasets.

---

## 1. Validation Framework

### 1.1 Technology Stack
- **Primary Tool**: Custom pandas-based validation (Great Expectations alternative)
- **Language**: Python 3.12
- **Output**: JSON validation reports

### 1.2 Validation Module
**File**: `src/validation/validate_data.py`

```python
class DataValidator:
    """Data validation using pandas-based checks"""
    
    def run_validation_suite(self) -> Dict[str, Any]:
        """Run complete validation on all datasets"""
```

---

## 2. Validation Checks by Dataset

### 2.1 User Data Validation

| Check | Type | Threshold | Description |
|-------|------|-----------|-------------|
| `user_id_unique` | Uniqueness | 100% | No duplicate user IDs |
| `age_in_range_18_65` | Range | ≥95% | Age between 18-65 years |
| `gender_valid` | Categorical | ≥95% | Values: M, F, Male, Female |
| `device_valid` | Categorical | ≥95% | Values: Mobile, Desktop, Tablet |
| `no_null_user_ids` | Completeness | 100% | No null values in user_id |

**Implementation**:
```python
def validate_users(self, df: pd.DataFrame) -> Dict[str, Any]:
    """Validate user data"""
    checks = []
    
    # Check 1: user_id uniqueness
    duplicate_ids = df.duplicated(subset=['user_id']).sum()
    checks.append({
        'check': 'user_id_unique',
        'passed': bool(duplicate_ids == 0),
        'details': f"{duplicate_ids} duplicates found"
    })
    
    # Check 2: age range (18-65)
    if 'age' in df.columns:
        age_in_range = df['age'].between(18, 65).sum()
        age_pass_rate = age_in_range / len(df)
        checks.append({
            'check': 'age_in_range_18_65',
            'passed': bool(age_pass_rate >= 0.95),
            'details': f"{age_pass_rate:.1%} within range"
        })
```

### 2.2 Product Data Validation

| Check | Type | Threshold | Description |
|-------|------|-----------|-------------|
| `item_id_unique` | Uniqueness | 100% | No duplicate item IDs |
| `price_positive` | Range | ≥99% | Price > 0 |
| `rating_in_range_1_5` | Range | ≥99% | Rating between 1.0-5.0 |
| `category_not_null` | Completeness | ≥99% | Category field populated |
| `brand_not_null` | Completeness | ≥95% | Brand field populated |

**Implementation**:
```python
def validate_products(self, df: pd.DataFrame) -> Dict[str, Any]:
    """Validate product data"""
    checks = []
    
    # Check: price > 0
    if 'price' in df.columns:
        valid_prices = (df['price'] > 0).sum()
        price_pass_rate = valid_prices / len(df)
        checks.append({
            'check': 'price_positive',
            'passed': bool(price_pass_rate >= 0.99),
            'details': f"{price_pass_rate:.1%} positive prices"
        })
```

### 2.3 Transaction Data Validation

| Check | Type | Threshold | Description |
|-------|------|-----------|-------------|
| `user_id_not_null` | Completeness | 100% | All transactions have user_id |
| `item_id_not_null` | Completeness | 100% | All transactions have item_id |
| `view_mode_valid` | Categorical | ≥99% | Values: view, add_to_cart, purchase |
| `rating_in_range_1_5` | Range | ≥99% | Rating between 1-5 |
| `timestamp_parseable` | Format | ≥99% | Valid datetime format |
| `user_id_exists` | Foreign Key | ≥95% | References valid user |
| `item_id_exists` | Foreign Key | ≥95% | References valid product |

**Implementation**:
```python
def validate_transactions(self, df: pd.DataFrame, 
                          valid_user_ids: set, 
                          valid_item_ids: set) -> Dict[str, Any]:
    """Validate transaction data with foreign key checks"""
    
    # Foreign key validation
    if valid_user_ids:
        valid_users = df['user_id'].isin(valid_user_ids).sum()
        user_fk_rate = valid_users / len(df)
        checks.append({
            'check': 'user_id_exists',
            'passed': bool(user_fk_rate >= 0.95),
            'details': f"{user_fk_rate:.1%} valid user references"
        })
```

---

## 3. Quality Score Calculation

### 3.1 Dataset Quality Score
```python
# Quality score = Passed checks / Total checks
results['quality_score'] = sum(1 for c in checks if c['passed']) / len(checks)
```

### 3.2 Overall Pipeline Quality Score
```python
def _calculate_overall_quality(self, all_results: Dict) -> Dict:
    """Calculate overall data quality metrics"""
    
    total_checks = sum(len(r['validations']) for r in all_results.values())
    passed_checks = sum(
        sum(1 for c in r['validations'] if c['passed']) 
        for r in all_results.values()
    )
    
    return {
        'total_datasets': len(all_results),
        'total_checks': total_checks,
        'passed_checks': passed_checks,
        'failed_checks': total_checks - passed_checks,
        'quality_score': passed_checks / total_checks if total_checks > 0 else 0
    }
```

---

## 4. Validation Report

### 4.1 Report Structure
```json
{
  "users": {
    "dataset": "users",
    "record_count": 927,
    "validations": [
      {
        "check": "user_id_unique",
        "passed": false,
        "details": "10 duplicates found"
      },
      {
        "check": "age_in_range_18_65",
        "passed": true,
        "details": "97.0% within range"
      }
    ],
    "quality_score": 0.8
  },
  "products": {
    "dataset": "products",
    "record_count": 101,
    "validations": [...],
    "quality_score": 1.0
  },
  "transactions": {
    "dataset": "transactions",
    "record_count": 3001,
    "validations": [...],
    "quality_score": 0.857
  },
  "overall": {
    "total_datasets": 3,
    "total_checks": 17,
    "passed_checks": 15,
    "failed_checks": 2,
    "quality_score": 0.882
  }
}
```

### 4.2 Report Location
Reports are saved to: `reports/validation_results_{timestamp}.json`

---

## 5. Sample Validation Results

### 5.1 Users Dataset (Quality: 80%)

| Check | Status | Details |
|-------|--------|---------|
| user_id_unique | ❌ Failed | 10 duplicates found |
| age_in_range_18_65 | ✅ Passed | 97.0% within range |
| gender_valid | ✅ Passed | 98.4% valid values |
| device_valid | ✅ Passed | 96.9% valid values |
| no_null_user_ids | ✅ Passed | 0 nulls in user_id |

### 5.2 Products Dataset (Quality: 100%)

| Check | Status | Details |
|-------|--------|---------|
| item_id_unique | ✅ Passed | 0 duplicates found |
| price_positive | ✅ Passed | 100.0% positive prices |
| rating_in_range_1_5 | ✅ Passed | 100.0% valid ratings |
| category_not_null | ✅ Passed | 100.0% populated |
| brand_not_null | ✅ Passed | 100.0% populated |

### 5.3 Transactions Dataset (Quality: 85.7%)

| Check | Status | Details |
|-------|--------|---------|
| user_id_not_null | ✅ Passed | 0 nulls |
| item_id_not_null | ✅ Passed | 0 nulls |
| view_mode_valid | ✅ Passed | 100.0% valid modes |
| rating_in_range_1_5 | ✅ Passed | 100.0% valid ratings |
| timestamp_parseable | ✅ Passed | 100.0% parseable |
| user_id_exists | ❌ Failed | 94.2% valid references |
| item_id_exists | ✅ Passed | 100.0% valid references |

### 5.4 Overall Quality Score: 88.2%

---

## 6. Running Validation

### 6.1 Standalone Execution
```bash
python -m src.validation.validate_data
```

### 6.2 Programmatic Usage
```python
from src.validation.validate_data import DataValidator

validator = DataValidator()
results = validator.run_validation_suite()
validator.save_validation_results(results)

print(f"Overall Quality: {results['overall']['quality_score']:.1%}")
```

### 6.3 Pipeline Integration
Validation runs automatically as part of the orchestrated pipeline:
```python
@task(name="Validate Data", retries=1)
def validate_data():
    """Run data validation"""
    from src.validation.validate_data import DataValidator
    validator = DataValidator()
    results = validator.run_validation_suite()
    
    quality_score = results['overall']['quality_score']
    if quality_score < 0.95:
        raise ValueError(f"Data quality score {quality_score:.1%} below threshold 95%")
    
    return results
```

---

## 7. Data Quality Issues Detected

### 7.1 Known Issues in Source Data
Based on validation results:

| Dataset | Issue | Count | Impact |
|---------|-------|-------|--------|
| Users | Duplicate user_ids | 10 | Requires deduplication |
| Users | Age out of range | 28 | 3% records with invalid age |
| Users | Invalid gender | 15 | 1.6% records |
| Users | Invalid device | 29 | 3.1% records |
| Transactions | Invalid user_id FK | 174 | 5.8% orphan records |

### 7.2 Resolution Strategy
These issues are handled in the Data Preparation stage (Task 5):
- Duplicates: Keep first occurrence
- Invalid ranges: Impute with median/mode
- Foreign key violations: Filter out orphan records

---

## 8. Quality Thresholds

### 8.1 Pipeline Gate Thresholds

| Metric | Threshold | Action if Failed |
|--------|-----------|------------------|
| Overall Quality Score | ≥ 95% | Block pipeline |
| Individual Dataset Score | ≥ 80% | Warning |
| Critical Field Completeness | 100% | Block pipeline |
| Foreign Key Validity | ≥ 95% | Warning |

### 8.2 Alerting
```python
if quality_score < 0.95:
    logger.warning(f"Data quality below threshold: {quality_score:.1%}")
    raise ValueError(f"Data quality score {quality_score:.1%} below threshold 95%")
```

---

## 9. Validation Output Files

### 9.1 Report Files
```
reports/
├── validation_results_20260123_161640.json
├── validation_results_20260123_162028.json
└── figures/
    └── (EDA visualizations)
```

### 9.2 Sample Report Content
```json
{
  "users": {
    "dataset": "users",
    "record_count": 927,
    "validations": [
      {"check": "user_id_unique", "passed": false, "details": "10 duplicates found"},
      {"check": "age_in_range_18_65", "passed": true, "details": "97.0% within range"},
      {"check": "gender_valid", "passed": true, "details": "98.4% valid values"},
      {"check": "device_valid", "passed": true, "details": "96.9% valid values"},
      {"check": "no_null_user_ids", "passed": true, "details": "0 nulls in user_id"}
    ],
    "quality_score": 0.8
  }
}
```

---

## Deliverables Checklist

| Deliverable | Status | Location |
|-------------|--------|----------|
| Python code for automated validation | ✅ | `src/validation/validate_data.py` |
| Data Quality Report (JSON) | ✅ | `reports/validation_results_*.json` |
| Missing value checks | ✅ | Null count validation |
| Duplicate entry checks | ✅ | Uniqueness validation |
| Schema mismatch checks | ✅ | Column presence validation |
| Range and format checks | ✅ | Age, rating, price ranges |
