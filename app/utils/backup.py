"""
Backup- und Restore-Funktionalität für PrismaTeams
"""
import json
import os
import shutil
import tempfile
from datetime import datetime
from typing import List, Dict, Set, Optional
from flask import current_app
from app import db
from app.models import (
    User, Chat, ChatMessage, ChatMember,
    File, FileVersion, Folder,
    CalendarEvent, EventParticipant,
    EmailMessage, EmailPermission, EmailAttachment,
    Credential, SystemSettings, WhitelistEntry,
    NotificationSettings
)
from app.blueprints.credentials import get_encryption_key


BACKUP_VERSION = "1.0"
SUPPORTED_CATEGORIES = {
    'settings': 'Einstellungen',
    'users': 'Benutzer',
    'emails': 'E-Mails',
    'chats': 'Chats',
    'appointments': 'Termine',
    'credentials': 'Zugangsdaten',
    'files': 'Dateien'
}


def export_backup(categories: List[str], output_path: str) -> Dict:
    """
    Erstellt ein Backup der ausgewählten Kategorien.
    
    Args:
        categories: Liste der zu exportierenden Kategorien
        output_path: Pfad zur Ausgabedatei (.teamportal)
    
    Returns:
        Dict mit Metadaten über das Backup
    """
    backup_data = {
        'version': BACKUP_VERSION,
        'created_at': datetime.utcnow().isoformat(),
        'categories': categories,
        'data': {}
    }
    
    # Einstellungen exportieren
    if 'settings' in categories or 'all' in categories:
        backup_data['data']['settings'] = export_settings()
        backup_data['data']['whitelist'] = export_whitelist()
    
    # Benutzer exportieren
    if 'users' in categories or 'all' in categories:
        backup_data['data']['users'] = export_users()
        backup_data['data']['notification_settings'] = export_notification_settings()
    
    # E-Mails exportieren
    if 'emails' in categories or 'all' in categories:
        backup_data['data']['emails'] = export_emails()
        backup_data['data']['email_permissions'] = export_email_permissions()
        backup_data['data']['email_attachments'] = export_email_attachments()
    
    # Chats exportieren
    if 'chats' in categories or 'all' in categories:
        backup_data['data']['chats'] = export_chats()
        backup_data['data']['chat_messages'] = export_chat_messages()
        backup_data['data']['chat_members'] = export_chat_members()
    
    # Termine exportieren
    if 'appointments' in categories or 'all' in categories:
        backup_data['data']['calendar_events'] = export_calendar_events()
        backup_data['data']['event_participants'] = export_event_participants()
    
    # Zugangsdaten exportieren (entschlüsselt)
    if 'credentials' in categories or 'all' in categories:
        backup_data['data']['credentials'] = export_credentials()
    
    # Dateien exportieren
    if 'files' in categories or 'all' in categories:
        backup_data['data']['folders'] = export_folders()
        backup_data['data']['files'] = export_files()
        backup_data['data']['file_versions'] = export_file_versions()
    
    # Backup-Datei schreiben
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, indent=2, ensure_ascii=False, default=str)
    
    return {
        'success': True,
        'file_path': output_path,
        'categories': categories,
        'created_at': backup_data['created_at']
    }


def export_settings() -> List[Dict]:
    """Exportiert System-Einstellungen."""
    settings = SystemSettings.query.all()
    return [{
        'key': s.key,
        'value': s.value,
        'description': s.description,
        'updated_at': s.updated_at.isoformat() if s.updated_at else None
    } for s in settings]


def export_whitelist() -> List[Dict]:
    """Exportiert Whitelist-Einträge."""
    entries = WhitelistEntry.query.all()
    return [{
        'entry': e.entry,
        'entry_type': e.entry_type,
        'description': e.description,
        'is_active': e.is_active,
        'created_at': e.created_at.isoformat() if e.created_at else None
    } for e in entries]


def export_users() -> List[Dict]:
    """Exportiert Benutzer (inkl. Passwort-Hashes)."""
    users = User.query.all()
    return [{
        'email': u.email,
        'password_hash': u.password_hash,  # Passwort-Hash wird exportiert
        'first_name': u.first_name,
        'last_name': u.last_name,
        'phone': u.phone,
        'is_active': u.is_active,
        'is_admin': u.is_admin,
        'is_email_confirmed': u.is_email_confirmed,
        'profile_picture': u.profile_picture,
        'accent_color': u.accent_color,
        'accent_gradient': u.accent_gradient,
        'dark_mode': u.dark_mode,
        'notifications_enabled': u.notifications_enabled,
        'chat_notifications': u.chat_notifications,
        'email_notifications': u.email_notifications,
        'can_borrow': u.can_borrow,
        'created_at': u.created_at.isoformat() if u.created_at else None,
        'last_login': u.last_login.isoformat() if u.last_login else None
    } for u in users]


