"""
Utility functions for the Team Portal application.
"""

import pytz
from datetime import datetime
from flask import current_app


def get_local_time(utc_datetime):
    """
    Convert UTC datetime to local timezone.
    
    Args:
        utc_datetime: datetime object in UTC
        
    Returns:
        datetime object in local timezone
    """
    if utc_datetime is None:
        return None
    
    # Get timezone from config
    timezone_name = current_app.config.get('TIMEZONE', 'Europe/Berlin')
    local_tz = pytz.timezone(timezone_name)
    
    # If datetime is naive, assume it's UTC
    if utc_datetime.tzinfo is None:
        utc_datetime = pytz.utc.localize(utc_datetime)
    
    # Convert to local timezone
    return utc_datetime.astimezone(local_tz)


def format_datetime(dt, format_string='%d.%m.%Y %H:%M'):
    """
    Format a datetime object with local timezone.
    
    Args:
        dt: datetime object
        format_string: strftime format string
        
    Returns:
        Formatted datetime string
    """
    if dt is None:
        return ''
    
    local_dt = get_local_time(dt)
    return local_dt.strftime(format_string)


def format_time(dt, format_string='%H:%M'):
    """
    Format a datetime object to time only with local timezone.
    
    Args:
        dt: datetime object
        format_string: strftime format string for time
        
    Returns:
        Formatted time string
    """
    if dt is None:
        return ''
    
    local_dt = get_local_time(dt)
    return local_dt.strftime(format_string)
