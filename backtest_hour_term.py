import datetime

from lib import repository


def get_fr_Date(Date, f):
    before_Date = Date - datetime.timedelta(hours=1)
    return datetime.datetime(
        before_Date.year,
        before_Date.month,
        before_Date.day,
        before_Date.hour,
        f,
        00,
        00)


def get_to_Date(Date):
    return datetime.datetime(
        Date.year,
        Date.month,
        Date.day,
        Date.hour,
        0,
        00,
        00)


def get_entry_Date(Date):
    return datetime.datetime(
        Date.year,
        Date.month,
        Date.day,
        Date.hour,
        1,
        00,
        00)


def get_close_Date(Date, c):
    return datetime.datetime(
        Date.year,
        Date.month,
        Date.day,
        Date.hour,
        c,
        00,
        00)


database = "tradingbot"

sql = "truncate backtest_parameter"
repository.execute(database=database, sql=sql, log=False)

sql = """
        select
            Date
        from
            (select
                min(Date) as Date,
                DATE_FORMAT(min(Date), '%i') as Min
            from
                bitflyer_btc_ohlc_1M
            group by
                year(Date),
                month(Date),
                day(Date),
                hour(Date)
            order by
                year(Date),
                month(Date),
                day(Date),
                hour(Date)) as b
        where
            Min = '00'
        """
test_dates = repository.read_sql(database=database, sql=sql)

for i in range(len(test_dates)):
    Date = test_dates.iloc[i]["Date"]

    result_profit_datas = []
    for f in range(55, 56):
        for c in range(25, 60):
            fr_Date = get_fr_Date(Date, f)
            to_Date = get_to_Date(Date)
            entry_Date = get_entry_Date(Date)
            close_Date = get_close_Date(Date, c)

            sql = """
                    select
                        *
                    from
                        bitflyer_btc_ohlc_1M
                    where
                        Date = '{fr_Date}'
                    or  Date = '{to_Date}'
                    or  Date = '{entry_Date}'
                    or  Date = '{close_Date}'
                    order by
                        Date
                    """.format(fr_Date=fr_Date,
                               to_Date=to_Date,
                               entry_Date=entry_Date,
                               close_Date=close_Date)
            test_data = repository.read_sql(database=database, sql=sql)

            if len(test_data) != 4:
                continue

            fr_data = test_data.iloc[0]
            to_data = test_data.iloc[1]
            entry_data = test_data.iloc[2]
            close_data = test_data.iloc[3]

            fr_Date = fr_data["Date"]
            to_Date = to_data["Date"]
            entry_Date = entry_data["Date"]
            close_Date = close_data["Date"]

            fr_Date_add = fr_Date + datetime.timedelta(hours=1)
            if fr_Date_add.hour != to_Date.hour or to_Date.hour != entry_Date.hour or entry_Date.hour != close_Date.hour \
                    or fr_Date.minute != f or to_Date.minute != 0 or entry_Date.minute != 1 or close_Date.minute != c:
                continue

            asset = 1000000

            roc = (to_data["Close"] - fr_data["Close"]) / fr_data["Close"]

            entry_Price = entry_data["Open"]
            close_Price = close_data["Open"]

            amount = asset / entry_Price

            if roc < 0:
                profit = (amount * close_Price) - asset
            else:
                profit = asset - (amount * close_Price)

            result_profit_datas.append({"fr_min": f,
                                        "close_min": c,
                                        "profit": profit})
    result_profit_datas = \
        sorted(result_profit_datas, key=lambda x: x["profit"], reverse=True)

    if len(result_profit_datas) >= 1:
        max_profit_data = result_profit_datas[0]

        sql = "insert into backtest_parameter values ('{date}',{fr_min},{close_min},{profit})"\
            .format(date=Date,
                    fr_min=max_profit_data["fr_min"],
                    close_min=max_profit_data["close_min"],
                    profit=int(max_profit_data["profit"]))
        repository.execute(database=database, sql=sql, log=False)
