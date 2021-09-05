# bishamon

bitflyer-lightning（btcfxjpy）用のビットコイン自動売買 bot です。

**免責事項**：  
当 bot の利用により損失や被害が生じた場合、作者は一切の責任を負うことはできません。  
投資は自己責任でお願いします。

---

[ライセンス](https://github.com/yuta-komura/bishamon/blob/master/LICENSE)

---

### パラメータ

parameter1 :  
analysis_from_minutes 51  
analysis_to_minutes 0  
entry_minutes 1  
close_minutes 18

parameter2 :  
analysis_from_minutes 1  
analysis_to_minutes 13  
entry_minutes 20  
close_minutes 36

---

### 単利パフォーマンス

※entry時は資産分賭ける

**initial parameter**：  
資産 50,000 円  
レバレッジ 2 倍

**backtest result**：  
2019-10-02 09:00:00 ～ 2021-09-06 00:00:00  
総利益 615,830 円  
pf 1.55  
勝率 58 %  
trading回数 9628  

pnl curve  
<a href="https://imgur.com/J9s9weS"><img src="https://imgur.com/J9s9weS.png" title="source: imgur.com" /></a>

---

### 環境

ubuntu20.04 / mysql / python

---

### インストール

**mysql**：  
db.sql 参照  
必要なデータベースとテーブルを作成後、  
lib/config.py に設定してください。

```python:config.py
class DATABASE(Enum):
    class TRADINGBOT(Enum):
        HOST = 'localhost'
        USER = 'user'
        PASSWORD = 'password'
        DATABASE = 'tradingbot'
```

**python ライブラリ**：  
同梱の requirements.txt を利用して、インストールを行ってください。

```bash
pip install -r requirements.txt
```

**bitflyer apikey**：  
1．bitflyer-lightning のサイドバーから"API"を選択  
<a href="https://imgur.com/afZrmWf"><img src="https://i.imgur.com/afZrmWf.png" title="source: imgur.com" /></a>  
2．"新しい API キーを追加"を選択し apikey を作成  
<a href="https://imgur.com/x56kiBy"><img src="https://i.imgur.com/x56kiBy.png" title="source: imgur.com" /></a>  
3．lib/config.py に設定してください。

```python:config.py
class Bitflyer(Enum):
    class Api(Enum):
        KEY = "fcksdjcji9swefeixcJKj1"
        SECRET = "sdjkalsxc90wdwkksldfdscmcldsa"
```

**レバレッジ**：  
このシステムでは、レバレッジ 4 倍分のポジションサイズをとります。  
ポジションサイズの変更は**lib/bitflyer.py**のコンストラクタで設定してください。

```python:bitflyer.py
    def __init__(self, api_key, api_secret):
        self.api = pybitflyer.API(api_key=api_key, api_secret=api_secret)
        self.PRODUCT_CODE = "FX_BTC_JPY"
        self.LEVERAGE = 4
        self.DATABASE = "tradingbot"
```

---

### 起動方法

下記 2 点のシェルスクリプトを実行してください。（別画面で）

**get_realtime_data.sh**：  
websocket プロトコルを利用し Realtime API と通信。  
ticker と約定履歴（ローソク足作成用）を取得します。

```bash
sh bishamon/main/get_realtime_data.sh
```

**execute.sh**：  
メインスクリプト用

```bash
sh bishamon/main/execute.sh
```

---

### main process

<a href="https://imgur.com/D9MlxAZ"><img src="https://i.imgur.com/D9MlxAZ.png" title="source: imgur.com" /></a>
