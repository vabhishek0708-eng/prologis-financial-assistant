import joblib
import numpy as np

model = joblib.load('models/classification/model.pkl')
scaler = joblib.load('models/classification/scaler.pkl')
feature_names = joblib.load('models/classification/feature_names.pkl')

def predict_subscription(features: dict) -> dict:
    input_data = np.array([[features[f] for f in feature_names]])
    input_scaled = scaler.transform(input_data)
    prediction = model.predict(input_scaled)[0]
    probability = model.predict_proba(input_scaled)[0]
    return {
        'prediction': int(prediction),
        'prediction_label': 'Will Subscribe' if prediction == 1 else 'Will Not Subscribe',
        'probability_yes': round(float(probability[1]), 4),
        'probability_no': round(float(probability[0]), 4)
    }

if __name__ == '__main__':
    sample = {
        'age': 35,
        'job': 2,
        'marital': 1,
        'education': 3,
        'default': 0,
        'balance': 1500,
        'housing': 1,
        'loan': 0,
        'contact': 1,
        'day_of_week': 2,
        'month': 5,
        'duration': 200,
        'campaign': 2,
        'pdays': 999,
        'previous': 0,
        'poutcome': 1
    }
    result = predict_subscription(sample)
    print('Sample Prediction:')
    print('Result:', result['prediction_label'])
    print('Probability Yes:', result['probability_yes'])
    print('Probability No:', result['probability_no'])
