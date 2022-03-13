import pandas as pd


def add_rsi(df: pd.DataFrame, value: int, use_columns: str) -> pd.DataFrame:
    d = df.copy()
    price_diff_df = d[use_columns].diff()

    up = price_diff_df.copy()
    down = price_diff_df.copy()
    up[up < 0] = 0
    down[down > 0] = 0

    up_sum = up.rolling(value).sum()
    down_sum = down.abs().rolling(value).sum()

    d[f"rsi{use_columns}{value}"] = up_sum / (up_sum + down_sum) * 100
    return d


def add_sma(df: pd.DataFrame, value: int, use_columns: str) -> pd.DataFrame:
    d = df.copy()
    price_df = d[use_columns]
    d[f"sma{use_columns}{value}"] = price_df.rolling(value).mean()
    return d


def add_ema(df: pd.DataFrame, value: int, use_columns: str) -> pd.DataFrame:
    d = df.copy()
    price_df = d[use_columns]
    sma = price_df.rolling(value).mean()[:value]
    d[f"ema{use_columns}{value}"] = \
        pd.concat([sma, price_df[value:]]).ewm(span=value, adjust=False).mean()
    return d


def add_bb(df: pd.DataFrame, value: int, use_columns: str) -> pd.DataFrame:
    d = df.copy()
    mean = d[use_columns].rolling(window=value).mean()
    std = d[use_columns].rolling(window=value).std()
    upper = mean + (std * 2)
    lower = mean - (std * 2)
    d[f"bbupper{use_columns}{value}"] = upper
    d[f"bblower{use_columns}{value}"] = lower
    return d