def export_notification_settings() -> List[Dict]:
    """Exportiert Notification-Einstellungen."""
    settings = NotificationSettings.query.all()
    return [{
        'user_email': User.query.get(s.user_id).email if User.query.get(s.user_id) else None,
        'chat_notifications_enabled': s.chat_notifications_enabled,
        'file_notifications_enabled': s.file_notifications_enabled,
        'file_new_notifications': s.file_new_notifications,
        'file_modified_notifications': s.file_modified_notifications,
        'email_notifications_enabled': s.email_notifications_enabled,
        'calendar_notifications_enabled': s.calendar_notifications_enabled,
        'calendar_all_events': s.calendar_all_events,
        'calendar_participating_only': s.calendar_participating_only,
        'calendar_not_participating': s.calendar_not_participating,
        'calendar_no_response': s.calendar_no_response,
        'reminder_times': s.reminder_times
    } for s in settings]


def export_emails() -> List[Dict]:
    """Exportiert E-Mails."""
    emails = EmailMessage.query.all()
    return [{
        'uid': e.uid,
        'message_id': e.message_id,
        'subject': e.subject,
        'sender': e.sender,
        'recipients': e.recipients,
        'cc': e.cc,
        'bcc': e.bcc,
        'body_text': e.body_text,
        'body_html': e.body_html,
        'is_read': e.is_read,
        'is_sent': e.is_sent,
        'has_attachments': e.has_attachments,
        'folder': e.folder,
        'sent_by_user_email': User.query.get(e.sent_by_user_id).email if e.sent_by_user_id and User.query.get(e.sent_by_user_id) else None,
        'received_at': e.received_at.isoformat() if e.received_at else None,
        'sent_at': e.sent_at.isoformat() if e.sent_at else None,
        'created_at': e.created_at.isoformat() if e.created_at else None
    } for e in emails]


def export_email_permissions() -> List[Dict]:
    """Exportiert E-Mail-Berechtigungen."""
    permissions = EmailPermission.query.all()
    return [{
        'user_email': User.query.get(p.user_id).email if User.query.get(p.user_id) else None,
        'can_read': p.can_read,
        'can_send': p.can_send
    } for p in permissions]


def export_email_attachments() -> List[Dict]:
    """Exportiert E-Mail-Anhänge."""
    attachments = EmailAttachment.query.all()
    result = []
    for att in attachments:
        att_data = {
            'email_message_id': att.email.message_id if att.email else None,
            'filename': att.filename,
            'content_type': att.content_type,
            'size': att.size,
            'is_inline': att.is_inline,
            'created_at': att.created_at.isoformat() if att.created_at else None
        }
        # Dateiinhalt nur wenn vorhanden
        if att.file_path and os.path.exists(att.file_path):
            try:
                with open(att.file_path, 'rb') as f:
                    import base64
                    att_data['content_base64'] = base64.b64encode(f.read()).decode('utf-8')
            except Exception:
                pass
        elif att.content:
            import base64
            att_data['content_base64'] = base64.b64encode(att.content).decode('utf-8')
        result.append(att_data)
    return result


def export_chats() -> List[Dict]:
    """Exportiert Chats."""
    chats = Chat.query.all()
    return [{
        'name': c.name,
        'is_main_chat': c.is_main_chat,
        'is_direct_message': c.is_direct_message,
        'created_by_email': User.query.get(c.created_by).email if c.created_by and User.query.get(c.created_by) else None,
        'created_at': c.created_at.isoformat() if c.created_at else None,
        'updated_at': c.updated_at.isoformat() if c.updated_at else None
    } for c in chats]


def export_chat_messages() -> List[Dict]:
    """Exportiert Chat-Nachrichten."""
    messages = ChatMessage.query.all()
    return [{
        'chat_name': Chat.query.get(m.chat_id).name if Chat.query.get(m.chat_id) else None,
        'sender_email': User.query.get(m.sender_id).email if User.query.get(m.sender_id) else None,
        'content': m.content,
        'message_type': m.message_type,
        'media_url': m.media_url,
        'created_at': m.created_at.isoformat() if m.created_at else None,
        'edited_at': m.edited_at.isoformat() if m.edited_at else None,
        'is_deleted': m.is_deleted
    } for m in messages]


def export_chat_members() -> List[Dict]:
    """Exportiert Chat-Mitglieder."""
    members = ChatMember.query.all()
    return [{
        'chat_name': Chat.query.get(m.chat_id).name if Chat.query.get(m.chat_id) else None,
        'user_email': User.query.get(m.user_id).email if User.query.get(m.user_id) else None,
        'joined_at': m.joined_at.isoformat() if m.joined_at else None,
        'last_read_at': m.last_read_at.isoformat() if m.last_read_at else None
    } for m in members]


def export_calendar_events() -> List[Dict]:
    """Exportiert Kalender-Termine."""
    events = CalendarEvent.query.all()
    return [{
        'title': e.title,
        'description': e.description,
        'start_time': e.start_time.isoformat() if e.start_time else None,
        'end_time': e.end_time.isoformat() if e.end_time else None,
        'location': e.location,
        'created_by_email': User.query.get(e.created_by).email if User.query.get(e.created_by) else None,
        'created_at': e.created_at.isoformat() if e.created_at else None,
        'updated_at': e.updated_at.isoformat() if e.updated_at else None
    } for e in events]


def export_event_participants() -> List[Dict]:
    """Exportiert Event-Teilnehmer."""
    participants = EventParticipant.query.all()
    return [{
        'event_title': CalendarEvent.query.get(p.event_id).title if CalendarEvent.query.get(p.event_id) else None,
        'user_email': User.query.get(p.user_id).email if User.query.get(p.user_id) else None,
        'status': p.status,
        'responded_at': p.responded_at.isoformat() if p.responded_at else None
    } for p in participants]


