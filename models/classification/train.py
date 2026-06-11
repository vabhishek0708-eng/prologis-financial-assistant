
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from ucimlrepo import fetch_ucirepo
import joblib
import os

print('Loading Bank Marketing dataset...')
bank_marketing = fetch_ucirepo(id=222)
X = bank_marketing.data.features
y = bank_marketing.data.targets

print('Dataset shape:', X.shape)
y = y.squeeze()
print('Target distribution:')
print(y.value_counts())

categorical_cols = X.select_dtypes(include=['object']).columns
le = LabelEncoder()
for col in categorical_cols:
    X[col] = le.fit_transform(X[col].astype(str))

y = (y == 'yes').astype(int)

scaler = StandardScaler()
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
X_train = scaler.fit_transform(X_train)
X_test  = scaler.transform(X_test)
print('Train size:', X_train.shape[0], 'Test size:', X_test.shape[0])

print('Training Logistic Regression...')
model = LogisticRegression(max_iter=1000, random_state=42)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred)
recall = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)
cm = confusion_matrix(y_test, y_pred)

print('Model Evaluation:')
print('Accuracy:', round(accuracy, 4))
print('Precision:', round(precision, 4))
print('Recall:', round(recall, 4))
print('F1 Score:', round(f1, 4))
print('Confusion Matrix:')
print(cm)

os.makedirs('models/classification', exist_ok=True)
joblib.dump(model, 'models/classification/model.pkl')
joblib.dump(scaler, 'models/classification/scaler.pkl')
joblib.dump(list(X.columns), 'models/classification/feature_names.pkl')

metrics = {
    'accuracy': round(accuracy, 4),
    'precision': round(precision, 4),
    'recall': round(recall, 4),
    'f1': round(f1, 4),
    'confusion_matrix': cm.tolist()
}
joblib.dump(metrics, 'models/classification/metrics.pkl')
print('Model saved to models/classification/model.pkl')
print('Training complete!')
