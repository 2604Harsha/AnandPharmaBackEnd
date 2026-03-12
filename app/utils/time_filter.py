from datetime import datetime, timedelta
from sqlalchemy import and_
import pytz


def get_time_filter(range_type, column):

    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)

    if range_type == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    elif range_type == "week":
        start = now - timedelta(days=7)

    elif range_type == "month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    elif range_type == "quarter":
        month = (now.month - 1) // 3 * 3 + 1
        start = now.replace(month=month, day=1, hour=0, minute=0, second=0, microsecond=0)

    elif range_type == "year":
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

    else:
        return None

    return and_(column >= start)