def export_credentials() -> List[Dict]:
    """Exportiert Zugangsdaten (entschlüsselt)."""
    credentials = Credential.query.all()
    key = get_encryption_key()
    result = []
    for cred in credentials:
        try:
            decrypted_password = cred.get_password(key)
            result.append({
                'website_url': cred.website_url,
                'website_name': cred.website_name,
                'username': cred.username,
                'password': decrypted_password,  # Entschlüsselt
                'notes': cred.notes,
                'favicon_url': cred.favicon_url,
                'created_by_email': User.query.get(cred.created_by).email if User.query.get(cred.created_by) else None,
                'created_at': cred.created_at.isoformat() if cred.created_at else None,
                'updated_at': cred.updated_at.isoformat() if cred.updated_at else None
            })
        except Exception as e:
            # Wenn Entschlüsselung fehlschlägt, überspringen
            current_app.logger.error(f"Fehler beim Entschlüsseln von Credential {cred.id}: {str(e)}")
            continue
    return result


def export_folders() -> List[Dict]:
    """Exportiert Ordner."""
    folders = Folder.query.all()
    return [{
        'name': f.name,
        'parent_name': Folder.query.get(f.parent_id).name if f.parent_id and Folder.query.get(f.parent_id) else None,
        'created_by_email': User.query.get(f.created_by).email if User.query.get(f.created_by) else None,
        'is_dropbox': f.is_dropbox,
        'share_enabled': f.share_enabled,
        'share_name': f.share_name,
        'share_expires_at': f.share_expires_at.isoformat() if f.share_expires_at else None,
        'created_at': f.created_at.isoformat() if f.created_at else None,
        'updated_at': f.updated_at.isoformat() if f.updated_at else None
    } for f in folders]


def export_files() -> List[Dict]:
    """Exportiert Dateien."""
    files = File.query.all()
    result = []
    for file in files:
        file_data = {
            'name': file.name,
            'original_name': file.original_name,
            'folder_name': Folder.query.get(file.folder_id).name if file.folder_id and Folder.query.get(file.folder_id) else None,
            'uploaded_by_email': User.query.get(file.uploaded_by).email if User.query.get(file.uploaded_by) else None,
            'file_size': file.file_size,
            'mime_type': file.mime_type,
            'version_number': file.version_number,
            'is_current': file.is_current,
            'share_enabled': file.share_enabled,
            'share_name': file.share_name,
            'share_expires_at': file.share_expires_at.isoformat() if file.share_expires_at else None,
            'created_at': file.created_at.isoformat() if file.created_at else None,
            'updated_at': file.updated_at.isoformat() if file.updated_at else None
        }
        # Dateiinhalt hinzufügen wenn vorhanden
        if file.file_path and os.path.exists(file.file_path):
            try:
                with open(file.file_path, 'rb') as f:
                    import base64
                    file_data['content_base64'] = base64.b64encode(f.read()).decode('utf-8')
                    file_data['file_path'] = file.file_path
            except Exception as e:
                current_app.logger.error(f"Fehler beim Lesen von Datei {file.file_path}: {str(e)}")
        result.append(file_data)
    return result


def export_file_versions() -> List[Dict]:
    """Exportiert Datei-Versionen."""
    versions = FileVersion.query.all()
    result = []
    for v in versions:
        version_data = {
            'file_name': File.query.get(v.file_id).name if File.query.get(v.file_id) else None,
            'version_number': v.version_number,
            'file_size': v.file_size,
            'uploaded_by_email': User.query.get(v.uploaded_by).email if User.query.get(v.uploaded_by) else None,
            'created_at': v.created_at.isoformat() if v.created_at else None
        }
        # Dateiinhalt hinzufügen wenn vorhanden
        if v.file_path and os.path.exists(v.file_path):
            try:
                with open(v.file_path, 'rb') as f:
                    import base64
                    version_data['content_base64'] = base64.b64encode(f.read()).decode('utf-8')
                    version_data['file_path'] = v.file_path
            except Exception as e:
                current_app.logger.error(f"Fehler beim Lesen von Dateiversion {v.file_path}: {str(e)}")
        result.append(version_data)
    return result


