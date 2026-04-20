import httpx
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, classification_report

df = pd.read_csv('data/data.csv')
df.columns = df.columns.str.strip()
for col in df.select_dtypes(include='object').columns:
    df[col] = df[col].str.strip()

print(f"Total records: {len(df)}")

y_true_cat = []
y_pred_cat = []
y_true_pri = []
y_pred_pri = []

for idx, row in df.iterrows():
    try:
        r = httpx.post('http://localhost:8766/predict', json={
            'complaint_id': int(row['complaint_id']),
            'text': str(row['text'])
        }, timeout=60)
        result = r.json()
        
        y_true_cat.append(row['category'])
        y_pred_cat.append(result['category'])
        y_true_pri.append(row['priority'])
        y_pred_pri.append(result['priority'])
        print(f"Processed complaint_id {row['complaint_id']}: True Category={row['category']}, Predicted Category={result['category']}, True Priority={row['priority']}, Predicted Priority={result['priority']}")
    except Exception as e:
        print(f"Error at {row['complaint_id']}: {e}")

print("\n=== CATEGORY METRICS ===")
print(f"Accuracy: {accuracy_score(y_true_cat, y_pred_cat):.4f}")
print(classification_report(y_true_cat, y_pred_cat))

print("\n=== PRIORITY METRICS ===")
print(f"Accuracy: {accuracy_score(y_true_pri, y_pred_pri):.4f}")
print(classification_report(y_true_pri, y_pred_pri))

print("\n=== CATEGORY METRICS ===")
print(f"Recall: {recall_score(y_true_cat, y_pred_cat):.4f}")
print(classification_report(y_true_cat, y_pred_cat))

print("\n=== PRIORITY METRICS ===")
print(f"Recall: {recall_score(y_true_pri, y_pred_pri):.4f}")
print(classification_report(y_true_pri, y_pred_pri))

print("\n=== CATEGORY METRICS ===")
print(f"Precision: {precision_score(y_true_cat, y_pred_cat):.4f}")
print(classification_report(y_true_cat, y_pred_cat))

print("\n=== PRIORITY METRICS ===")
print(f"Precision: {precision_score(y_true_pri, y_pred_pri):.4f}")
print(classification_report(y_true_pri, y_pred_pri))


