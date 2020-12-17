# bishamon
bitflyer-lightning（btcfxjpy）用のビットコイン自動売買botです。  

**免責事項**：  
当botの利用により損失や被害が生じた場合、作者は一切の責任を負うことはできません。  
投資は自己責任でお願いします。　　

---
[ライセンス](https://github.com/yuta-komura/bishamon/blob/master/LICENSE)

---    
### パフォーマンス
**initial parameter**：  
asset 1,000,000  

**backtest result**：  
2019-11-27 00:00:00 〜 2020-11-27 00:00:00  
profit 31,491,987  
pf 1.52  
wp 57 %  
trading cnt 7994  

pnl curve  
<a href="https://imgur.com/vZvBgN1"><img src="https://i.imgur.com/vZvBgN1.png" title="source: imgur.com" /></a>
entry timing  
<a href="https://imgur.com/gGBiy34"><img src="https://i.imgur.com/gGBiy34.png" title="source: imgur.com" /></a>
<a href="https://imgur.com/fygENTI"><img src="https://i.imgur.com/fygENTI.png" title="source: imgur.com" /></a>

---  
### 環境  
ubuntu20.04 / mysql / python

---  
### インストール  
**mysql**：  
db.sql参照  
必要なデータベースとテーブルを作成後、  
lib/config.pyに設定してください。
```python:config.py
class DATABASE(Enum):
    class TRADINGBOT(Enum):
        HOST = 'localhost'
        USER = 'user'
        PASSWORD = 'password'
        DATABASE = 'tradingbot'
```

**pythonライブラリ**：  
同梱のrequirements.txtを利用して、インストールを行ってください。
```bash
pip install -r requirements.txt
```

**bitflyer apikey**：  
1．bitflyer-lightningのサイドバーから"API"を選択  
<a href="https://imgur.com/afZrmWf"><img src="https://i.imgur.com/afZrmWf.png" title="source: imgur.com" /></a>  
2．"新しいAPIキーを追加"を選択しapikeyを作成  
<a href="https://imgur.com/x56kiBy"><img src="https://i.imgur.com/x56kiBy.png" title="source: imgur.com" /></a>  
3．lib/config.pyに設定してください。
```python:config.py
class Bitflyer(Enum):
    class Api(Enum):
        KEY = "fcksdjcji9swefeixcJKj1"
        SECRET = "sdjkalsxc90wdwkksldfdscmcldsa"
```

**mpg123インストール**：  
このシステムでは、loggerのwarningまたはerror出力時に  
音声が流れるようになっております。  
```bash
sudo apt update -y
sudo apt install -y mpg123
```

**レバレッジ**：  
このシステムでは、レバレッジ4倍分のポジションサイズをとります。  
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
下記2点のシェルスクリプトを実行してください。（別画面で）  

**get_realtime_data.sh**：  
websocketプロトコルを利用しRealtime APIと通信。  
tickerと約定履歴（ローソク足作成用）を取得します。  
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