"""
Badí' (Bahá'í) Calendar Utility

The Bahá'í calendar consists of 19 months of 19 days each (361 days),
plus 4-5 intercalary days (Ayyám-i-Há) between the 18th and 19th months.

The Bahá'í year begins on Naw-Rúz (March 20 or 21, depending on the spring equinox).
Year 1 of the Bahá'í Era began on March 21, 1844.
"""

from datetime import date, timedelta
from typing import Tuple, Optional

# Bahá'í months with their names and meanings
BADI_MONTHS = [
    {"number": 1, "name": "Bahá", "arabic": "بهاء", "meaning": "Splendour", "translation": "Splendor"},
    {"number": 2, "name": "Jalál", "arabic": "جلال", "meaning": "Glory", "translation": "Glory"},
    {"number": 3, "name": "Jamál", "arabic": "جمال", "meaning": "Beauty", "translation": "Beauty"},
    {"number": 4, "name": "'Aẓamat", "arabic": "عظمة", "meaning": "Grandeur", "translation": "Grandeur"},
    {"number": 5, "name": "Núr", "arabic": "نور", "meaning": "Light", "translation": "Light"},
    {"number": 6, "name": "Raḥmat", "arabic": "رحمة", "meaning": "Mercy", "translation": "Mercy"},
    {"number": 7, "name": "Kalimát", "arabic": "كلمات", "meaning": "Words", "translation": "Words"},
    {"number": 8, "name": "Kamál", "arabic": "كمال", "meaning": "Perfection", "translation": "Perfection"},
    {"number": 9, "name": "Asmá'", "arabic": "أسماء", "meaning": "Names", "translation": "Names"},
    {"number": 10, "name": "'Izzat", "arabic": "عزة", "meaning": "Might", "translation": "Might"},
    {"number": 11, "name": "Mashíyyat", "arabic": "مشية", "meaning": "Will", "translation": "Will"},
    {"number": 12, "name": "'Ilm", "arabic": "علم", "meaning": "Knowledge", "translation": "Knowledge"},
    {"number": 13, "name": "Qudrat", "arabic": "قدرة", "meaning": "Power", "translation": "Power"},
    {"number": 14, "name": "Qawl", "arabic": "قول", "meaning": "Speech", "translation": "Speech"},
    {"number": 15, "name": "Masá'il", "arabic": "مسائل", "meaning": "Questions", "translation": "Questions"},
    {"number": 16, "name": "Sharaf", "arabic": "شرف", "meaning": "Honour", "translation": "Honor"},
    {"number": 17, "name": "Sulṭán", "arabic": "سلطان", "meaning": "Sovereignty", "translation": "Sovereignty"},
    {"number": 18, "name": "Mulk", "arabic": "ملك", "meaning": "Dominion", "translation": "Dominion"},
    {"number": 0, "name": "Ayyám-i-Há", "arabic": "أيام الهاء", "meaning": "Intercalary Days", "translation": "Days of Há"},
    {"number": 19, "name": "'Alá'", "arabic": "علاء", "meaning": "Loftiness", "translation": "Loftiness"},
]

# Map month number to index in BADI_MONTHS
MONTH_INDEX = {m["number"]: i for i, m in enumerate(BADI_MONTHS)}

def get_naw_ruz(gregorian_year: int) -> date:
    """
    Get the date of Naw-Rúz for a given Gregorian year.
    Naw-Rúz falls on March 20 or 21, determined by the spring equinox in Tehran.
    For simplicity, we use March 20 for years 2015 onwards (when the new calculation began),
    and March 21 for earlier years.
    """
    # From 2015 onwards, Naw-Rúz is calculated based on the equinox in Tehran
    # This is a simplified calculation - actual dates may vary slightly
    if gregorian_year >= 2015:
        # Most years it's March 20, but some years it's March 21
        # This is a simplified approximation
        return date(gregorian_year, 3, 20)
    else:
        return date(gregorian_year, 3, 21)

def is_leap_year_badi(badi_year: int) -> bool:
    """
    Determine if a Bahá'í year is a leap year (has 5 Ayyám-i-Há days instead of 4).
    This corresponds to when the Gregorian year containing most of the Bahá'í year is a leap year.
    """
    # The Bahá'í year starts in March, so year X corresponds mostly to Gregorian year (X + 1843)
    gregorian_year = badi_year + 1843
    # Check if the following Gregorian year is a leap year (since Ayyám-i-Há is in February)
    next_year = gregorian_year + 1
    return (next_year % 4 == 0 and next_year % 100 != 0) or (next_year % 400 == 0)

