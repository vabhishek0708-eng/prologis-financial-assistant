# 🏭 Prologis Financial Assistant

An AI-powered financial assistant for Prologis Inc. — a leading industrial REIT. Built with a multi-cloud architecture using AWS and GCP, combining machine learning predictions, a PostgreSQL property database, SEC financial data, and a Gemini-powered AI chatbot.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit UI                          │
│  Dashboard | Explorer | Forecast | Risk | AI Chat        │
└────────────┬────────────────────────┬────────────────────┘
             │                        │
    ┌────────▼────────┐     ┌─────────▼──────────┐
    │   AWS (us-east-2)│     │   GCP (us-central1) │
    │                  │     │                     │
    │  S3 Bucket       │     │  Vertex AI          │
    │  ├─ regression/  │     │  └─ Gemini 2.5 Flash│
    │  └─ classif../   │     │                     │
    │                  │     └─────────────────────┘
    │  SageMaker       │
    │  ├─ Regression   │     ┌─────────────────────┐
    │  └─ Classif..    │     │  Local (PostgreSQL)  │
    └──────────────────┘     │  ├─ properties (22)  │
                             │  └─ financials        │
                             └─────────────────────┘
```

---

## 📋 Features

| Feature | Description |
|---|---|
| 📊 Executive Dashboard | KPI cards, revenue charts, occupancy distribution, portfolio map |
| 🏭 Property Explorer | Filterable table of 22 properties with detail drilldown |
| 📈 Revenue Forecast | ML regression model predicting property values (R²=0.805) |
| ⚠️ Risk Classification | ML classification model for investment risk (Accuracy=81.7%) |
| 🤖 AI Chat | Gemini 2.5 Flash chatbot with Prologis financial context |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| ML Models | scikit-learn 1.2.2 (Random Forest, Logistic Regression) |
| Database | PostgreSQL |
| Cloud — AWS | S3, SageMaker, IAM |
| Cloud — GCP | Vertex AI, Gemini 2.5 Flash |
| Language | Python 3.10 |

---

## 📁 Project Structure

```
financial_assistant/
├── app.py                          # Main Streamlit application
├── model_loader.py                 # Local model inference module
├── endpoint_config.json            # AWS endpoint configuration
├── requirements.txt                # Python dependencies
│
├── models/
│   ├── regression/
│   │   ├── train.py                # Regression training script
│   │   ├── model.pkl               # Trained regression model
│   │   ├── scaler.pkl              # Feature scaler
│   │   └── feature_names.pkl       # Feature names
│   └── classification/
│       ├── train.py                # Classification training script
│       ├── model.pkl               # Trained classification model
│       ├── scaler.pkl              # Feature scaler
│       └── feature_names.pkl       # Feature names
│
├── data/
│   ├── sec_mock.json               # SEC EDGAR mock filings
│   └── press_releases.json         # Prologis press releases
│
├── db/
│   └── seed_db.py                  # Database seeding script
│
├── chatbot/                        # Vertex AI chatbot module
│
├── sagemaker/                      # SageMaker deployment scripts
│
└── notebooks/
    ├── 01_eda_and_training.ipynb   # EDA + model training walkthrough
    └── 02_sagemaker_deployment.ipynb # Deployment documentation
```

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.10+
- PostgreSQL
- AWS CLI configured (`aws configure`)
- GCP CLI configured (`gcloud auth application-default login`)

### 1. Clone and install dependencies
```bash
git clone <repo-url>
cd financial_assistant
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 2. Set up the database
```bash
psql -U postgres -c "CREATE DATABASE realestate_db;"
python db/seed_db.py
```

### 3. Configure AWS
```bash
aws configure
# Enter: AWS Access Key, Secret Key, region=us-east-2
```

### 4. Configure GCP
```bash
gcloud auth application-default login
gcloud config set project project-f47a88c6-9a3a-4b51-903
gcloud services enable aiplatform.googleapis.com
```

### 5. Train models
```bash
python models/regression/train.py
python models/classification/train.py
```

### 6. Run the app
```bash
streamlit run app.py
```

---

## ☁️ Cloud Deployment

### AWS — Upload models to S3
```bash
python sagemaker/upload_to_s3.py
```

### AWS — Deploy SageMaker endpoints
```bash
python deploy_serverless.py
```

### GCP — Vertex AI chatbot
The chatbot uses `gcloud` application default credentials. No additional setup needed after `gcloud auth application-default login`.

---

## 🤖 ML Models

### Regression Model — Revenue Forecast
| Metric | Value |
|---|---|
| Algorithm | Random Forest Regressor |
| Dataset | California Housing (sklearn) |
| R² Score | 0.805 |
| RMSE | 0.5055 ($50,550) |
| Features | MedInc, HouseAge, AveRooms, AveBedrms, Population, AveOccup, Latitude, Longitude |

> **Note:** Trained on California Housing as a proxy dataset. In production, this would be retrained on actual Prologis portfolio data.

### Classification Model — Risk Assessment
| Metric | Value |
|---|---|
| Algorithm | Logistic Regression (class_weight=balanced) |
| Dataset | Bank Marketing (UCI) |
| Accuracy | 81.7% |
| Features | age, job, marital, education, balance, housing, loan, contact, duration, campaign, pdays, previous, poutcome |

> **Note:** Trained on Bank Marketing dataset as a proxy. Risk labels (Low/Medium/High) are mapped from binary subscription prediction probabilities.

---

## 🗄️ Database Schema

### properties
| Column | Type | Description |
|---|---|---|
| id | INTEGER | Primary key |
| property_name | VARCHAR | Property name |
| property_type | VARCHAR | Industrial/Warehouse/Logistics etc. |
| square_footage | FLOAT | Total square footage |
| occupancy_rate | FLOAT | Current occupancy % |
| annual_revenue | FLOAT | Annual revenue ($) |
| latitude | FLOAT | Geographic latitude |
| longitude | FLOAT | Geographic longitude |

### financials
| Column | Type | Description |
|---|---|---|
| id | INTEGER | Primary key |
| property_id | INTEGER | FK to properties |
| revenue | FLOAT | Revenue ($) |
| expenses | FLOAT | Operating expenses ($) |
| net_income | FLOAT | Net income ($) |

---

## ⚠️ Known Limitations

1. **SageMaker endpoints** — Serverless endpoints hit memory limits due to 144MB model size. Models run locally as fallback via `model_loader.py`
2. **Proxy datasets** — ML models use public datasets as substitutes for proprietary Prologis data
3. **22 properties** — Demo dataset; production would use full Prologis portfolio (~5,500 properties)
4. **Python 3.10** — GCP recommends 3.11+ for full Vertex AI SDK support

---

## 📚 References

- [Prologis Investor Relations](https://ir.prologis.com)
- [AWS SageMaker Documentation](https://docs.aws.amazon.com/sagemaker/)
- [Google Vertex AI Documentation](https://cloud.google.com/vertex-ai)
- [California Housing Dataset](https://scikit-learn.org/stable/datasets/real_world.html#california-housing-dataset)
- [Bank Marketing Dataset — UCI](https://archive.ics.uci.edu/dataset/222/bank+marketing)

---

## 👨‍💻 Author

**Vamsi** — MS Computer Science, DePaul University  
AI/Data Engineer | AWS | GCP | Python | scikit-learn
#   p r o l o g i s - f i n a n c i a l - a s s i s t a n t  
 #   p r o l o g i s - f i n a n c i a l - a s s i s t a n t  
 #   p r o l o g i s - f i n a n c i a l - a s s i s t a n t  
 