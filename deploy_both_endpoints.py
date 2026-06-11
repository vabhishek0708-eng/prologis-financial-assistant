
import boto3, json, logging, time, tarfile, tempfile, os, shutil

AWS_REGION    = "us-east-2"
S3_BUCKET     = "prologis-financial-assistant-362612348837"
IAM_ROLE_ARN  = "arn:aws:iam::362612348837:role/SageMakerRole"
SKLEARN_IMAGE = "257758044811.dkr.ecr.us-east-2.amazonaws.com/sagemaker-scikit-learn:1.2-1-cpu-py3"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

# Exact inference script that worked for classification
INFERENCE_SCRIPT = """import os, json, joblib
import numpy as np

def model_fn(model_dir):
    path = os.path.join(model_dir, 'model.pkl')
    print('Loading model from:', path)
    return joblib.load(path)

def input_fn(body, ct='application/json'):
    return np.array(json.loads(body)['features'], dtype=float)

def predict_fn(x, model):
    x = x.reshape(1,-1) if x.ndim == 1 else x
    pred  = model.predict(x).tolist()
    proba = model.predict_proba(x).tolist() if hasattr(model, 'predict_proba') else None
    return {'prediction': pred, 'probabilities': proba}

def output_fn(pred, accept='application/json'):
    return json.dumps(pred), 'application/json'
"""

MODELS = {
    "regression": {
        "files": {
            "model.pkl":         "models/regression/model.pkl",
            "scaler.pkl":        "models/regression/scaler.pkl",
            "feature_names.pkl": "models/regression/feature_names.pkl",
        },
        "s3_key":    "models/regression/regression_final.tar.gz",
        "model_name":"prologis-regression-final",
        "cfg_name":  "prologis-regression-final-cfg",
        "ep_name":   "prologis-regression-endpoint",
    },
    "classification": {
        "files": {
            "model.pkl":         "models/classification/model.pkl",
            "scaler.pkl":        "models/classification/scaler.pkl",
            "feature_names.pkl": "models/classification/feature_names.pkl",
        },
        "s3_key":    "models/classification/classification_final.tar.gz",
        "model_name":"prologis-classification-final",
        "cfg_name":  "prologis-classification-final-cfg",
        "ep_name":   "prologis-classification-endpoint",
    },
}


def build_and_upload(s3, label, cfg):
    log.info("[%s] Building tarball...", label)
    tmp = tempfile.mkdtemp()
    try:
        # Copy all model files into temp dir with exact names
        for dest_name, src_path in cfg["files"].items():
            shutil.copy(src_path, os.path.join(tmp, dest_name))
            size = os.path.getsize(os.path.join(tmp, dest_name))
            log.info("[%s]   %s: %.1f KB", label, dest_name, size/1024)

        # Write inference.py with exact working script
        with open(os.path.join(tmp, "inference.py"), "w") as f:
            f.write(INFERENCE_SCRIPT)
        with open(os.path.join(tmp, "predict.py"), "w") as f:
            f.write(INFERENCE_SCRIPT)

        # Pack tarball — all files flat at root level
        tar_path = os.path.join(tmp, "model.tar.gz")
        with tarfile.open(tar_path, "w:gz") as tf:
            for fname in os.listdir(tmp):
                if fname != "model.tar.gz":
                    tf.add(os.path.join(tmp, fname), arcname=fname)

        tar_size = os.path.getsize(tar_path)
        log.info("[%s] Tarball: %.1f KB", label, tar_size/1024)

        # Upload
        s3.upload_file(tar_path, S3_BUCKET, cfg["s3_key"])
        log.info("[%s] Uploaded to s3://%s/%s", label, S3_BUCKET, cfg["s3_key"])
        return "s3://" + S3_BUCKET + "/" + cfg["s3_key"]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def delete_if_exists(sm, rtype, name):
    fns = {
        "endpoint":        ("describe_endpoint",        "delete_endpoint",        {"EndpointName": name}),
        "endpoint-config": ("describe_endpoint_config", "delete_endpoint_config", {"EndpointConfigName": name}),
        "model":           ("describe_model",           "delete_model",           {"ModelName": name}),
    }
    d, dl, kw = fns[rtype]
    try:
        getattr(sm, d)(**kw)
        log.warning("Deleting %s %s", rtype, name)
        getattr(sm, dl)(**kw)
        if rtype == "endpoint":
            sm.get_waiter("endpoint_deleted").wait(
                EndpointName=name, WaiterConfig={"Delay": 15, "MaxAttempts": 40}
            )
    except sm.exceptions.ClientError:
        pass


def deploy(sm, label, cfg, uri):
    log.info("--- Deploying %s ---", label)
    ep_name = cfg["ep_name"]
    ep_cfg  = cfg["cfg_name"]
    m_name  = cfg["model_name"]

    delete_if_exists(sm, "endpoint",        ep_name)
    delete_if_exists(sm, "endpoint-config", ep_cfg)
    delete_if_exists(sm, "model",           m_name)

    sm.create_model(
        ModelName=m_name,
        PrimaryContainer={
            "Image":        SKLEARN_IMAGE,
            "ModelDataUrl": uri,
            "Environment":  {
                "SAGEMAKER_PROGRAM": "inference.py",
                "SAGEMAKER_SUBMIT_DIRECTORY": uri,
            },
        },
        ExecutionRoleArn=IAM_ROLE_ARN,
    )
    log.info("Model created.")

    sm.create_endpoint_config(
        EndpointConfigName=ep_cfg,
        ProductionVariants=[{
            "VariantName": "AllTraffic",
            "ModelName":   m_name,
            "ServerlessConfig": {
                "MemorySizeInMB": 3072,
                "MaxConcurrency": 5,
            },
        }],
    )
    log.info("Endpoint config created (serverless 3072MB).")

    sm.create_endpoint(EndpointName=ep_name, EndpointConfigName=ep_cfg)
    log.info("Polling %s...", ep_name)

    while True:
        r      = sm.describe_endpoint(EndpointName=ep_name)
        status = r["EndpointStatus"]
        log.info("%s -> %s", ep_name, status)
        if status == "InService":
            log.info("✅ %s InService!", ep_name)
            break
        elif status == "Failed":
            log.error("Failed: %s", r.get("FailureReason"))
            break
        time.sleep(20)


def main():
    log.info("=== Prologis — Deploy Both Endpoints ===")
    sess = boto3.Session(region_name=AWS_REGION)
    sm   = sess.client("sagemaker")
    s3   = sess.client("s3")

    for label, cfg in MODELS.items():
        uri = build_and_upload(s3, label, cfg)
        deploy(sm, label, cfg, uri)

    with open("endpoint_config.json", "w") as f:
        json.dump({
            "regression_endpoint":     MODELS["regression"]["ep_name"],
            "classification_endpoint": MODELS["classification"]["ep_name"],
            "region":    AWS_REGION,
            "s3_bucket": S3_BUCKET,
        }, f, indent=2)
    log.info("✅ All done!")


if __name__ == "__main__":
    main()