def import_backup(file_path: str, categories: List[str]) -> Dict:
    """
    Importiert ein Backup der ausgewählten Kategorien.
    
    Args:
        file_path: Pfad zur Backup-Datei
        categories: Liste der zu importierenden Kategorien
    
    Returns:
        Dict mit Import-Ergebnissen
    """
    # Backup-Datei laden
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
    except Exception as e:
        return {'success': False, 'error': f'Fehler beim Lesen der Backup-Datei: {str(e)}'}
    
    # Version prüfen
    if backup_data.get('version') != BACKUP_VERSION:
        return {'success': False, 'error': f'Unsupported backup version: {backup_data.get("version")}'}
    
    # Import in Transaktion
    try:
        db.session.begin()
        
        results = {
            'success': True,
            'imported': [],
            'errors': []
        }
        
        # Einstellungen importieren
        if 'settings' in categories or 'all' in categories:
            if 'settings' in backup_data.get('data', {}):
                import_settings(backup_data['data']['settings'])
                results['imported'].append('settings')
            if 'whitelist' in backup_data.get('data', {}):
                import_whitelist(backup_data['data']['whitelist'])
                results['imported'].append('whitelist')
        
        # Benutzer importieren (muss zuerst sein wegen Foreign Keys)
        if 'users' in categories or 'all' in categories:
            if 'users' in backup_data.get('data', {}):
                user_map = import_users(backup_data['data']['users'])
                results['imported'].append('users')
            else:
                user_map = {}
            
            if 'notification_settings' in backup_data.get('data', {}):
                import_notification_settings(backup_data['data']['notification_settings'], user_map)
                results['imported'].append('notification_settings')
        
        # E-Mails importieren
        if 'emails' in categories or 'all' in categories:
            if 'emails' in backup_data.get('data', {}):
                email_map = import_emails(backup_data['data']['emails'], user_map)
                results['imported'].append('emails')
            else:
                email_map = {}
            
            if 'email_permissions' in backup_data.get('data', {}):
                import_email_permissions(backup_data['data']['email_permissions'], user_map)
                results['imported'].append('email_permissions')
            
            if 'email_attachments' in backup_data.get('data', {}):
                import_email_attachments(backup_data['data']['email_attachments'], email_map)
                results['imported'].append('email_attachments')
        
        # Chats importieren
        if 'chats' in categories or 'all' in categories:
            if 'chats' in backup_data.get('data', {}):
                chat_map = import_chats(backup_data['data']['chats'], user_map)
                results['imported'].append('chats')
            else:
                chat_map = {}
            
            if 'chat_messages' in backup_data.get('data', {}):
                import_chat_messages(backup_data['data']['chat_messages'], chat_map, user_map)
                results['imported'].append('chat_messages')
            
            if 'chat_members' in backup_data.get('data', {}):
                import_chat_members(backup_data['data']['chat_members'], chat_map, user_map)
                results['imported'].append('chat_members')
        
        # Termine importieren
        if 'appointments' in categories or 'all' in categories:
            if 'calendar_events' in backup_data.get('data', {}):
                event_map = import_calendar_events(backup_data['data']['calendar_events'], user_map)
                results['imported'].append('calendar_events')
            else:
                event_map = {}
            
            if 'event_participants' in backup_data.get('data', {}):
                import_event_participants(backup_data['data']['event_participants'], event_map, user_map)
                results['imported'].append('event_participants')
        
        # Zugangsdaten importieren
        if 'credentials' in categories or 'all' in categories:
            if 'credentials' in backup_data.get('data', {}):
                import_credentials(backup_data['data']['credentials'], user_map)
                results['imported'].append('credentials')
        
        # Dateien importieren
        if 'files' in categories or 'all' in categories:
            if 'folders' in backup_data.get('data', {}):
                folder_map = import_folders(backup_data['data']['folders'], user_map)
                results['imported'].append('folders')
            else:
                folder_map = {}
            
            if 'files' in backup_data.get('data', {}):
                import_files(backup_data['data']['files'], folder_map, user_map)
                results['imported'].append('files')
            
            if 'file_versions' in backup_data.get('data', {}):
                import_file_versions(backup_data['data']['file_versions'], user_map)
                results['imported'].append('file_versions')
        
        db.session.commit()
        return results
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Fehler beim Import: {str(e)}")
        return {'success': False, 'error': f'Fehler beim Import: {str(e)}'}


def import_settings(settings_data: List[Dict]):
    """Importiert System-Einstellungen."""
    for s_data in settings_data:
        existing = SystemSettings.query.filter_by(key=s_data['key']).first()
        if existing:
            existing.value = s_data['value']
            if 'description' in s_data:
                existing.description = s_data['description']
        else:
            setting = SystemSettings(
                key=s_data['key'],
                value=s_data['value'],
                description=s_data.get('description')
            )
            db.session.add(setting)


def import_whitelist(whitelist_data: List[Dict]):
    """Importiert Whitelist-Einträge."""
    for w_data in whitelist_data:
        existing = WhitelistEntry.query.filter_by(
            entry=w_data['entry'],
            entry_type=w_data['entry_type']
        ).first()
        if not existing:
            entry = WhitelistEntry(
                entry=w_data['entry'],
                entry_type=w_data['entry_type'],
                description=w_data.get('description'),
                is_active=w_data.get('is_active', True)
            )
            db.session.add(entry)


