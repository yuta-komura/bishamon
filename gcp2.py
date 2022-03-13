import time

from lib.mysql import MySQL

database = "tradingbot"

conn = MySQL(database=database).conn
cur = conn.cursor()

while True:
    sql = """
    insert
    into ohlcv_1min_bitflyer_perp with basis as (
        select
            *
        from
            (
                select
                    date_format(cast(op.date as datetime), '%Y-%m-%d %H:%i:00') as date
                    , op.price as open
                    , basis.high
                    , basis.low
                    , cl.price as close
                    , basis.volume
                from
                    (
                        select
                            min(id) as open_id
                            , max(price) as high
                            , min(price) as low
                            , max(id) as close_id
                            , sum(size) as volume
                        from
                            execution_history_bitflyer_perp
                        group by
                            year (date)
                            , month (date)
                            , day (date)
                            , hour (date)
                            , minute (date)
                    ) basis
                    inner join execution_history_bitflyer_perp op
                        on basis.open_id = op.id
                    inner join execution_history_bitflyer_perp cl
                        on basis.close_id = cl.id
                order by
                    date desc
            ) basis
    )
    ,
    start as (
        select
            date
        from
            ohlcv_1min_bitflyer_perp
        order by
            date desc
        limit
            1
    )
    select
        *
    from
        basis b
    where
        b.date != date_format(cast(now() as datetime), '%Y-%m-%d %H:%i:00')
        and b.date > ifnull((select date from start), '2000-01-01')
    order by
        date
    """
    try:
        cur.execute(sql)
    except Exception:
        pass

    sql = """
    delete
    from
        execution_history_bitflyer_perp
    where
        date < (
            select
                date
            from
                ohlcv_1min_bitflyer_perp
            order by
                date desc
            limit
                1
        )
    """
    try:
        cur.execute(sql)
    except Exception:
        pass

    sql = """
    insert
    into ohlcv_1min_bitflyer_spot with basis as (
        select
            *
        from
            (
                select
                    date_format(cast(op.date as datetime), '%Y-%m-%d %H:%i:00') as date
                    , op.price as open
                    , basis.high
                    , basis.low
                    , cl.price as close
                    , basis.volume
                from
                    (
                        select
                            min(id) as open_id
                            , max(price) as high
                            , min(price) as low
                            , max(id) as close_id
                            , sum(size) as volume
                        from
                            execution_history_bitflyer_spot
                        group by
                            year (date)
                            , month (date)
                            , day (date)
                            , hour (date)
                            , minute (date)
                    ) basis
                    inner join execution_history_bitflyer_spot op
                        on basis.open_id = op.id
                    inner join execution_history_bitflyer_spot cl
                        on basis.close_id = cl.id
                order by
                    date desc
            ) basis
    )
    ,
    start as (
        select
            date
        from
            ohlcv_1min_bitflyer_spot
        order by
            date desc
        limit
            1
    )
    select
        *
    from
        basis b
    where
        b.date != date_format(cast(now() as datetime), '%Y-%m-%d %H:%i:00')
        and b.date > ifnull((select date from start), '2000-01-01')
    order by
        date
    """
    try:
        cur.execute(sql)
    except Exception:
        pass

    sql = """
    delete
    from
        execution_history_bitflyer_spot
    where
        date < (
            select
                date
            from
                ohlcv_1min_bitflyer_spot
            order by
                date desc
            limit
                1
        )
    """
    try:
        cur.execute(sql)
    except Exception:
        pass

    conn.commit()
    time.sleep(1)
