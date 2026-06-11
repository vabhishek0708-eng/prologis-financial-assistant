import joblib
import numpy as np

model = joblib.load('models/regression/model.pkl')
scaler = joblib.load('models/regression/scaler.pkl')
feature_names = joblib.load('models/regression/feature_names.pkl')

def predict_house_value(features: dict) -> dict:
    input_data = np.array([[features[f] for f in feature_names]])
    input_scaled = scaler.transform(input_data)
    prediction = model.predict(input_scaled)[0]
    return {
        'predicted_value': round(float(prediction), 4),
        'predicted_value_usd': round(float(prediction) * 100000, 2),
        'features_used': list(feature_names)
    }

if __name__ == '__main__':
    sample = {
        'MedInc': 8.3252,
        'HouseAge': 41.0,
        'AveRooms': 6.984,
        'AveBedrms': 1.023,
        'Population': 322.0,
        'AveOccup': 2.555,
        'Latitude': 37.88,
        'Longitude': -122.23
    }
    result = predict_house_value(sample)
    print('Sample Prediction:')
    print('Predicted House Value:', result['predicted_value'])
    print('Predicted Value USD:', result['predicted_value_usd'])