def import_users(users_data: List[Dict]) -> Dict[str, int]:
    """
    Importiert Benutzer und gibt ein Mapping von E-Mail zu neuer ID zurück.
    IDs werden neu generiert.
    """
    user_map = {}  # email -> neue_id
    
    for u_data in users_data:
        existing = User.query.filter_by(email=u_data['email']).first()
        if existing:
            # Aktualisiere bestehenden Benutzer
            existing.first_name = u_data['first_name']
            existing.last_name = u_data['last_name']
            existing.phone = u_data.get('phone')
            existing.is_active = u_data.get('is_active', False)
            existing.is_admin = u_data.get('is_admin', False)
            existing.is_email_confirmed = u_data.get('is_email_confirmed', False)
            existing.profile_picture = u_data.get('profile_picture')
            existing.accent_color = u_data.get('accent_color', '#0d6efd')
            existing.accent_gradient = u_data.get('accent_gradient')
            existing.dark_mode = u_data.get('dark_mode', False)
            existing.notifications_enabled = u_data.get('notifications_enabled', True)
            existing.chat_notifications = u_data.get('chat_notifications', True)
            existing.email_notifications = u_data.get('email_notifications', True)
            existing.can_borrow = u_data.get('can_borrow', True)
            # Passwort-Hash aktualisieren falls vorhanden
            if u_data.get('password_hash'):
                existing.password_hash = u_data['password_hash']
            user_map[u_data['email']] = existing.id
        else:
            # Neuer Benutzer (mit Passwort-Hash aus Backup)
            user = User(
                email=u_data['email'],
                password_hash=u_data.get('password_hash'),  # Passwort-Hash wird importiert
                first_name=u_data['first_name'],
                last_name=u_data['last_name'],
                phone=u_data.get('phone'),
                is_active=u_data.get('is_active', False),
                is_admin=u_data.get('is_admin', False),
                is_email_confirmed=u_data.get('is_email_confirmed', False),
                profile_picture=u_data.get('profile_picture'),
                accent_color=u_data.get('accent_color', '#0d6efd'),
                accent_gradient=u_data.get('accent_gradient'),
                dark_mode=u_data.get('dark_mode', False),
                notifications_enabled=u_data.get('notifications_enabled', True),
                chat_notifications=u_data.get('chat_notifications', True),
                email_notifications=u_data.get('email_notifications', True),
                can_borrow=u_data.get('can_borrow', True)
            )
            # Falls kein Passwort-Hash vorhanden, temporäres Passwort setzen
            if not user.password_hash:
                user.set_password('TEMPORARY_PASSWORD_RESET_REQUIRED')
            db.session.add(user)
            db.session.flush()  # Um die ID zu bekommen
            user_map[u_data['email']] = user.id
    
    return user_map


def import_notification_settings(settings_data: List[Dict], user_map: Dict[str, int]):
    """Importiert Notification-Einstellungen."""
    for s_data in settings_data:
        user_email = s_data.get('user_email')
        if not user_email or user_email not in user_map:
            continue
        
        user_id = user_map[user_email]
        existing = NotificationSettings.query.filter_by(user_id=user_id).first()
        if existing:
            existing.chat_notifications_enabled = s_data.get('chat_notifications_enabled', True)
            existing.file_notifications_enabled = s_data.get('file_notifications_enabled', True)
            existing.file_new_notifications = s_data.get('file_new_notifications', True)
            existing.file_modified_notifications = s_data.get('file_modified_notifications', True)
            existing.email_notifications_enabled = s_data.get('email_notifications_enabled', True)
            existing.calendar_notifications_enabled = s_data.get('calendar_notifications_enabled', True)
            existing.calendar_all_events = s_data.get('calendar_all_events', False)
            existing.calendar_participating_only = s_data.get('calendar_participating_only', True)
            existing.calendar_not_participating = s_data.get('calendar_not_participating', False)
            existing.calendar_no_response = s_data.get('calendar_no_response', False)
            existing.reminder_times = s_data.get('reminder_times')
        else:
            setting = NotificationSettings(
                user_id=user_id,
                chat_notifications_enabled=s_data.get('chat_notifications_enabled', True),
                file_notifications_enabled=s_data.get('file_notifications_enabled', True),
                file_new_notifications=s_data.get('file_new_notifications', True),
                file_modified_notifications=s_data.get('file_modified_notifications', True),
                email_notifications_enabled=s_data.get('email_notifications_enabled', True),
                calendar_notifications_enabled=s_data.get('calendar_notifications_enabled', True),
                calendar_all_events=s_data.get('calendar_all_events', False),
                calendar_participating_only=s_data.get('calendar_participating_only', True),
                calendar_not_participating=s_data.get('calendar_not_participating', False),
                calendar_no_response=s_data.get('calendar_no_response', False),
                reminder_times=s_data.get('reminder_times')
            )
            db.session.add(setting)


