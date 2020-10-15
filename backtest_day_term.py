import datetime

from lib import repository

database = "tradingbot"

sql = """
        select
            *
        from
            (select
                min(Date) as Date
            from
                bitflyer_btc_ohlc_1M
            group by
                year(Date),
                month(Date),
                day(Date)
            order by
                year(Date),
                month(Date),
                day(Date)) as b
        where
            b.Date not in ('2019-10-02 02:25:00', '2020-09-02 17:44:00')
            and b.Date >= '2020-02-13 00:00:00'
        """
test_dates = repository.read_sql(database=database, sql=sql)

for i in range(len(test_dates)):
    test_date = test_dates.loc[i]["Date"]
    test_Year = test_date.year
    test_Month = test_date.month
    test_Day = test_date.day

    result_profit_datas = []
    for m in range(25, 46):
        for j in range(45, 60):
            sql = """
                    select
                        *
                    from
                        bitflyer_btc_ohlc_1M
                    where
                        year(Date) = {year}
                        and month(Date) = {month}
                        and day(Date) = {day}
                        and
                        (
                            minute(Date) = {j}
                        or  minute(Date) between 0 and 1
                        or  minute(Date) = {m}
                        )
                    order by
                        Date
                    """.format(year=test_Year, month=test_Month, day=test_Day, j=j, m=m)
            day_test_data = repository.read_sql(database=database, sql=sql)

            asset = 1000000
            for i in range(len(day_test_data)):
                try:
                    now_data = day_test_data.iloc[i]
                    now_Date = now_data["Date"]
                    now_Close = now_data["Close"]

                    if now_Date.minute == 0 \
                            and now_Date.hour != 5:

                        past_data = day_test_data.iloc[i - 1]
                        past_Date = past_data["Date"]

                        entry_data = day_test_data.iloc[i + 1]
                        entry_Date = entry_data["Date"]

                        close_data = day_test_data.iloc[i + 2]
                        close_Date = close_data["Date"]

                        tD = past_Date + datetime.timedelta(hours=1)
                        if tD.hour != now_Date.hour or now_Date.hour != entry_Date.hour or entry_Date.hour != close_Date.hour \
                                or past_Date.minute != j or entry_Date.minute != 1 or close_Date.minute != m:
                            continue

                        past_Close = past_data["Close"]

                        roc = (now_Close - past_Close) / past_Close

                        entry_Price = entry_data["Open"]
                        close_Price = close_data["Open"]

                        amount = asset / entry_Price

                        if roc < 0:
                            profit = (amount * close_Price) - asset
                        else:
                            profit = asset - (amount * close_Price)

                        asset += profit
                except Exception:
                    pass
            result_profit_datas.append({"back_k": j,
                                        "close_min": m,
                                        "asset": asset})

    result_profit_datas = \
        sorted(result_profit_datas, key=lambda x: x["asset"], reverse=True)
    max_profit_data = result_profit_datas[0]

    sql = "insert into backtest_parameter values ({year},{month},{day},{back_k},{close_min})"\
        .format(year=test_Year,
                month=test_Month,
                day=test_Day,
                back_k=max_profit_data["back_k"],
                close_min=max_profit_data["close_min"])
    print(sql)
    # repository.execute(database=database, sql=sql, log=False)
