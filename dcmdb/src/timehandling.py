"""Collection of time handling functions."""

import datetime
import re
import sys


def hub(p, dtgs, leadtime=0):

    dtg = simulation_datetime.strptime(dtgs, "%Y-%m-%d %H:%M:%S")
    dtg.leadtime = datetime.timedelta(seconds=leadtime)

    return dtg.strftime(p)


def expand_dates(sdate, edate, step):
    # Construct a list of dates
    dates = []
    if sdate is not None and edate is not None:
        while sdate <= edate:
            dates.append(sdate)
            sdate += step

    return dates


def expand_times(stime, etime, step):
    # Construct a list of lead_times
    leadtimes = None
    if stime is not None and etime is not None:
        leadtimes = []
        while stime <= etime:
            leadtimes.append(stime.days * 24 * 3600 + stime.seconds)
            stime += step

    return leadtimes


def leadtime2hm(leadtime):

    if isinstance(leadtime, str):
        lh = int(leadtime / 3600)
        lm = int(leadtime) % 3600 / 60
    elif isinstance(leadtime, float):
        lh = int(leadtime / 3600)
        lm = int(leadtime) % 3600 / 60
    elif isinstance(leadtime, int):
        lh = int(leadtime / 3600)
        lm = leadtime % 3600 / 60
    else:
        sys.exit()

    return lh, int(lm)


class simulation_datetime(datetime.datetime):
    """
    Wrapper class for datetime.datetime that adds a leadtime attribute to the datetime object.

    >>> c = simulation_datetime(
    ...     2020, 1, 1, leadtime=datetime.timedelta(hours=10, minutes=30)
    ... )
    >>> c.leadtime
    datetime.timedelta(seconds=37800)
    >>> c.strftime("%Y-%m-%d %H:%M+%LLLL")
    '2020-01-01 00:00+0010'
    >>> c.strftime("%Y-%m-%d %H:%M+%LLL")
    '2020-01-01 00:00+010'
    >>> c.strftime("%Y-%m-%d %H:%M+%LM")
    '2020-01-01 00:00+30'
    >>> c.strftime("%Y-%m-%d %H:%M+%LL%LM")
    '2020-01-01 00:00+1030'
    >>> c = simulation_datetime.strptime(
    ...     "/path/to/output/2024/01/15/0045/file",
    ...     "/path/to/output/%Y/%m/%d/%LLLL/file",
    ... )
    >>> c
    simulation_datetime(2024, 1, 15, 0, 0)
    >>> c.leadtime
    datetime.timedelta(days=1, seconds=75600)
    """

    def __new__(
        cls,
        year=1900,
        month=1,
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
        tzinfo=None,
        leadtime: datetime.timedelta = None,
    ):
        instance = super(simulation_datetime, cls).__new__(
            cls, year, month, day, hour, minute, second, microsecond, tzinfo
        )
        instance.leadtime = leadtime
        return instance

    def strptime(string, format):
        standard_directives = {
            "%Y": {"len": 4, "id": "year"},
            "%m": {"len": 2, "id": "month"},
            "%d": {"len": 2, "id": "day"},
            "%H": {"len": 2, "id": "hour"},
            "%M": {"len": 2, "id": "minute"},
            "%S": {"len": 2, "id": "second"},
        }
        lead_h_directives = {
            "%LLLL": {"len": 4, "id": "leadtime_hour"},
            "%LLL": {"len": 3, "id": "leadtime_hour"},
            "%LL": {"len": 2, "id": "leadtime_hour"},
        }
        lead_m_directives = {"%LM": {"len": 2, "id": "leadtime_minute"}}
        directives = {**standard_directives, **lead_h_directives, **lead_m_directives}
        fmt_pos = re.finditer(f"{'|'.join(directives)}", format)
        time_info = {}
        string_offset = 0

        for match in fmt_pos:
            directive = match.group()
            string_pos_start = string_offset + match.span()[0]
            string_pos_end = (
                string_offset + match.span()[0] + directives[directive]["len"]
            )
            sl = slice(string_pos_start, string_pos_end)
            string_offset += directives[directive]["len"] - len(directive)
            time_info[directives[directive]["id"]] = int(string[sl])

        leadtime = datetime.timedelta(
            hours=time_info.get("leadtime_hour", 0),
            minutes=time_info.get("leadtime_minute", 0),
        )

        time_info["leadtime"] = leadtime
        time_info.pop("leadtime_hour", None)
        time_info.pop("leadtime_minute", None)

        obj = simulation_datetime(**time_info)

        if obj.strftime(format) != string:
            raise ValueError(
                f"String {string} does not match format {format} with leadtime"
            )

        return obj

    def strftime(self, format):
        if self.leadtime is not None:
            re_map = {}
            total_hours = self.leadtime.total_seconds() // 3600
            total_minutes = (self.leadtime.total_seconds() % 3600) // 60
            re_map["%LLLL"] = "{:04d}".format(int(total_hours))
            re_map["%LLL"] = "{:03d}".format(int(total_hours))
            re_map["%LL"] = "{:02d}".format(int(total_hours))
            re_map["%LM"] = "{:02d}".format(int(total_minutes))
        # Replace leadtime directives with leadtime values
        for key, value in re_map.items():
            format = format.replace(key, value)
        # Evaluate remaining standard time directives
        return super().strftime(format)

    def replace(self, **kwargs):
        if "leadtime" in kwargs:
            kwargs["leadtime"] = kwargs["leadtime"] or self.leadtime
        obj = super().replace(**kwargs)
        obj.__class__ = simulation_datetime
        obj.leadtime = kwargs.get("leadtime", self.leadtime)
        return obj
