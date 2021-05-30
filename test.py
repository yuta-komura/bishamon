import datetime
import sys
from pprint import pprint

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import mean_absolute_error
from sklearn.preprocessing import MinMaxScaler

from lib import indicator, message
from lib import pandas_option as pd_op
from lib import repository

tf.compat.v1.disable_eager_execution()


database = "tradingbot"

sql = """
        select
            perp.date,
            perp.close as price,
            perp.open,
            perp.high,
            perp.low,
            perp.volume
        from
            ohlcv_1min_bitflyer_perp perp
        where
            perp.date between '2021-04-15 00:00:00' and '2099-04-30 00:00:00'
        order by
            date
        limit 10000
        """
df = repository.read_sql(database=database, sql=sql)

df_shift = df.copy()


df_shift = indicator.add_sma(df=df_shift, value=22)
df_shift = indicator.add_sma(df=df_shift, value=34)
df_shift = indicator.add_sma(df=df_shift, value=55)
df_shift = indicator.add_ema(df=df_shift, value=22)
df_shift = indicator.add_ema(df=df_shift, value=34)
df_shift = indicator.add_ema(df=df_shift, value=55)
df_shift = indicator.add_rsi(df=df_shift, value=22)
df_shift = indicator.add_rsi(df=df_shift, value=34)
df_shift = indicator.add_rsi(df=df_shift, value=55)
df_shift = df_shift.dropna()


df_shift["price"] = df_shift["price"].shift(-1)
df_shift = df_shift[:-1]

df_2 = df_shift.copy()
del df_2["date"]

n = df_2.shape[0]
p = df_2.shape[1]
train_start = 0
train_end = int(np.floor(0.8 * n))
test_start = train_end + 1
test_end = n

data_train = df_2.iloc[np.arange(train_start, train_end), :]
data_test = df_2.iloc[np.arange(test_start, test_end), :]

scaler = MinMaxScaler(feature_range=(-1, 1))
scaler.fit(data_train)
data_train_norm = scaler.transform(data_train)
data_test_norm = scaler.transform(data_test)

X_train = data_train_norm[:, 1:]
y_train = data_train_norm[:, 0]
X_test = data_test_norm[:, 1:]
y_test = data_test_norm[:, 0]

y_test = y_test.reshape(len(data_test), 1)
test_inv = np.concatenate((y_test, X_test), axis=1)
test_inv = scaler.inverse_transform(test_inv)

# 訓練データの特徴量の数を取得
n_stocks = X_train.shape[1]

n_neurons_1 = 256
n_neurons_2 = 128

net = tf.compat.v1.InteractiveSession()

X = tf.compat.v1.placeholder(dtype=tf.float32, shape=[None, n_stocks])
Y = tf.compat.v1.placeholder(dtype=tf.float32, shape=[None])

sigma = 1
weight_initializer = tf.compat.v1.variance_scaling_initializer(
    mode="fan_avg", distribution="uniform", scale=sigma)
bias_initializer = tf.zeros_initializer()

# Hidden weights
W_hidden_1 = tf.Variable(weight_initializer([n_stocks, n_neurons_1]))
bias_hidden_1 = tf.Variable(bias_initializer([n_neurons_1]))
W_hidden_2 = tf.Variable(weight_initializer([n_neurons_1, n_neurons_2]))
bias_hidden_2 = tf.Variable(bias_initializer([n_neurons_2]))

# 出力の重み
W_out = tf.Variable(weight_initializer([n_neurons_2, 1]))
bias_out = tf.Variable(bias_initializer([1]))

# 隠れ層の設定（ReLU＝活性化関数）
hidden_1 = tf.nn.relu(tf.add(tf.matmul(X, W_hidden_1), bias_hidden_1))
hidden_2 = tf.nn.relu(tf.add(tf.matmul(hidden_1, W_hidden_2), bias_hidden_2))

# 出力層の設定
out = tf.transpose(tf.add(tf.matmul(hidden_2, W_out), bias_out))

# コスト関数
mse = tf.reduce_mean(tf.compat.v1.squared_difference(out, Y))

# 最適化関数
opt = tf.compat.v1.train.AdamOptimizer().minimize(mse)

# 初期化
net.run(tf.compat.v1.global_variables_initializer())

# ニューラルネットワークの設定
batch_size = 128
mse_train = []
mse_test = []

# 訓練開始！500回の反復処理
epochs = 500
for e in range(epochs):
    net.run(opt, feed_dict={X: X_train, Y: y_train})

# テストデータで予測
pred_test = net.run(out, feed_dict={X: X_test})

# 予測値をテストデータに戻そう（値も正規化からインバース）
pred_test = np.concatenate((pred_test.T, X_test), axis=1)
pred_inv = scaler.inverse_transform(pred_test)

# MAEの計算
mae_test = mean_absolute_error(test_inv, pred_inv)
message.info("mae", mae_test)

fig = plt.figure()
ax1 = fig.add_subplot(111)
line1, = ax1.plot(test_inv[:, 0])
line2, = ax1.plot(pred_inv[:, 0])
plt.show()