def import_emails(emails_data: List[Dict], user_map: Dict[str, int]) -> Dict[str, int]:
    """Importiert E-Mails und gibt ein Mapping von message_id zu neuer ID zurück."""
    email_map = {}  # message_id -> neue_id
    
    for e_data in emails_data:
        sent_by_user_id = None
        if e_data.get('sent_by_user_email'):
            sent_by_user_id = user_map.get(e_data['sent_by_user_email'])
        
        existing = None
        if e_data.get('message_id'):
            existing = EmailMessage.query.filter_by(message_id=e_data['message_id']).first()
        
        if existing:
            # Aktualisiere bestehende E-Mail
            existing.subject = e_data['subject']
            existing.sender = e_data['sender']
            existing.recipients = e_data['recipients']
            existing.cc = e_data.get('cc')
            existing.bcc = e_data.get('bcc')
            existing.body_text = e_data.get('body_text')
            existing.body_html = e_data.get('body_html')
            existing.is_read = e_data.get('is_read', False)
            existing.is_sent = e_data.get('is_sent', False)
            existing.has_attachments = e_data.get('has_attachments', False)
            existing.folder = e_data.get('folder', 'INBOX')
            existing.sent_by_user_id = sent_by_user_id
            if e_data.get('received_at'):
                existing.received_at = datetime.fromisoformat(e_data['received_at'])
            if e_data.get('sent_at'):
                existing.sent_at = datetime.fromisoformat(e_data['sent_at'])
            if e_data.get('message_id'):
                email_map[e_data['message_id']] = existing.id
        else:
            # Neue E-Mail
            email = EmailMessage(
                uid=e_data.get('uid'),
                message_id=e_data.get('message_id'),
                subject=e_data['subject'],
                sender=e_data['sender'],
                recipients=e_data['recipients'],
                cc=e_data.get('cc'),
                bcc=e_data.get('bcc'),
                body_text=e_data.get('body_text'),
                body_html=e_data.get('body_html'),
                is_read=e_data.get('is_read', False),
                is_sent=e_data.get('is_sent', False),
                has_attachments=e_data.get('has_attachments', False),
                folder=e_data.get('folder', 'INBOX'),
                sent_by_user_id=sent_by_user_id
            )
            if e_data.get('received_at'):
                email.received_at = datetime.fromisoformat(e_data['received_at'])
            if e_data.get('sent_at'):
                email.sent_at = datetime.fromisoformat(e_data['sent_at'])
            db.session.add(email)
            db.session.flush()
            if email.message_id:
                email_map[email.message_id] = email.id
    
    return email_map


def import_email_permissions(permissions_data: List[Dict], user_map: Dict[str, int]):
    """Importiert E-Mail-Berechtigungen."""
    for p_data in permissions_data:
        user_email = p_data.get('user_email')
        if not user_email or user_email not in user_map:
            continue
        
        user_id = user_map[user_email]
        existing = EmailPermission.query.filter_by(user_id=user_id).first()
        if existing:
            existing.can_read = p_data.get('can_read', True)
            existing.can_send = p_data.get('can_send', True)
        else:
            permission = EmailPermission(
                user_id=user_id,
                can_read=p_data.get('can_read', True),
                can_send=p_data.get('can_send', True)
            )
            db.session.add(permission)


def import_email_attachments(attachments_data: List[Dict], email_map: Dict[str, int]):
    """Importiert E-Mail-Anhänge."""
    for att_data in attachments_data:
        message_id = att_data.get('email_message_id')
        if not message_id or message_id not in email_map:
            continue
        
        email_id = email_map[message_id]
        
        attachment = EmailAttachment(
            email_id=email_id,
            filename=att_data['filename'],
            content_type=att_data['content_type'],
            size=att_data.get('size', 0),
            is_inline=att_data.get('is_inline', False)
        )
        
        # Dateiinhalt speichern wenn vorhanden
        if att_data.get('content_base64'):
            try:
                import base64
                content = base64.b64decode(att_data['content_base64'])
                
                # Speichere Datei im Upload-Verzeichnis
                from werkzeug.utils import secure_filename
                filename = secure_filename(att_data['filename'])
                timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                
                upload_dir = os.path.join(current_app.root_path, '..', current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'email_attachments')
                os.makedirs(upload_dir, exist_ok=True)
                file_path = os.path.join(upload_dir, filename)
                
                with open(file_path, 'wb') as f:
                    f.write(content)
                
                attachment.file_path = file_path
                attachment.is_large_file = True
            except Exception as e:
                current_app.logger.error(f"Fehler beim Speichern von E-Mail-Anhang {att_data['filename']}: {str(e)}")
                # Fallback: In Datenbank speichern
                attachment.content = content
        
        db.session.add(attachment)


def import_chats(chats_data: List[Dict], user_map: Dict[str, int]) -> Dict[str, int]:
    """Importiert Chats und gibt ein Mapping von Chat-Name zu neuer ID zurück."""
    chat_map = {}  # chat_name -> neue_id
    
    for c_data in chats_data:
        created_by_id = None
        if c_data.get('created_by_email'):
            created_by_id = user_map.get(c_data['created_by_email'])
        
        # Prüfe ob Chat mit gleichem Namen existiert
        existing = Chat.query.filter_by(name=c_data['name']).first()
        if existing:
            chat_map[c_data['name']] = existing.id
        else:
            chat = Chat(
                name=c_data['name'],
                is_main_chat=c_data.get('is_main_chat', False),
                is_direct_message=c_data.get('is_direct_message', False),
                created_by=created_by_id
            )
            db.session.add(chat)
            db.session.flush()
            chat_map[c_data['name']] = chat.id
    
    return chat_map


def import_chat_messages(messages_data: List[Dict], chat_map: Dict[str, int], user_map: Dict[str, int]):
    """Importiert Chat-Nachrichten."""
    for m_data in messages_data:
        chat_name = m_data.get('chat_name')
        sender_email = m_data.get('sender_email')
        
        if not chat_name or chat_name not in chat_map:
            continue
        if not sender_email or sender_email not in user_map:
            continue
        
        chat_id = chat_map[chat_name]
        sender_id = user_map[sender_email]
        
        message = ChatMessage(
            chat_id=chat_id,
            sender_id=sender_id,
            content=m_data.get('content'),
            message_type=m_data.get('message_type', 'text'),
            media_url=m_data.get('media_url'),
            is_deleted=m_data.get('is_deleted', False)
        )
        if m_data.get('created_at'):
            message.created_at = datetime.fromisoformat(m_data['created_at'])
        if m_data.get('edited_at'):
            message.edited_at = datetime.fromisoformat(m_data['edited_at'])
        db.session.add(message)


