# Scripts Directory

This directory contains standalone test scripts and utilities.

## Test ForexRateAPI Provider

Test the ForexRateAPI provider functionality:

### Method 1: Django Management Command (Recommended)
```bash
cd backend
python manage.py test_forexrateapi
```

### Method 2: Django Shell
```bash
cd backend
python manage.py shell < scripts/test_forexrateapi.py
```

### Method 3: Direct Execution
```bash
cd backend
python scripts/test_forexrateapi.py
```

### Method 4: Import in Shell
```bash
python manage.py shell
```
Then:
```python
from scripts.test_forexrateapi import run_all_tests
run_all_tests()
```

## What It Tests

1. **Single Price Fetch** - Tests `get_latest_price()` for a single pair
2. **Batch Price Fetch** - Tests `get_latest_prices_batch()` for multiple pairs
3. **Rate Inversion** - Verifies inverse rate calculation (EUR/USD ↔ USD/EUR)
4. **Candle Data** - Tests `get_candles()` for hourly data
5. **API Optimization** - Verifies batch requests reduce API calls

## Requirements

- `FOREXRATEAPI_API_KEY` must be set in `.env` file
- Active internet connection
- Valid API key with sufficient quota
