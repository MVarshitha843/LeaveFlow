from datetime import date, timedelta
from typing import Set, Tuple, List, Dict

def calculate_business_days(
    start_date: date,
    end_date: date,
    holiday_dates: Set[date]
) -> Dict:
    """
    Calculates working business days between start_date and end_date (inclusive).
    Excludes weekends (Saturday, Sunday) and dates present in holiday_dates.
    Returns a dict with business_days, calendar_days, weekend_days, holiday_days, and details.
    """
    if start_date > end_date:
        return {
            "business_days": 0.0,
            "calendar_days": 0,
            "weekend_days": 0,
            "holiday_days": 0,
            "excluded_dates": [],
            "valid_range": False,
            "error": "Start date must be on or before end date"
        }

    calendar_days = (end_date - start_date).days + 1
    business_days = 0.0
    weekend_days = 0
    holiday_days = 0
    excluded_dates: List[Dict] = []

    current = start_date
    while current <= end_date:
        is_weekend = current.weekday() in (5, 6)  # 5: Saturday, 6: Sunday
        is_holiday = current in holiday_dates

        if is_weekend:
            weekend_days += 1
            excluded_dates.append({
                "date": current.isoformat(),
                "reason": "WEEKEND",
                "day_of_week": current.strftime("%A")
            })
        elif is_holiday:
            holiday_days += 1
            excluded_dates.append({
                "date": current.isoformat(),
                "reason": "HOLIDAY",
                "day_of_week": current.strftime("%A")
            })
        else:
            business_days += 1.0

        current += timedelta(days=1)

    return {
        "business_days": business_days,
        "calendar_days": calendar_days,
        "weekend_days": weekend_days,
        "holiday_days": holiday_days,
        "excluded_dates": excluded_dates,
        "valid_range": True,
        "error": None
    }
