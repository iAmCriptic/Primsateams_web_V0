"""
iCal Import/Export Utility Functions
"""

from icalendar import Calendar, Event as ICalEvent
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from app.models.calendar import CalendarEvent
from pytz import UTC


def export_event_to_ical(event: CalendarEvent) -> ICalEvent:
    """
    Konvertiert ein CalendarEvent zu einem iCal Event.
    
    Args:
        event: Das CalendarEvent-Objekt
    
    Returns:
        ICalEvent-Objekt
    """
    ical_event = ICalEvent()
    ical_event.add('summary', event.title)
    ical_event.add('dtstart', event.start_time)
    ical_event.add('dtend', event.end_time)
    
    if event.description:
        ical_event.add('description', event.description)
    
    if event.location:
        ical_event.add('location', event.location)
    
    # Wiederkehrende Termine
    if event.is_master_event and event.recurrence_type != 'none':
        rrule = generate_rrule(event)
        if rrule:
            ical_event.add('rrule', rrule)
    
    # UID für eindeutige Identifikation
    ical_event.add('uid', f'event-{event.id}@prismateams')
    
    # Erstellt/Geändert
    ical_event.add('created', event.created_at)
    ical_event.add('last-modified', event.updated_at)
    
    return ical_event


def generate_rrule(event: CalendarEvent):
    """
    Generiert eine RRULE für wiederkehrende Termine.
    
    Args:
        event: Das CalendarEvent mit Wiederholungsinformationen
    
    Returns:
        RRULE-Dictionary oder None
    """
    if event.recurrence_type == 'none':
        return None
    
    rrule = {}
    
    # FREQ (Frequency)
    freq_map = {
        'daily': 'DAILY',
        'weekly': 'WEEKLY',
        'monthly': 'MONTHLY',
        'yearly': 'YEARLY'
    }
    rrule['FREQ'] = freq_map.get(event.recurrence_type)
    
    # INTERVAL
    if event.recurrence_interval > 1:
        rrule['INTERVAL'] = event.recurrence_interval
    
    # BYDAY für wöchentliche Wiederholung mit spezifischen Wochentagen
    if event.recurrence_type == 'weekly' and event.recurrence_days:
        days = [int(d) for d in event.recurrence_days.split(',')]
        day_map = {0: 'MO', 1: 'TU', 2: 'WE', 3: 'TH', 4: 'FR', 5: 'SA', 6: 'SU'}
        byday = [day_map.get(d) for d in days if d in day_map]
        if byday:
            rrule['BYDAY'] = ','.join(byday)
    
    # UNTIL (Enddatum)
    if event.recurrence_end_date:
        rrule['UNTIL'] = event.recurrence_end_date
    
    return rrule


def generate_ical_feed(events, feed_name='Kalender') -> str:
    """
    Generiert einen vollständigen iCal-String aus einer Liste von Events.
    
    Args:
        events: Liste von CalendarEvent-Objekten
        feed_name: Name des Kalenders
    
    Returns:
        iCal-String
    """
    cal = Calendar()
    cal.add('prodid', '-//Prismateams//Kalender//DE')
    cal.add('version', '2.0')
    cal.add('calscale', 'GREGORIAN')
    cal.add('X-WR-CALNAME', feed_name)
    cal.add('X-WR-TIMEZONE', 'Europe/Berlin')
    
    for event in events:
        ical_event = export_event_to_ical(event)
        cal.add_component(ical_event)
    
    return cal.to_ical().decode('utf-8')


def import_events_from_ical(ical_data: str, user_id: int):
    """
    Importiert Events aus einem iCal-String.
    
    Args:
        ical_data: iCal-String
        user_id: ID des Benutzers, der die Events importiert
    
    Returns:
        Liste von CalendarEvent-Objekten (noch nicht gespeichert)
    """
    from app import db
    
    cal = Calendar.from_ical(ical_data)
    events = []
    
    for component in cal.walk():
        if component.name == 'VEVENT':
            # Titel
            title = str(component.get('summary', 'Unbenannter Termin'))
            
            # Start- und Endzeit
            dtstart = component.get('dtstart')
            dtend = component.get('dtend')
            
            if not dtstart:
                continue
            
            start_time = dtstart.dt
            if isinstance(start_time, datetime):
                pass
            else:
                # Nur Datum, keine Zeit
                start_time = datetime.combine(start_time, datetime.min.time())
            
            if dtend:
                end_time = dtend.dt
                if not isinstance(end_time, datetime):
                    end_time = datetime.combine(end_time, datetime.max.time())
            else:
                # Wenn kein Enddatum, verwende Startzeit + 1 Stunde
                end_time = start_time + timedelta(hours=1)
            
            # Beschreibung
            description = str(component.get('description', ''))
            
            # Ort
            location = str(component.get('location', ''))
            
            # Wiederholung
            rrule = component.get('rrule')
            recurrence_type = 'none'
            recurrence_end_date = None
            recurrence_interval = 1
            recurrence_days = None
            
            if rrule:
                rrule_dict = dict(rrule)
                freq = rrule_dict.get('FREQ', [None])[0]
                
                freq_map = {
                    'DAILY': 'daily',
                    'WEEKLY': 'weekly',
                    'MONTHLY': 'monthly',
                    'YEARLY': 'yearly'
                }
                recurrence_type = freq_map.get(freq, 'none')
                
                if 'INTERVAL' in rrule_dict:
                    recurrence_interval = int(rrule_dict['INTERVAL'][0])
                
                if 'BYDAY' in rrule_dict:
                    byday = rrule_dict['BYDAY']
                    day_map = {'MO': 0, 'TU': 1, 'WE': 2, 'TH': 3, 'FR': 4, 'SA': 5, 'SU': 6}
                    days = [str(day_map.get(d, '')) for d in byday if d in day_map]
                    recurrence_days = ','.join([d for d in days if d])
                
                if 'UNTIL' in rrule_dict:
                    until = rrule_dict['UNTIL'][0]
                    if isinstance(until, datetime):
                        recurrence_end_date = until
            
            event = CalendarEvent(
                title=title,
                description=description if description else None,
                start_time=start_time,
                end_time=end_time,
                location=location if location else None,
                created_by=user_id,
                recurrence_type=recurrence_type,
                recurrence_end_date=recurrence_end_date,
                recurrence_interval=recurrence_interval,
                recurrence_days=recurrence_days,
                is_recurring_instance=False
            )
            
            events.append(event)
    
    return events