def gregorian_to_badi(gregorian_date: date) -> Tuple[int, int, int]:
    """
    Convert a Gregorian date to a Badí' date.
    Returns (year, month, day) where month 0 = Ayyám-i-Há.
    """
    # Find the Bahá'í year
    naw_ruz_this_year = get_naw_ruz(gregorian_date.year)
    
    if gregorian_date >= naw_ruz_this_year:
        badi_year = gregorian_date.year - 1843
        start_of_year = naw_ruz_this_year
    else:
        badi_year = gregorian_date.year - 1844
        start_of_year = get_naw_ruz(gregorian_date.year - 1)
    
    # Calculate day of the Bahá'í year (1-indexed)
    day_of_year = (gregorian_date - start_of_year).days + 1
    
    # Determine month and day
    if day_of_year <= 342:  # First 18 months (18 * 19 = 342 days)
        month = ((day_of_year - 1) // 19) + 1
        day = ((day_of_year - 1) % 19) + 1
    elif day_of_year <= 342 + (5 if is_leap_year_badi(badi_year) else 4):
        # Ayyám-i-Há
        month = 0
        day = day_of_year - 342
    else:
        # Month of 'Alá' (19th month)
        month = 19
        day = day_of_year - 342 - (5 if is_leap_year_badi(badi_year) else 4)
    
    return (badi_year, month, day)

def badi_to_gregorian(badi_year: int, badi_month: int, badi_day: int) -> date:
    """
    Convert a Badí' date to a Gregorian date.
    badi_month: 1-18, 0 for Ayyám-i-Há, 19 for 'Alá'
    """
    gregorian_year = badi_year + 1843
    naw_ruz = get_naw_ruz(gregorian_year)
    
    if badi_month >= 1 and badi_month <= 18:
        # Regular months 1-18
        day_of_year = (badi_month - 1) * 19 + badi_day
    elif badi_month == 0:
        # Ayyám-i-Há
        day_of_year = 342 + badi_day
    elif badi_month == 19:
        # Month of 'Alá' (19th month)
        ayyam_days = 5 if is_leap_year_badi(badi_year) else 4
        day_of_year = 342 + ayyam_days + badi_day
    else:
        raise ValueError(f"Invalid Badí' month: {badi_month}")
    
    return naw_ruz + timedelta(days=day_of_year - 1)

def get_badi_month_date_range(badi_year: int, badi_month: int) -> Tuple[date, date]:
    """
    Get the Gregorian date range for a Badí' month.
    Returns (start_date, end_date) in Gregorian calendar.
    """
    if badi_month >= 1 and badi_month <= 18:
        start = badi_to_gregorian(badi_year, badi_month, 1)
        end = badi_to_gregorian(badi_year, badi_month, 19)
    elif badi_month == 0:
        # Ayyám-i-Há
        start = badi_to_gregorian(badi_year, 0, 1)
        days = 5 if is_leap_year_badi(badi_year) else 4
        end = badi_to_gregorian(badi_year, 0, days)
    elif badi_month == 19:
        start = badi_to_gregorian(badi_year, 19, 1)
        end = badi_to_gregorian(badi_year, 19, 19)
    else:
        raise ValueError(f"Invalid Badí' month: {badi_month}")
    
    return (start, end)

def get_badi_year_date_range(badi_year: int) -> Tuple[date, date]:
    """
    Get the Gregorian date range for a Badí' year.
    Returns (start_date, end_date) in Gregorian calendar.
    """
    start = badi_to_gregorian(badi_year, 1, 1)  # First day of Bahá
    end = badi_to_gregorian(badi_year, 19, 19)  # Last day of 'Alá'
    return (start, end)

def get_current_badi_date() -> Tuple[int, int, int]:
    """Get the current date in Badí' calendar."""
    return gregorian_to_badi(date.today())

def get_badi_month_name(month_number: int) -> dict:
    """Get the month info for a given month number."""
    if month_number in MONTH_INDEX:
        return BADI_MONTHS[MONTH_INDEX[month_number]]
    return None

def get_all_months() -> list:
    """Get all Badí' months info."""
    return BADI_MONTHS

def format_badi_date(badi_year: int, badi_month: int, badi_day: int) -> str:
    """Format a Badí' date as a string."""
    month_info = get_badi_month_name(badi_month)
    month_name = month_info["name"] if month_info else "Unknown"
    return f"{badi_day} {month_name} {badi_year} BE"

def gregorian_year_to_badi_year(gregorian_year: int, gregorian_month: int = 1) -> int:
    """
    Convert a Gregorian year to a Badí' year.
    If the Gregorian month is before Naw-Rúz (March 20/21), returns the previous Badí' year.
    """
    if gregorian_month >= 3:
        return gregorian_year - 1843
    else:
        return gregorian_year - 1844