def import_chat_members(members_data: List[Dict], chat_map: Dict[str, int], user_map: Dict[str, int]):
    """Importiert Chat-Mitglieder."""
    for m_data in members_data:
        chat_name = m_data.get('chat_name')
        user_email = m_data.get('user_email')
        
        if not chat_name or chat_name not in chat_map:
            continue
        if not user_email or user_email not in user_map:
            continue
        
        chat_id = chat_map[chat_name]
        user_id = user_map[user_email]
        
        # Prüfe ob Mitgliedschaft bereits existiert
        existing = ChatMember.query.filter_by(chat_id=chat_id, user_id=user_id).first()
        if not existing:
            member = ChatMember(
                chat_id=chat_id,
                user_id=user_id
            )
            if m_data.get('joined_at'):
                member.joined_at = datetime.fromisoformat(m_data['joined_at'])
            if m_data.get('last_read_at'):
                member.last_read_at = datetime.fromisoformat(m_data['last_read_at'])
            db.session.add(member)


def import_calendar_events(events_data: List[Dict], user_map: Dict[str, int]) -> Dict[str, int]:
    """Importiert Kalender-Termine und gibt ein Mapping von Titel zu neuer ID zurück."""
    event_map = {}  # event_title -> neue_id
    
    for e_data in events_data:
        created_by_email = e_data.get('created_by_email')
        if not created_by_email or created_by_email not in user_map:
            continue
        
        created_by_id = user_map[created_by_email]
        
        event = CalendarEvent(
            title=e_data['title'],
            description=e_data.get('description'),
            start_time=datetime.fromisoformat(e_data['start_time']),
            end_time=datetime.fromisoformat(e_data['end_time']),
            location=e_data.get('location'),
            created_by=created_by_id
        )
        db.session.add(event)
        db.session.flush()
        event_map[e_data['title']] = event.id
    
    return event_map


def import_event_participants(participants_data: List[Dict], event_map: Dict[str, int], user_map: Dict[str, int]):
    """Importiert Event-Teilnehmer."""
    for p_data in participants_data:
        event_title = p_data.get('event_title')
        user_email = p_data.get('user_email')
        
        if not event_title or event_title not in event_map:
            continue
        if not user_email or user_email not in user_map:
            continue
        
        event_id = event_map[event_title]
        user_id = user_map[user_email]
        
        # Prüfe ob Teilnahme bereits existiert
        existing = EventParticipant.query.filter_by(event_id=event_id, user_id=user_id).first()
        if not existing:
            participant = EventParticipant(
                event_id=event_id,
                user_id=user_id,
                status=p_data.get('status', 'pending')
            )
            if p_data.get('responded_at'):
                participant.responded_at = datetime.fromisoformat(p_data['responded_at'])
            db.session.add(participant)


def import_credentials(credentials_data: List[Dict], user_map: Dict[str, int]):
    """Importiert Zugangsdaten (verschlüsselt neu)."""
    key = get_encryption_key()
    
    for c_data in credentials_data:
        created_by_email = c_data.get('created_by_email')
        if not created_by_email or created_by_email not in user_map:
            continue
        
        created_by_id = user_map[created_by_email]
        
        # Prüfe ob Credential bereits existiert
        existing = Credential.query.filter_by(
            website_url=c_data['website_url'],
            username=c_data['username'],
            created_by=created_by_id
        ).first()
        
        if existing:
            # Aktualisiere bestehendes Credential
            existing.website_name = c_data['website_name']
            existing.notes = c_data.get('notes')
            existing.favicon_url = c_data.get('favicon_url')
            if c_data.get('password'):
                existing.set_password(c_data['password'], key)
        else:
            # Neues Credential
            credential = Credential(
                website_url=c_data['website_url'],
                website_name=c_data['website_name'],
                username=c_data['username'],
                notes=c_data.get('notes'),
                favicon_url=c_data.get('favicon_url'),
                created_by=created_by_id
            )
            if c_data.get('password'):
                credential.set_password(c_data['password'], key)
            db.session.add(credential)


