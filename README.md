# Broadband Fraud Batch API

A FastAPI service for scoring stored broadband transaction records in MongoDB and flagging suspicious activity with a combination of rules and an XGBoost model.

This project is designed for batch processing with **automatic background scoring**. You add transaction data to MongoDB (however you like), and a background worker automatically scores it and stores the results — no manual API call required. You can then pull fraud statistics, visualizations, and a downloadable PDF report for any time period.

## What this project does

- Loads transaction records from MongoDB
- Applies rule-based scoring and machine-learning scoring
- Combines both scores into a final fraud decision
- **Automatically scores new transactions in the background** as soon as they're added to MongoDB, no manual trigger needed
- Stores every scored result with a timestamp, so it can be queried by time period later
- Exposes a batch prediction API through FastAPI (for on-demand/manual scoring)
- Exposes a time-range statistics API with a MongoDB aggregation pipeline (fraud/normal counts, percentages, per-rule breakdown)
- Generates a downloadable PDF report for any selected time period
- Ships with a synthetic training dataset so you can run it locally end to end

## Project layout

```text
fraud_api/
├── app/
│   ├── main.py                     # FastAPI app, API routes, startup/shutdown hooks
│   ├── config/rules.yaml           # Rule thresholds and scoring settings
│   ├── core/logging.py             # Logging setup
│   ├── db/mongo.py                 # MongoDB connections, repositories, and the
│   │                                #   time-range aggregation pipeline
│   ├── models/
│   │   ├── schemas.py              # Pydantic request/response models
│   │   └── fraud_model.json        # Trained XGBoost model output
│   ├── services/
│   │   ├── features.py             # Feature engineering (shared with training)
│   │   ├── rules.py                # Rule-based scoring (reads rules.yaml)
│   │   ├── ml.py                   # XGBoost model loading and scoring
│   │   ├── ensemble.py             # Combines rule + ML scores into a decision
│   │   ├── scoring.py              # Orchestrates rules + ML + ensemble
│   │   ├── batch.py                # Batch scoring helpers, storage formatting
│   │   ├── auto_scorer.py          # Background poller: auto-scores new
│   │   │                            #   transactions without a manual /predict call
│   │   └── report.py               # PDF report generation (reportlab)
│   └── static/                     # Web dashboard (index.html, dashboard.css)
├── scripts/
│   ├── import_csv_to_mongodb.py    # Loads the synthetic CSV into MongoDB
│   ├── add_sample_transactions.py  # Inserts a small hand-crafted test dataset
│   ├── check_recent_predictions.py # Diagnostic: inspect recent scored predictions
│   ├── VerifytheRecords.py         # Diagnostic: count/inspect raw transactions
│   ├── test_connection.py          # Diagnostic: verify MongoDB connectivity
│   └── test_mongo_repository.py
├── training/
│   ├── train_model.py              # Offline model training script
│   ├── generate_synthetic_dataset.py
│   └── synthetic_broadband_fraud_data.csv
├── tests/                          # Automated tests
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

This includes `fastapi`, `uvicorn`, `pymongo`, `xgboost`, `pyyaml`, `pandas`, `scikit-learn`, and `reportlab` (used to generate PDF reports).

## Configure MongoDB

By default the app connects to:

- `mongodb://localhost:27017`
- database: `fraud_api`
- raw transactions collection: `transactions`
- scored predictions collection: `fraud_predictions` (created automatically)

If you want to override these values, create a `.env` file in the project root:

