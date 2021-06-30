# bishamon

bitflyer-lightning（btcfxjpy）用のビットコイン自動売買 bot です。

**免責事項**：  
当 bot の利用により損失や被害が生じた場合、作者は一切の責任を負うことはできません。  
投資は自己責任でお願いします。

---

[ライセンス](https://github.com/yuta-komura/bishamon/blob/master/LICENSE)

---

### 複利パフォーマンス

**initial parameter**：  
資産 50,000 円  
月一で 50,000 円 deposit する  
レバレッジ 2倍  

**backtest result**：  
2019-10-02 02:29:00 〜 2021-06-30 16:13:00  
総利益 54,562,603,794,457 円  
pf 1.5  
勝率 54 %  
ic 0.09  
trading回数 35697  

pnl curve  
<a href="https://imgur.com/8T9qzoW"><img src="https://i.imgur.com/8T9qzoW.png" title="source: imgur.com" /></a>

### 単利パフォーマンス

**initial parameter**：  
資産 50,000 円

**backtest result**：  
2019-10-02 02:29:00 〜 2021-06-28 19:18:00  
総利益 662,610 円  
pf 1.26  
wp 54 %  
ic 0.09  
trading cnt 24336

pnl curve  
<a href="https://imgur.com/BRBENTL"><img src="https://i.imgur.com/BRBENTL.png" title="source: imgur.com" /></a>

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
