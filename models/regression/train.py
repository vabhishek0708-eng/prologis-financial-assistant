import pandas as pd
import numpy as np
from sklearn.datasets import fetch_california_housing
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib
import os

print('Loading California Housing dataset...')
housing = fetch_california_housing()
X = pd.DataFrame(housing.data, columns=housing.feature_names)
y = pd.Series(housing.target, name='MedHouseVal')

print('Dataset shape:', X.shape)
print('Features:', list(X.columns))
print('Target stats:')
print(y.describe())

scaler = StandardScaler()
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
X_train = scaler.fit_transform(X_train)
X_test  = scaler.transform(X_test)
print('Train size:', X_train.shape[0], 'Test size:', X_test.shape[0])

print('Training Random Forest Regressor...')
model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print('Model Evaluation:')
print('RMSE:', round(rmse, 4))
print('MAE:', round(mae, 4))
print('R2 Score:', round(r2, 4))

os.makedirs('models/regression', exist_ok=True)
joblib.dump(model, 'models/regression/model.pkl')
joblib.dump(scaler, 'models/regression/scaler.pkl')

feature_names = housing.feature_names
joblib.dump(feature_names, 'models/regression/feature_names.pkl')

metrics = {'rmse': round(rmse, 4), 'mae': round(mae, 4), 'r2': round(r2, 4)}
joblib.dump(metrics, 'models/regression/metrics.pkl')

print('Model saved to models/regression/model.pkl')
print('Scaler saved to models/regression/scaler.pkl')
print('Training complete!')
