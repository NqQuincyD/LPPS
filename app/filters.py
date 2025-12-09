from datetime import datetime
import json

def month_name(month_num):
    """Convert month number to month name"""
    months = [
        '', 'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ]
    return months[month_num] if 1 <= month_num <= 12 else ''

def format_datetime(dt, format='%Y-%m-%d %H:%M'):
    """Format datetime object"""
    if dt:
        return dt.strftime(format)
    return ''

def format_number(number, decimals=1):
    """Format number with specified decimal places"""
    if number is not None:
        return f"{number:.{decimals}f}"
    return '0.0'

def from_json(json_string):
    """Parse JSON string to Python object"""
    if json_string:
        try:
            return json.loads(json_string)
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}
