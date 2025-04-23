import numpy as np
import pandas as pd
from ta.momentum import RSIIndicator, StochRSIIndicator, ROCIndicator, WilliamsRIndicator, UltimateOscillator
from ta.trend import MACD, CCIIndicator, EMAIndicator, SMAIndicator, ADXIndicator
from ta.volatility import BollingerBands, AverageTrueRange
from sklearn.preprocessing import LabelEncoder

def assign_risk_profile(completeness):
    if completeness >= 0.95:
        return "prudent"
    elif completeness >= 0.75:
        return "moyen"
    else:
        return "risqué"

def enrichir_features(df):
    df = df.copy()

    try:
        # Indicateurs techniques
        df['sma_10'] = SMAIndicator(close=df['close'], window=10).sma_indicator()
        df['sma_50'] = SMAIndicator(close=df['close'], window=50).sma_indicator()
        df['ema_20'] = EMAIndicator(close=df['close'], window=20).ema_indicator()
        df['rsi'] = RSIIndicator(close=df['close'], window=14).rsi()

        stoch = StochRSIIndicator(close=df['close'])
        df['stoch_rsi'] = stoch.stochrsi()
        df['stoch_rsi_k'] = stoch.stochrsi_k()
        df['stoch_rsi_d'] = stoch.stochrsi_d()

        macd = MACD(close=df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        df['macd_diff'] = macd.macd_diff()

        bb = BollingerBands(close=df['close'])
        df['bollinger_high'] = bb.bollinger_hband()
        df['bollinger_low'] = bb.bollinger_lband()
        df['bollinger_width'] = bb.bollinger_wband()

        df['adx'] = ADXIndicator(high=df['high'], low=df['low'], close=df['close']).adx()
        df['atr'] = AverageTrueRange(high=df['high'], low=df['low'], close=df['close']).average_true_range()
        df['cci'] = CCIIndicator(high=df['high'], low=df['low'], close=df['close']).cci()
        df['williams_r'] = WilliamsRIndicator(high=df['high'], low=df['low'], close=df['close']).williams_r()
        df['roc'] = ROCIndicator(close=df['close']).roc()
        df['mom'] = df['close'].diff()
        df['ult_osc'] = UltimateOscillator(high=df['high'], low=df['low'], close=df['close']).ultimate_oscillator()

        # Structure de bougie
        df['delta_pct'] = df['close'].pct_change() * 100
        df['variation'] = (df['close'] - df['open']) / df['open'] * 100
        df['volume_ema'] = df['volume'].ewm(span=20).mean()
        df['upper_shadow'] = df['high'] - df[['close', 'open']].max(axis=1)
        df['lower_shadow'] = df[['close', 'open']].min(axis=1) - df['low']
        df['body_size'] = abs(df['close'] - df['open'])

        # Indicateurs binaires
        df['rsi_overbought'] = (df['rsi'] > 70).astype(int)
        df['rsi_oversold'] = (df['rsi'] < 30).astype(int)
        df['macd_cross'] = (df['macd'] > df['macd_signal']).astype(int)

        # Variations temporelles
        df['variation_10min'] = df['close'].pct_change(periods=2) * 100
        df['variation_1h'] = df['close'].pct_change(periods=12) * 100
        df['variation_24h'] = df['close'].pct_change(periods=288) * 100

        # Complétude et profil de risque
        df["completeness"] = df.notna().mean(axis=1)
        df["risk_profile"] = df["completeness"].apply(assign_risk_profile)

        # Encodage numérique
        le_risk = LabelEncoder()
        df["risk_profile_encoded"] = le_risk.fit_transform(df["risk_profile"])

        return df

    except Exception as e:
        print(f"[❌ enrichir_features ERROR] : {e}")
        return pd.DataFrame()
