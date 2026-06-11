import os
import boto3
import json
import warnings
warnings.filterwarnings("ignore")


AWS_REGION   = os.getenv("AWS_DEFAULT_REGION", "us-east-2")
AWS_KEY      = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET   = os.getenv("AWS_SECRET_ACCESS_KEY")
S3_BUCKET    = "prologis-financial-assistant-362612348837"
REG_ENDPOINT = "prologis-regression-endpoint"
CLF_ENDPOINT = "prologis-classification-endpoint"

def _sm():
    return boto3.client("sagemaker-runtime",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_KEY,
        aws_secret_access_key=AWS_SECRET)

def _s3():
    return boto3.client("s3",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_KEY,
        aws_secret_access_key=AWS_SECRET)

def _invoke(endpoint_name: str, features: list) -> dict:
    try:
        sm = boto3.client("sagemaker-runtime", region_name=AWS_REGION)
        resp = sm.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType="application/json",
            Body=json.dumps({"features": features}),
        )
        return json.loads(resp["Body"].read())
    except Exception as e:
        return {"error": str(e)}


def predict_revenue(features: list) -> dict:
    result = _invoke(REG_ENDPOINT, features)
    if "error" in result:
        return result
    pred = result.get("prediction", [0])
    if isinstance(pred, list):
        pred = pred[0]
    return {"prediction": float(pred) * 100000}


def predict_risk(features: list) -> dict:
    result = _invoke(CLF_ENDPOINT, features)
    if "error" in result:
        return result
    proba   = result.get("probabilities", None)
    prob_yes = result.get("probability_yes", None)
    if prob_yes is None and proba is not None:
        prob_yes = float(proba[0][1]) if isinstance(proba[0], list) else float(proba[1])
    elif prob_yes is None:
        prob_yes = 0.5
    if prob_yes > 0.7:
        risk_label = "Low"
    elif prob_yes > 0.45:
        risk_label = "Medium"
    else:
        risk_label = "High"
    return {
        "prediction":    [risk_label],
        "probabilities": [[1 - prob_yes, prob_yes]],
        "prob_yes":      prob_yes,
    }


def load_sec_data() -> dict:
    """Load SEC mock filing data from S3."""
    try:
        s3  = boto3.client("s3", region_name=AWS_REGION)
        obj = s3.get_object(Bucket=S3_BUCKET, Key="data/sec_mock.json")
        return json.loads(obj["Body"].read())
    except Exception as e:
        return {"error": str(e)}


def load_press_releases() -> list:
    """Load press releases from S3."""
    try:
        s3  = boto3.client("s3", region_name=AWS_REGION)
        obj = s3.get_object(Bucket=S3_BUCKET, Key="data/press_releases.json")
        return json.loads(obj["Body"].read())
    except Exception as e:
        return []


def summarize_with_bedrock(text: str) -> str:
    """
    Summarize text using AWS Bedrock (Claude Haiku) as a multi-cloud fallback.
    Demonstrates multi-cloud awareness: GCP Vertex AI (primary) + AWS Bedrock (fallback).
    """
    try:
        import boto3, json
        bedrock = boto3.client("bedrock-runtime", region_name="us-east-2")
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 512,
            "messages": [{
                "role": "user",
                "content": f"Summarize this financial text concisely:\n\n{text[:2000]}"
            }]
        })
        resp   = bedrock.invoke_model(
            modelId="anthropic.claude-haiku-20240307-v1:0",
            body=body,
            contentType="application/json",
            accept="application/json",
        )
        result = json.loads(resp["Body"].read())
        return result["content"][0]["text"]
    except Exception as e:
        return f"Bedrock unavailable: {e}"
