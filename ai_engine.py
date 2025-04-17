import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from joblib import dump, load

def prepare_dataset(csv_path, future_shift=1):
    df = pd.read_csv(csv_path, index_col='timestamp', parse_dates=True)

    df['delta_pct'] = (df['close'] - df['open']) / df['open']
    df['future_close'] = df['close'].shift(-future_shift)
    df['target'] = (df['future_close'] > df['close']).astype(int)
    df.dropna(inplace=True)

    features = ['open', 'high', 'low', 'close', 'volume', 'rsi', 
                'MACD_12_26_9', 'MACDh_12_26_9', 'MACDs_12_26_9',
                'ema20', 'ema50', 'delta_pct']
    
    X = df[features]
    y = df['target']
    return X, y, df

def train_model(csv_path, model_output_path):
    X, y, _ = prepare_dataset(csv_path)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

    model = xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss')
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    dump(model, model_output_path)

    return model_output_path, acc

def predict_from_csv(csv_path, model_path):
    X, _, df = prepare_dataset(csv_path)
    model = load(model_path)
    latest_data = X.iloc[-1:]
    prediction = model.predict(latest_data)[0]
    proba = model.predict_proba(latest_data)[0]

    return {
        "prediction": int(prediction),
        "proba_up": round(float(proba[1]), 4),
        "proba_down": round(float(proba[0]), 4),
        "timestamp": df.index[-1].isoformat()
    }
