"""
Utility functions for the Team Portal application.
"""

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
    
    # For now, just return the datetime as-is
    # TODO: Implement proper timezone conversion when pytz is available
    return utc_datetime


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


def is_module_enabled(module_key):
    """
    Prüft ob ein Modul aktiviert ist.
    
    Args:
        module_key: Der Schlüssel des Moduls (z.B. 'module_chat', 'module_files')
        
    Returns:
        True wenn das Modul aktiviert ist, False sonst. Standardmäßig True wenn nicht gesetzt.
    """
    try:
        from app.models.settings import SystemSettings
        setting = SystemSettings.query.filter_by(key=module_key).first()
        if setting:
            # Prüfe ob der Wert 'true' ist (case-insensitive)
            return str(setting.value).lower() == 'true'
        # Standardmäßig aktiviert wenn nicht gesetzt (für Rückwärtskompatibilität)
        return True
    except Exception:
        # Bei Fehlern (z.B. während Setup) standardmäßig aktiviert
        return True