def import_folders(folders_data: List[Dict], user_map: Dict[str, int]) -> Dict[str, int]:
    """Importiert Ordner und gibt ein Mapping von Ordner-Name zu neuer ID zurück."""
    folder_map = {}  # folder_name -> neue_id
    
    # Sortiere nach Hierarchie (Root-Ordner zuerst)
    sorted_folders = sorted(folders_data, key=lambda x: (x.get('parent_name') is not None, x.get('name', '')))
    
    for f_data in sorted_folders:
        created_by_email = f_data.get('created_by_email')
        if not created_by_email or created_by_email not in user_map:
            continue
        
        created_by_id = user_map[created_by_email]
        parent_id = None
        if f_data.get('parent_name') and f_data['parent_name'] in folder_map:
            parent_id = folder_map[f_data['parent_name']]
        
        # Prüfe ob Ordner bereits existiert
        existing = Folder.query.filter_by(name=f_data['name'], created_by=created_by_id).first()
        if existing:
            folder_map[f_data['name']] = existing.id
        else:
            folder = Folder(
                name=f_data['name'],
                parent_id=parent_id,
                created_by=created_by_id,
                is_dropbox=f_data.get('is_dropbox', False),
                share_enabled=f_data.get('share_enabled', False),
                share_name=f_data.get('share_name')
            )
            if f_data.get('share_expires_at'):
                folder.share_expires_at = datetime.fromisoformat(f_data['share_expires_at'])
            db.session.add(folder)
            db.session.flush()
            folder_map[f_data['name']] = folder.id
    
    return folder_map


def import_files(files_data: List[Dict], folder_map: Dict[str, int], user_map: Dict[str, int]):
    """Importiert Dateien."""
    for f_data in files_data:
        uploaded_by_email = f_data.get('uploaded_by_email')
        if not uploaded_by_email or uploaded_by_email not in user_map:
            continue
        
        uploaded_by_id = user_map[uploaded_by_email]
        folder_id = None
        if f_data.get('folder_name') and f_data['folder_name'] in folder_map:
            folder_id = folder_map[f_data['folder_name']]
        
        # Prüfe ob Datei bereits existiert
        existing = File.query.filter_by(name=f_data['name'], uploaded_by=uploaded_by_id).first()
        
        if existing:
            # Aktualisiere bestehende Datei
            existing.original_name = f_data.get('original_name', f_data['name'])
            existing.folder_id = folder_id
            existing.file_size = f_data.get('file_size', 0)
            existing.mime_type = f_data.get('mime_type')
            existing.version_number = f_data.get('version_number', 1)
            existing.is_current = f_data.get('is_current', True)
            existing.share_enabled = f_data.get('share_enabled', False)
            existing.share_name = f_data.get('share_name')
            if f_data.get('share_expires_at'):
                existing.share_expires_at = datetime.fromisoformat(f_data['share_expires_at'])
        else:
            # Neue Datei
            file = File(
                name=f_data['name'],
                original_name=f_data.get('original_name', f_data['name']),
                folder_id=folder_id,
                uploaded_by=uploaded_by_id,
                file_size=f_data.get('file_size', 0),
                mime_type=f_data.get('mime_type'),
                version_number=f_data.get('version_number', 1),
                is_current=f_data.get('is_current', True),
                share_enabled=f_data.get('share_enabled', False),
                share_name=f_data.get('share_name')
            )
            if f_data.get('share_expires_at'):
                file.share_expires_at = datetime.fromisoformat(f_data['share_expires_at'])
            
            # Dateiinhalt speichern wenn vorhanden
            if f_data.get('content_base64'):
                try:
                    import base64
                    content = base64.b64decode(f_data['content_base64'])
                    # Speichere Datei im Upload-Verzeichnis
                    from werkzeug.utils import secure_filename
                    filename = secure_filename(file.name)
                    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                    filename = f"{timestamp}_{filename}"
                    
                    upload_dir = os.path.join(current_app.root_path, '..', current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'files')
                    os.makedirs(upload_dir, exist_ok=True)
                    file_path = os.path.join(upload_dir, filename)
                    
                    with open(file_path, 'wb') as f:
                        f.write(content)
                    
                    file.file_path = file_path
                except Exception as e:
                    current_app.logger.error(f"Fehler beim Speichern von Datei {file.name}: {str(e)}")
            
            db.session.add(file)


def import_file_versions(versions_data: List[Dict], user_map: Dict[str, int]):
    """Importiert Datei-Versionen."""
    for v_data in versions_data:
        uploaded_by_email = v_data.get('uploaded_by_email')
        if not uploaded_by_email or uploaded_by_email not in user_map:
            continue
        
        uploaded_by_id = user_map[uploaded_by_email]
        
        # Finde Datei nach Name
        file = File.query.filter_by(name=v_data.get('file_name')).first()
        if not file:
            continue
        
        # Prüfe ob Version bereits existiert
        existing = FileVersion.query.filter_by(file_id=file.id, version_number=v_data['version_number']).first()
        if existing:
            continue
        
        version = FileVersion(
            file_id=file.id,
            version_number=v_data['version_number'],
            file_size=v_data.get('file_size', 0),
            uploaded_by=uploaded_by_id
        )
        
        # Dateiinhalt speichern wenn vorhanden
        if v_data.get('content_base64'):
            try:
                import base64
                content = base64.b64decode(v_data['content_base64'])
                from werkzeug.utils import secure_filename
                filename = secure_filename(f"{file.name}_v{v_data['version_number']}")
                timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                
                upload_dir = os.path.join(current_app.root_path, '..', current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'files')
                os.makedirs(upload_dir, exist_ok=True)
                file_path = os.path.join(upload_dir, filename)
                
                with open(file_path, 'wb') as f:
                    f.write(content)
                
                version.file_path = file_path
            except Exception as e:
                current_app.logger.error(f"Fehler beim Speichern von Dateiversion: {str(e)}")
        
        db.session.add(version)

