# Broadband Fraud Batch API

A FastAPI service for scoring stored broadband transaction records in MongoDB and flagging suspicious activity with a combination of rules and an XGBoost model.

This project is designed for batch processing. It reads transactions from MongoDB, scores them, and returns a fraud decision for each record together with a summary.

## What this project does

- Loads transaction records from MongoDB
- Applies rule-based scoring and machine-learning scoring
- Combines both scores into a final fraud decision
- Exposes a batch prediction API through FastAPI
- Ships with a synthetic training dataset so you can run it locally end to end

## Project layout

```text
fraud_api/
├── app/
│   ├── main.py                  # FastAPI app and API routes
│   ├── config/rules.yaml        # Rule thresholds and scoring settings
│   ├── core/logging.py          # Logging setup
│   ├── db/mongo.py              # MongoDB connection and repository helpers
│   ├── models/
│   │   ├── schemas.py           # Pydantic request/response models
│   │   └── fraud_model.json     # Trained XGBoost model output
│   ├── services/                # Feature engineering, rules, ML, scoring logic
│   └── static/                  # Simple web dashboard assets
├── scripts/
│   └── import_csv_to_mongodb.py # Helper to load CSV data into MongoDB
├── training/
│   ├── train_model.py           # Offline model training script
│   ├── generate_synthetic_dataset.py
│   └── synthetic_broadband_fraud_data.csv
├── tests/                       # Automated tests
└── requirements.txt
```

## Requirements

- Windows, macOS, or Linux
- Python 3.11 or newer recommended
- MongoDB Community Server running locally, or a MongoDB Atlas cluster
- Internet access to install Python dependencies

## Install Python

Check your Python version first:

```powershell
python --version
```

If Python is not installed, install it from https://www.python.org/downloads/ and make sure it is added to PATH.

## Create a virtual environment

From the project root folder `fraud_api`, run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run this once in the current terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate the environment again.

## Install dependencies

With the virtual environment activated:

```powershell
pip install -r requirements.txt
```

## Configure MongoDB

By default the app connects to:

- `mongodb://localhost:27017`
- database: `fraud_api`
- collection: `transactions`

If you want to override these values, create a `.env` file in the project root:

```env
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=fraud_api
MONGODB_COLLECTION=transactions
```

If you are using MongoDB Atlas, replace `MONGODB_URI` with your Atlas connection string.

## Start MongoDB

### Local MongoDB

Make sure the MongoDB service is running on your machine before starting the API.

### MongoDB Atlas

If you use Atlas, update `.env` with your cluster URI and make sure your IP address is allowed in the Atlas network access settings.

## Train the model

The API expects a trained model file at `app/models/fraud_model.json`.

Generate it from the training script:

```powershell
python training\train_model.py
```

What this does:

- loads or generates synthetic broadband fraud data
- trains an XGBoost classifier
- saves the model to `app/models/fraud_model.json`

Important:

- The included training script uses synthetic data so you can run the project immediately.
- For real-world use, replace the synthetic data generation in `training/train_model.py` with your own labeled historical data.

## Load transaction data into MongoDB

You can import the included synthetic CSV into MongoDB with the helper script:

```powershell
python scripts\import_csv_to_mongodb.py
```

The script reads:

- `training/synthetic_broadband_fraud_data.csv`

and inserts the rows into the configured MongoDB collection.

If you already have your own data, insert documents using the same field structure as the API expects.

### Expected transaction fields

Each MongoDB document should contain these fields:

- `customer_id`
- `usage_mb`
- `avg_usage_mb`
- `device_age_days`
- `num_devices_30d`
- `failed_payments_7d`
- `account_age_days`
- `login_hour`
- `distance_from_usual_km`
- `mac_address`

Example document:

```json
{
  "customer_id": "CUST-10293",
  "usage_mb": 15230.5,
  "avg_usage_mb": 2100.0,
  "device_age_days": 0,
  "num_devices_30d": 4,
  "failed_payments_7d": 3,
  "account_age_days": 5,
  "login_hour": 3,
  "distance_from_usual_km": 120.0,
  "mac_address": "AA:BB:CC:DD:EE:FF"
}
```

## Run the API

From the project root:

```powershell
uvicorn app.main:app --reload
```

Then open:

- API docs: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health
- Web UI: http://127.0.0.1:8000/

## Predict in batch

The API provides a batch scoring endpoint.

### Request

```http
POST /predict
Content-Type: application/json
```

Example body:

```json
{
  "collection_name": "transactions",
  "customer_id": null,
  "skip": 0,
  "limit": 100
}
```

### Example cURL

```powershell
curl -X POST http://127.0.0.1:8000/predict `
  -H "Content-Type: application/json" `
  -d '{"collection_name":"transactions","customer_id":null,"skip":0,"limit":100}'
```

### Response

The response includes:

- `collection_name`
- `matched_count`
- `predictions`
- `summary`

Each prediction contains:

- `document_id`
- `customer_id`
- `is_fraud`
- `rule_score`
- `ml_score`
- `final_score`
- `decision`
- `triggered_rules`
- `model_version`

## Running tests

Run the automated test suite with:

```powershell
python -m pytest
```

## Troubleshooting

### `FileNotFoundError` for the CSV file

Run the importer from the project root, or use:

```powershell
python scripts\import_csv_to_mongodb.py
```

The script uses a path relative to its own location, so it does not depend on the current working directory.

### `pymongo is not installed`

Install dependencies again with:

```powershell
pip install -r requirements.txt
```

### MongoDB connection errors

Check that:

- MongoDB is running
- the URI in `.env` is correct
- the database and collection names match your data

### API starts but `/predict` fails

Make sure you have:

- trained the model with `python training\train_model.py`
- loaded documents into MongoDB
- documents that contain all required fields

## How the scoring works

The service combines:

- rule-based fraud signals from `app/config/rules.yaml`
- machine-learning probability from the XGBoost model
- a final ensemble decision generated in the service layer

This gives you both a decision and traceability for why a record was flagged.

## Notes for development

- Edit `app/config/rules.yaml` to adjust thresholds
- Restart the app after changing rules or the model
- Use the synthetic data and training pipeline as a local demo setup before plugging in real data

## License

Add a license file .