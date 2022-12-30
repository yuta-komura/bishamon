from enum import Enum

PROJECT_DIR = __file__.replace("/lib/config.py", "")


class Anomaly1(Enum):
    TRADING_HOUR = [0, 1, 2, 3, 5, 6, 7, 8, 9, 10, 11,
                    12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
    ANALYSIS_FROM_MINUTE = [51]
    ANALYSIS_TO_MINUTE = [0]
    ENTRY_MINUTE = [1]
    CLOSE_MINUTE = [18]

    RSI = 1
    SMA1 = 100
    SMA2 = 200


class DATABASE(Enum):
    class TRADINGBOT(Enum):
        HOST = 'localhost'
        USER = '*********'
        PASSWORD = '*********'
        DATABASE = '*********'


class Bitflyer(Enum):
    class Api(Enum):
        KEY = "********************************"
        SECRET = "********************************"


class DirPath(Enum):
    PROJECT = PROJECT_DIR


class FilePath(Enum):
    SYSTEM_LOG = PROJECT_DIR + "/log/system.log"
    AA = PROJECT_DIR + "/document/AA.txt"


class Line(Enum):
    TOKEN = "********************************"
