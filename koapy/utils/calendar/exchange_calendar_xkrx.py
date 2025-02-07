from datetime import time

import pandas as pd
from exchange_calendars.exchange_calendar import (
    ExchangeCalendar,
    HolidayCalendar,
    end_default,
)
from exchange_calendars.precomputed_exchange_calendar import PrecomputedExchangeCalendar
from pandas.tseries.holiday import Holiday, next_monday
from pytz import UTC, timezone

from .xkrx_holidays import (
    krx_regular_holiday_rules,
    precomputed_csat_days,
    precomputed_krx_holidays,
)

start_krx = pd.Timestamp("1956-03-03", tz=UTC)
start_default = pd.Timestamp("1986-01-04", tz=UTC)


class XKRXExchangeCalendar(ExchangeCalendar):
    """
    Calendar for the Korea exchange, and the primary calendar for
    the country of South Korea.

    Open Time: 9:00 AM, KST (Korean Standard Time)
    Close Time: 3:30 PM, KST (Korean Standard Time)

    NOTE: Korea observes Standard Time year-round.

    Due to the complexity around the Korean holidays, we are hardcoding
    a list of holidays covering 1986-2019, inclusive.

    Regularly-Observed Holidays:
    - Seollal (New Year's Day)
    - Independence Movement Day
    - Labor Day
    - Buddha's Birthday
    - Memorial Day
    - Provincial Election Day
    - Liberation Day
    - Chuseok (Korean Thanksgiving)
    - National Foundation Day
    - Christmas Day
    - End of Year Holiday

    NOTE: Hangeul Day became a national holiday in 2013
    - Hangeul Proclamation Day
    """

    name = "XKRX"

    tz = timezone("Asia/Seoul")

    def __init__(self, start=start_default, end=end_default):
        super().__init__(start=start, end=end)

        earliest_precomputed_year = 1956  # KRX started since 1956
        latest_precomputed_year = (
            2050  # korean_lunar_calendar package currently supports until 2050
        )

        if earliest_precomputed_year > self.first_trading_session.year:
            raise ValueError(
                "The {} holidays are only recorded back to {},"
                " cannot instantiate the {} calendar back to {}.".format(
                    self.name,
                    earliest_precomputed_year,
                    self.name,
                    self.first_trading_session.year,
                ),
            )

        if latest_precomputed_year < self.last_trading_session.year:
            raise ValueError(
                "The {} holidays are only recorded to {},"
                " cannot instantiate the {} calendar for {}.".format(
                    self.name,
                    latest_precomputed_year,
                    self.name,
                    self.last_trading_session.year,
                ),
            )

    # KRX schedule change history
    # https://blog.naver.com/daishin_blog/220724111002

    # 1956-03-03: 0930~1130, 1330~1530
    # 1978-04-??: 1000~1200, 1330~1530
    # 1986-04-??: 0940~1200, 1320~1520
    # 1987-03-??: 0940~1140, 1320~1520
    # 1995-01-01: 0930~1130, 1300~1500
    # 1998-12-07: 0900~1200, 1300~1500
    # 2000-05-22: 0900~1500
    # 2016-08-01: 0900~1530

    # Break time disappears since 2000-05-02
    # https://www.donga.com/news/Economy/article/all/20000512/7534650/1

    # Closing time became 30mins late since 2016-08-01
    # https://biz.chosun.com/site/data/html_dir/2016/07/24/2016072400309.html

    open_times = (
        (None, time(9, 30)),
        (pd.Timestamp("1978-04-01"), time(10, 0)),
        (pd.Timestamp("1986-04-01"), time(9, 40)),
        (pd.Timestamp("1995-01-01"), time(9, 30)),
        (pd.Timestamp("1998-12-07"), time(9, 0)),
    )
    break_start_times = (
        (None, time(11, 30)),
        (pd.Timestamp("1978-04-01"), time(12, 0)),
        (pd.Timestamp("1987-03-01"), time(11, 40)),
        (pd.Timestamp("1995-01-01"), time(11, 30)),
        (pd.Timestamp("1998-12-07"), time(12, 0)),
        (pd.Timestamp("2000-05-22"), None),
    )
    break_end_times = (
        (None, time(13, 30)),
        (pd.Timestamp("1986-04-01"), time(13, 20)),
        (pd.Timestamp("1995-01-01"), time(13, 0)),
        (pd.Timestamp("2000-05-22"), None),
    )
    close_times = (
        (None, time(15, 30)),
        (pd.Timestamp("1986-04-01"), time(15, 20)),
        (pd.Timestamp("1995-01-01"), time(15, 0)),
        (pd.Timestamp("2016-08-01"), time(15, 30)),
    )

    # Saterday became holiday since 1998-12-07
    # https://www.hankyung.com/finance/article/1998080301961

    weekmask = "1111100"

    @property
    def special_weekmasks(self):
        return [
            (None, pd.Timestamp("1998-12-07") - pd.Timedelta(1, unit="D"), "1111110"),
        ]

    # KRX regular and adhoc holidays

    @property
    def regular_holidays(self):
        return HolidayCalendar(krx_regular_holiday_rules)

    @property
    def adhoc_holidays(self):
        return precomputed_krx_holidays.tolist()

    # The first business day of each year:
    #  opening schedule is delayed by an hour.

    @property
    def special_offsets(self):
        return [
            (
                pd.Timedelta(1, unit="h"),
                None,
                None,
                None,
                HolidayCalendar(
                    [
                        Holiday(
                            "First Business Day of Year",
                            month=1,
                            day=2,
                            observance=next_monday,
                        )
                    ]
                ),  # avoiding 01/01 since it's New Year's Day
            ),
        ]

    # Every year's CSAT day, all schedules are delayed by:
    #  before 1998-11-18: 30 minutes
    #  after  1998-11-18: 1 hour

    @property
    def special_offsets_adhoc(self):
        return [
            (
                pd.Timedelta(30, unit="m"),
                pd.Timedelta(30, unit="m"),
                pd.Timedelta(30, unit="m"),
                pd.Timedelta(30, unit="m"),
                precomputed_csat_days[
                    precomputed_csat_days.slice_indexer("1993-08-20", "1998-11-17")
                ],
            ),
            (
                pd.Timedelta(1, unit="h"),
                pd.Timedelta(1, unit="h"),
                pd.Timedelta(1, unit="h"),
                pd.Timedelta(1, unit="h"),
                precomputed_csat_days[
                    precomputed_csat_days.slice_indexer("1998-11-18", None)
                ],
            ),
        ]


class PrecomputedXKRXExchangeCalendar(PrecomputedExchangeCalendar):
    """
    Calendar for the Korea exchange, and the primary calendar for
    the country of South Korea.

    Open Time: 9:00 AM, KST (Korean Standard Time)
    Close Time: 3:30 PM, KST (Korean Standard Time)

    NOTE: Korea observes Standard Time year-round.

    Due to the complexity around the Korean holidays, we are hardcoding
    a list of holidays covering 1986-2019, inclusive.

    Regularly-Observed Holidays:
    - Seollal (New Year's Day)
    - Independence Movement Day
    - Labor Day
    - Buddha's Birthday
    - Memorial Day
    - Provincial Election Day
    - Liberation Day
    - Chuseok (Korean Thanksgiving)
    - National Foundation Day
    - Christmas Day
    - End of Year Holiday

    NOTE: Hangeul Day became a national holiday in 2013
    - Hangeul Proclamation Day
    """

    name = "XKRX"

    tz = timezone("Asia/Seoul")

    open_times = ((None, time(9)),)
    close_times = ((None, time(15, 30)),)

    @property
    def precomputed_holidays(self):
        return precomputed_krx_holidays