```env
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=fraud_api
MONGODB_COLLECTION=transactions
MONGODB_PREDICTIONS_COLLECTION=fraud_predictions
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

## Run the API

From the project root:

```powershell
uvicorn app.main:app --reload
```

On startup, the app will:

1. Load the XGBoost model
2. Ensure MongoDB indexes exist on `fraud_predictions` (`created_at`, `customer_id`, `document_id`)
3. **Start the background auto-scoring poller** — this runs every 5 seconds and automatically scores any transaction in `transactions` that hasn't been scored yet, saving the result into `fraud_predictions` with a timestamp

Then open:

- API docs: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health
- Web dashboard: http://127.0.0.1:8000/

## Adding transaction data (two supported ways)

### Option 1 — Import the included synthetic dataset

```powershell
python scripts\import_csv_to_mongodb.py
```

This reads `training/synthetic_broadband_fraud_data.csv` and inserts the rows into the configured MongoDB collection.

### Option 2 — Insert a small hand-crafted test set

```powershell
python scripts\add_sample_transactions.py
```

This inserts a mix of obviously-fraudulent, obviously-legitimate, and borderline records, useful for quickly testing the dashboard end to end.

### Your own data

If you have your own data, insert documents into the `transactions` collection using the same field structure the API expects (see below). **You don't need to call any endpoint afterward** — the background auto-scorer picks up new documents automatically within a few seconds.

### Expected transaction fields

Each MongoDB document in `transactions` should contain these fields:

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

## How automatic scoring works

The workflow is intentionally reduced to two steps for day-to-day use:

1. **Add data** to the `transactions` collection (via a script, MongoDB Compass, `mongosh`, or your own ingestion process).
2. **View results** on the dashboard or via the API for whatever time period you care about.

Behind the scenes, `app/services/auto_scorer.py` runs a background thread that:

- Every 5 seconds, checks `transactions` for documents whose `_id` doesn't yet have a matching `document_id` in `fraud_predictions`
- Scores any new documents using the same rules + ML + ensemble logic as `/predict`
- Saves the results into `fraud_predictions` with a `created_at` timestamp (UTC)

This means each transaction is scored automatically exactly once — no duplicate work, no manual trigger.

## Manual batch scoring (still available)

`POST /predict` remains available for on-demand, manual scoring of everything currently in `transactions` (useful for forcing a re-score, or scoring a specific customer/subset).

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

### Example cURL (PowerShell)

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

Note: calling `/predict` re-scores everything matching the query each time, which can create duplicate entries in `fraud_predictions` for the same customer if run repeatedly. This is fine for occasional manual/ad-hoc scoring, but the recommended day-to-day workflow is to just add data and let the background auto-scorer handle it once per record.

## Fraud statistics by time period

### `POST /stats/by-time`

Returns fraud statistics for a given time window, computed via a MongoDB aggregation pipeline against `fraud_predictions`.

Request body:

```json
{
  "start_time": "2026-07-01T00:00:00Z",
  "end_time": "2026-07-08T23:59:59Z"
}
```

Response includes:

- `total_records`, `fraud_count`, `normal_count`
- `fraud_percentage`, `normal_percentage`
- `records`: individual scored records in the range (`customer_id`, `is_fraud`, `decision`, scores, `triggered_rules`, `created_at`)
- `rule_breakdown`: for each triggered rule, how many times it fired in this period and what percentage of those firings were confirmed fraud

**Timezone note:** timestamps are stored in UTC. The dashboard converts your local time picker input into a proper UTC ISO string before querying, so results are correct regardless of your local timezone.

### `POST /stats/by-time/report`

Same request body as above, but returns a downloadable PDF instead of JSON — includes a summary table, a triggered-rules-vs-fraud-percentage chart, and a detailed records table (with a color-coded Fraud Status column: red for fraud, green for normal).

## Web dashboard

Open http://127.0.0.1:8000/ to use the dashboard. It provides:

- A time-range picker ("Fraud Statistics by Time Period")
- Summary boxes: total records, fraud %, normal %
- A bar visualization of triggered rules vs. their fraud percentage
- A detailed records table with a **Fraud Status** column (red = FRAUD, green = NOT FRAUD) and the Decision, Final Score, Triggered Rules, and Scored At columns
- A **Download PDF Report** button that generates the same report shown above as a file

## Running tests

Run the automated test suite with:

```powershell
python -m pytest
```

## Troubleshooting

### Dashboard shows 0 records even though I added data

The auto-scorer runs every 5 seconds — wait a few seconds after adding data before checking. You can confirm it worked by checking the server logs for:

```
Auto-scorer found N new transaction(s) to score
Auto-scorer saved N new predictions to fraud_predictions
```

or by running:

```powershell
python scripts\check_recent_predictions.py
```

### `FileNotFoundError` for the CSV file

Run the importer from the project root, or use:

```powershell
python scripts\import_csv_to_mongodb.py
```

The script uses a path relative to its own location, so it does not depend on the current working directory.

### `pymongo is not installed` / `reportlab is not installed`

Install dependencies again with:

```powershell
pip install -r requirements.txt
```

### MongoDB connection errors

Check that:

- MongoDB is running
- the URI in `.env` is correct
- the database and collection names match your data

### API starts but `/predict` or the dashboard fails

Make sure you have:

- trained the model with `python training\train_model.py`
- loaded documents into MongoDB
- documents that contain all required fields

## How the scoring works

The service combines:

- rule-based fraud signals from `app/config/rules.yaml`
- machine-learning probability from the XGBoost model
- a final ensemble decision generated in the service layer

This gives you both a decision and traceability (via `triggered_rules`) for why a record was flagged.

## Notes for development

- Edit `app/config/rules.yaml` to adjust thresholds
- Restart the app after changing rules or the model
- The auto-scorer poll interval is configurable via `POLL_INTERVAL_SECONDS` at the top of `app/services/auto_scorer.py`
- Use the synthetic data and training pipeline as a local demo setup before plugging in real data

## License

Add a license file.