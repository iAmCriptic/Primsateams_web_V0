from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, send_file, Response
from flask_login import login_required, current_user
from app import db, mail
from app.models.email import EmailMessage, EmailPermission, EmailAttachment, EmailFolder
from app.models.settings import SystemSettings
from app.utils.notifications import send_email_notification
from flask_mail import Message
from datetime import datetime, timedelta
import imaplib
import email as email_module
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import threading
import time
import logging
import io
import sqlalchemy
from markupsafe import Markup

email_bp = Blueprint('email', __name__)


def decode_header_field(field):
    """Decode email header field properly with multiple fallback strategies."""
    if not field:
        return ''
    
    try:
        from email.header import decode_header
        decoded_parts = decode_header(field)
        decoded_string = ''
        
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                if encoding:
                    try:
                        decoded_string += part.decode(encoding, errors='ignore')
                        continue
                    except (UnicodeDecodeError, LookupError):
                        pass
                
                for enc in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
                    try:
                        decoded_string += part.decode(enc, errors='ignore')
                        break
                    except (UnicodeDecodeError, LookupError):
                        continue
            else:
                decoded_string += str(part)
        
        return decoded_string.strip()
    except Exception as e:
        logging.error(f"Error decoding header field: {e}")
        return str(field) if field else ''


def connect_imap():
    """Connect to IMAP server."""
    try:
        imap_server = current_app.config.get('IMAP_SERVER')
        imap_port = current_app.config.get('IMAP_PORT', 993)
        imap_use_ssl = current_app.config.get('IMAP_USE_SSL', True)
        username = current_app.config.get('MAIL_USERNAME')
        password = current_app.config.get('MAIL_PASSWORD')
        
        if not all([imap_server, username, password]):
            raise Exception("IMAP configuration missing - check .env file")
        
        if imap_use_ssl:
            mail = imaplib.IMAP4_SSL(imap_server, imap_port)
        else:
            mail = imaplib.IMAP4(imap_server, imap_port)
        
        mail.login(username, password)
        mail.select('INBOX')
        
        return mail
    except Exception as e:
        error_msg = str(e).encode('ascii', errors='replace').decode('ascii')
        logging.error(f"IMAP connection failed: {error_msg}")
        return None


def sync_imap_folders():
    """Sync IMAP folders from server to database."""
    mail_conn = connect_imap()
    if not mail_conn:
        return False, "IMAP-Verbindung fehlgeschlagen"
    
    try:
        status, folders = mail_conn.list()
        if status != 'OK':
            return False, "Ordner-Liste konnte nicht abgerufen werden"
        
        synced_folders = []
        skipped_folders = []
        
        logging.info(f"Processing {len(folders)} folders from IMAP server")
        
        for folder_info in folders:
            try:
                folder_str = folder_info.decode('utf-8')
                parts = folder_str.split('"')
                if len(parts) >= 3:
                    folder_name = parts[-2]
                    logging.debug(f"Found folder: '{folder_name}'")
                    
                    # Filter out invalid folder names
                    if not folder_name or folder_name.strip() == '' or folder_name == '/' or folder_name.strip() == '/':
                        logging.debug(f"Skipping invalid folder name: '{folder_name}'")
                        continue
                    
                    # Check if folder already exists
                    existing_folder = EmailFolder.query.filter_by(name=folder_name).first()
                    if existing_folder:
                        logging.debug(f"Folder '{folder_name}' already exists in database")
                        synced_folders.append(folder_name)
                        continue
                    
                    # Create new folder
                    new_folder = EmailFolder(
                        name=folder_name,
                        display_name=folder_name,
                        is_system_folder=folder_name in ['INBOX', 'Drafts', 'Sent', 'Archive', 'Trash', 'Spam']
                    )
                    db.session.add(new_folder)
                    synced_folders.append(folder_name)
                    logging.info(f"Added new folder: '{folder_name}'")
                else:
                    logging.warning(f"Could not parse folder info: {folder_str}")
                    skipped_folders.append(folder_str)
            except Exception as e:
                logging.error(f"Error processing folder info: {e}")
                skipped_folders.append(str(folder_info))
                continue
        
        # Remove invalid folders from database if they exist
        invalid_folders = EmailFolder.query.filter(
            EmailFolder.name.in_(['', '/'])
        ).all()
        for invalid_folder in invalid_folders:
            logging.info(f"Removing invalid folder from database: '{invalid_folder.name}'")
            db.session.delete(invalid_folder)
        
        db.session.commit()
        
        result_msg = f"{len(synced_folders)} Ordner synchronisiert"
        if skipped_folders:
            result_msg += f", {len(skipped_folders)} übersprungen"
        
        logging.info(f"Folder sync completed: {result_msg}")
        return True, result_msg
        
    except Exception as e:
        logging.error(f"Error syncing folders: {e}")
        db.session.rollback()
        return False, f"Fehler beim Synchronisieren der Ordner: {str(e)}"
    finally:
        try:
            mail_conn.close()
            mail_conn.logout()
        except:
            pass


def sync_emails_from_folder(folder_name):
    """Sync emails from a specific IMAP folder with bidirectional support."""
    mail_conn = connect_imap()
    if not mail_conn:
        return False, "IMAP-Verbindung fehlgeschlagen"
    
    # Statistiken für strukturierte Ausgabe
    stats = {
        'new_emails': 0,
        'updated_emails': 0,
        'moved_emails': 0,
        'deleted_emails': 0,
        'skipped_emails': 0,
        'errors': 0
    }
    
    try:
        # Select the folder - use quoted folder name for folders with special characters
        try:
            status, messages = mail_conn.select(folder_name)
            if status != 'OK':
                # Try with quoted folder name
                try:
                    status, messages = mail_conn.select(f'"{folder_name}"')
                except:
                    pass
                if status != 'OK':
                    logging.error(f"IMAP folder selection failed for '{folder_name}': {messages}")
                    return False, f"Ordner '{folder_name}' konnte nicht geöffnet werden: {messages[0].decode() if messages else 'Unbekannter Fehler'}"
        except Exception as e:
            logging.error(f"Exception while selecting folder '{folder_name}': {e}")
            return False, f"Fehler beim Öffnen des Ordners '{folder_name}': {str(e)}"
        
        # Get message count
        try:
            message_count = int(messages[0].decode().split()[1])
            logging.info(f"Folder '{folder_name}' contains {message_count} messages")
        except:
            message_count = 0
        
        status, messages = mail_conn.search(None, 'ALL')
        if status != 'OK':
            logging.error(f"IMAP search failed for folder '{folder_name}': {messages}")
            return False, f"E-Mail-Suche in Ordner '{folder_name}' fehlgeschlagen: {messages[0].decode() if messages else 'Unbekannter Fehler'}"
        
        email_ids = messages[0].split()
        logging.info(f"Found {len(email_ids)} email IDs in folder '{folder_name}'")
        
        if len(email_ids) == 0:
            logging.info(f"No emails found in folder '{folder_name}'")
            mail_conn.close()
            mail_conn.logout()
            return True, f"Ordner '{folder_name}': Keine E-Mails vorhanden"
        
        synced_count = 0
        moved_count = 0
        deleted_count = 0
        
        current_imap_uids = set()
        for email_id in email_ids:
            current_imap_uids.add(email_id.decode())
        
        existing_emails = EmailMessage.query.filter_by(folder=folder_name).all()
        for email_obj in existing_emails:
            if email_obj.imap_uid and email_obj.imap_uid not in current_imap_uids:
                if email_obj.is_deleted_imap:
                    db.session.delete(email_obj)
                    stats['deleted_emails'] += 1
                else:
                    other_folder_email = EmailMessage.query.filter_by(
                        message_id=email_obj.message_id
                    ).filter(EmailMessage.folder != folder_name).first()
                    
                    if other_folder_email:
                        db.session.delete(email_obj)
                        stats['moved_emails'] += 1
                    else:
                        email_obj.is_deleted_imap = True
                        email_obj.last_imap_sync = datetime.utcnow()
                        stats['deleted_emails'] += 1
        
        max_emails = 200 if folder_name not in ['INBOX', 'Sent', 'Drafts', 'Trash', 'Spam', 'Archive'] else 50
        emails_to_process = email_ids[-max_emails:] if len(email_ids) > max_emails else email_ids
        logging.info(f"Processing {len(emails_to_process)} emails from folder '{folder_name}' (max: {max_emails})")
        
        for idx, email_id in enumerate(emails_to_process, 1):
            try:
                if idx % 10 == 0:
                    logging.debug(f"Processing email {idx}/{len(emails_to_process)} from folder '{folder_name}'")
                
                status, msg_data = mail_conn.fetch(email_id, '(RFC822)')
                if status != 'OK':
                    logging.warning(f"Failed to fetch email {email_id.decode()} from folder '{folder_name}': {msg_data}")
                    stats['errors'] += 1
                    continue
                
                raw_email = msg_data[0][1]
                email_msg = email_module.message_from_bytes(raw_email)
                
                sender_raw = email_msg.get('From', '')
                sender = decode_header_field(sender_raw)
                
                recipient_raw = email_msg.get('To', '')
                recipient = decode_header_field(recipient_raw)
                
                cc_raw = email_msg.get('Cc', '')
                cc = decode_header_field(cc_raw)
                
                subject_raw = email_msg.get('Subject', '')
                subject = decode_header_field(subject_raw)
                
                message_id = email_msg.get('Message-ID', '')
                if not message_id:
                    # Generate a unique message ID if none exists
                    message_id = f"<{folder_name}_{email_id.decode()}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}@local>"
                
                # Get IMAP UID
                imap_uid_str = email_id.decode()
                
                # Parse date
                date_str = email_msg.get('Date', '')
                received_at = datetime.utcnow()
                if date_str:
                    try:
                        from email.utils import parsedate_to_datetime
                        received_at = parsedate_to_datetime(date_str)
                    except:
                        pass
                
                # Check if email with same imap_uid already exists in this specific folder
                existing_in_folder = EmailMessage.query.filter_by(
                    imap_uid=imap_uid_str,
                    folder=folder_name
                ).first()
                
                if existing_in_folder:
                    # Update existing email in this folder
                    try:
                        existing_in_folder.last_imap_sync = datetime.utcnow()
                        existing_in_folder.is_deleted_imap = False
                        stats['updated_emails'] += 1
                        db.session.commit()
                        continue
                    except Exception as update_error:
                        if "MySQL server has gone away" in str(update_error) or "ConnectionResetError" in str(update_error):
                            logging.warning("Database connection lost during update, attempting to reconnect...")
                            db.session.rollback()
                            db.session.close()
                            db.session = db.create_scoped_session()
                            existing_in_folder = EmailMessage.query.filter_by(
                                imap_uid=imap_uid_str,
                                folder=folder_name
                            ).first()
                            if existing_in_folder:
                                existing_in_folder.last_imap_sync = datetime.utcnow()
                                existing_in_folder.is_deleted_imap = False
                                stats['updated_emails'] += 1
                                db.session.commit()
                                logging.info("Database reconnection successful for update")
                            continue
                        else:
                            raise update_error
                
                # If we reach here, the email doesn't exist in the database yet
                
                body_text = ""
                body_html = ""
                has_attachments = False
                attachments_data = []
                
                if email_msg.is_multipart():
                    for part in email_msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = part.get('Content-Disposition', '')
                        
                        if ('attachment' in content_disposition or 'inline' in content_disposition) and not content_type.startswith('text/'):
                            has_attachments = True
                            
                            # Process attachment - wrap in try-except to ensure email is still saved if attachment fails
                            try:
                                filename = part.get_filename()
                                if not filename:
                                    # Generate filename from content type
                                    extension = content_type.split('/')[-1] if '/' in content_type else 'bin'
                                    filename = f"attachment_{len(attachments_data)}.{extension}"
                                
                                # Decode filename if needed
                                if filename:
                                    try:
                                        from email.header import decode_header
                                        decoded_filename = decode_header(filename)
                                        if decoded_filename and decoded_filename[0][0]:
                                            filename = decoded_filename[0][0]
                                    except:
                                        pass  # Use original filename if decoding fails
                                
                                # Try to get content - handle large files gracefully
                                try:
                                    # For very large files, check size first if possible
                                    payload = None
                                    try:
                                        payload = part.get_payload(decode=True)
                                    except Exception as decode_error:
                                        # If decoding fails (e.g., memory error), log and continue
                                        logging.error(f"Failed to decode attachment '{filename}': {decode_error}")
                                        has_attachments = True  # Mark as having attachments even if we can't process it
                                        continue
                                    
                                    if payload:
                                        attachment_size = len(payload)
                                        
                                        # Log all attachments, especially large ones
                                        if attachment_size > 1 * 1024 * 1024:  # > 1MB
                                            logging.info(f"Processing large attachment: '{filename}' ({attachment_size / (1024*1024):.2f} MB) - saving to disk")
                                        else:
                                            logging.debug(f"Processing attachment: '{filename}' ({attachment_size / (1024*1024):.2f} MB) - saving to database")
                                        
                                        # Check if file should be stored on disk (>1MB) or in database (≤1MB)
                                        # Using 1MB to avoid MySQL max_allowed_packet errors
                                        max_db_size = 1 * 1024 * 1024  # 1MB limit for database storage
                                        
                                        logging.info(f"Attachment '{filename}': {attachment_size / (1024*1024):.2f} MB, max_db_size: {max_db_size / (1024*1024):.2f} MB, will store on: {'disk' if attachment_size > max_db_size else 'database'}")
                                        
                                        if attachment_size > max_db_size:
                                            # Store large file on disk
                                            import os
                                            
                                            # Create attachments directory if it doesn't exist
                                            attachments_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'attachments')
                                            os.makedirs(attachments_dir, exist_ok=True)
                                            
                                            # Generate unique filename
                                            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                                            safe_filename = "".join(c for c in filename if c.isalnum() or c in '._- ')
                                            file_path = os.path.join(attachments_dir, f"{timestamp}_{safe_filename}")
                                            
                                            # Write file to disk
                                            try:
                                                with open(file_path, 'wb') as f:
                                                    f.write(payload)
                                                logging.info(f"Large attachment saved to disk: {file_path}")
                                                
                                                attachments_data.append({
                                                    'filename': filename,
                                                    'content_type': content_type,
                                                    'file_path': file_path,
                                                    'is_large_file': True
                                                })
                                            except Exception as file_error:
                                                logging.error(f"Failed to save large attachment to disk: {file_error}")
                                                # Continue without this attachment
                                                continue
                                        else:
                                            # Store in database
                                            attachments_data.append({
                                                'filename': filename,
                                                'content_type': content_type,
                                                'content': payload,
                                                'is_large_file': False
                                            })
                                
                                except Exception as e:
                                    logging.error(f"Error processing attachment '{filename}': {e}")
                                    # Continue processing other attachments
                                    continue
                                    
                        elif content_type == "text/plain":
                            try:
                                payload = part.get_payload(decode=True)
                                if payload:
                                    import chardet
                                    detected = chardet.detect(payload)
                                    encoding = detected.get('encoding', 'utf-8')
                                    decoded_text = payload.decode(encoding, errors='ignore')
                                    if decoded_text.strip():
                                        body_text = decoded_text
                            except Exception as e:
                                logging.error(f"Error processing text part: {e}")
                                pass
                        elif content_type == "text/html":
                            try:
                                payload = part.get_payload(decode=True)
                                if payload:
                                    import chardet
                                    detected = chardet.detect(payload)
                                    encoding = detected.get('encoding', 'utf-8')
                                    decoded_html = payload.decode(encoding, errors='ignore')
                                    if decoded_html.strip():
                                        # Append to existing HTML content if multipart
                                        if body_html:
                                            body_html += "\n" + decoded_html
                                        else:
                                            body_html = decoded_html
                            except Exception as e:
                                logging.error(f"Error processing HTML part: {e}")
                                pass
                else:
                    content_type = email_msg.get_content_type()
                    try:
                        payload = email_msg.get_payload(decode=True)
                        if payload:
                            import chardet
                            detected = chardet.detect(payload)
                            encoding = detected.get('encoding', 'utf-8')
                            decoded_content = payload.decode(encoding, errors='ignore')
                            
                            if content_type == "text/html":
                                if decoded_content.strip():
                                    body_html = decoded_content
                            else:
                                if decoded_content.strip():
                                    body_text = decoded_content
                    except Exception as e:
                        logging.error(f"Error processing single part email: {e}")
                        pass
                
                # Create email record
                try:
                    email_record = EmailMessage(
                        message_id=message_id,
                        sender=sender,
                        recipient=recipient,
                        recipients=recipient,
                        cc=cc,
                        subject=subject,
                        body_text=body_text,
                        body_html=body_html,
                        received_at=received_at,
                        folder=folder_name,
                        imap_uid=imap_uid_str,
                        has_attachments=has_attachments,
                        last_imap_sync=datetime.utcnow(),
                        is_deleted_imap=False
                    )
                    
                    db.session.add(email_record)
                    db.session.flush()  # Get the email ID
                    
                    # Add attachments
                    for att_data in attachments_data:
                        attachment = EmailAttachment(
                            email_id=email_record.id,
                            filename=att_data['filename'],
                            content_type=att_data['content_type'],
                            content=att_data.get('content'),
                            file_path=att_data.get('file_path'),
                            is_large_file=att_data.get('is_large_file', False)
                        )
                        db.session.add(attachment)
                    
                    db.session.commit()
                    stats['new_emails'] += 1
                    synced_count += 1
                    
                    if synced_count % 10 == 0:
                        logging.info(f"Synced {synced_count} emails from folder '{folder_name}'")
                        
                except Exception as e:
                    db.session.rollback()
                    if "MySQL server has gone away" in str(e) or "ConnectionResetError" in str(e):
                        logging.warning("Database connection lost during email creation, attempting to reconnect...")
                        db.session.close()
                        db.session = db.create_scoped_session()
                        stats['errors'] += 1
                        continue
                    elif "Duplicate entry" in str(e):
                        # Email already exists - this can happen with concurrent syncs
                        logging.debug(f"Email already exists (duplicate entry): {message_id}")
                        stats['skipped_emails'] += 1
                        continue
                    else:
                        logging.error(f"Error creating email record: {e}")
                        stats['errors'] += 1
                        continue
                        
            except Exception as e:
                logging.error(f"Error processing email {email_id.decode()}: {e}")
                stats['errors'] += 1
                continue
        
        # Clean up deleted emails
        db.session.commit()
        
        result_msg = f"Ordner '{folder_name}': {stats['new_emails']} neue, {stats['updated_emails']} aktualisierte, {stats['moved_emails']} verschobene, {stats['deleted_emails']} gelöschte E-Mails"
        if stats['errors'] > 0:
            result_msg += f", {stats['errors']} Fehler"
        if stats['skipped_emails'] > 0:
            result_msg += f", {stats['skipped_emails']} übersprungen"
        
        logging.info(f"Folder sync completed: {result_msg}")
        return True, result_msg
        
    except Exception as e:
        logging.error(f"Error syncing folder '{folder_name}': {e}")
        db.session.rollback()
        return False, f"Fehler beim Synchronisieren des Ordners '{folder_name}': {str(e)}"
    finally:
        try:
            mail_conn.close()
            mail_conn.logout()
        except:
            pass


def sync_all_emails():
    """Sync emails from all folders."""
    folders = EmailFolder.query.all()
    if not folders:
        return False, "Keine Ordner gefunden"
    
    total_synced = 0
    folder_results = []
    
    for folder in folders:
        logging.info(f"Syncing folder: '{folder.name}' ({folder.display_name})")
        success, message = sync_emails_from_folder(folder.name)
        if success:
            import re
            match = re.search(r'(\d+) E-Mails', message)
            if match:
                count = int(match.group(1))
                total_synced += count
            folder_results.append(f"{folder.display_name}: {message}")
        else:
            logging.warning(f"Failed to sync folder '{folder.name}': {message}")
            folder_results.append(f"{folder.display_name}: Fehler - {message}")
    
    if total_synced > 0:
        return True, f"{total_synced} E-Mails aus {len(folders)} Ordnern synchronisiert"
    else:
        return False, "Keine E-Mails synchronisiert"


def check_email_permission(permission_type='read'):
    """Check if current user has email permissions."""
    perm = EmailPermission.query.filter_by(user_id=current_user.id).first()
    if not perm:
        return False
    return perm.can_read if permission_type == 'read' else perm.can_send


@email_bp.route('/')
@login_required
def index():
    """Email inbox with folder support."""
    if not check_email_permission('read'):
        flash('Sie haben keine Berechtigung, E-Mails zu lesen.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    current_folder = request.args.get('folder', 'INBOX')
    emails = EmailMessage.query.filter_by(folder=current_folder).order_by(EmailMessage.received_at.desc()).all()
    
    # Custom folder ordering: Standard folders first, then custom folders
    all_folders = EmailFolder.query.all()
    
    # Define standard folder order
    standard_folder_order = ['INBOX', 'Drafts', 'Sent', 'Archive', 'Trash', 'Spam']
    standard_folder_names = ['Posteingang', 'Entwürfe', 'Gesendet', 'Archiv', 'Papierkorb', 'Spam']
    
    # Separate standard and custom folders
    standard_folders = []
    custom_folders = []
    
    for folder in all_folders:
        if folder.name in standard_folder_order:
            # Find the index in standard order
            try:
                index = standard_folder_order.index(folder.name)
                standard_folders.append((index, folder))
            except ValueError:
                custom_folders.append(folder)
        else:
            custom_folders.append(folder)
    
    # Sort standard folders by predefined order
    standard_folders.sort(key=lambda x: x[0])
    standard_folders = [folder for _, folder in standard_folders]
    
    # Sort custom folders alphabetically
    custom_folders.sort(key=lambda x: x.display_name)
    
    # Combine: standard folders first, then custom folders
    ordered_folders = standard_folders + custom_folders
    
    return render_template('email/index.html', 
                         emails=emails, 
                         folders=ordered_folders, 
                         current_folder=current_folder,
                         standard_folder_names=standard_folder_names)


@email_bp.route('/folder/<folder_name>')
@login_required
def folder_view(folder_name):
    """View emails in a specific folder."""
    if not check_email_permission('read'):
        flash('Sie haben keine Berechtigung, E-Mails zu lesen.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Decode URL-encoded folder name
    import urllib.parse
    folder_name = urllib.parse.unquote(folder_name)
    
    # Check for invalid folder names
    if not folder_name or folder_name.strip() == '' or folder_name == '/':
        flash('Ungültiger Ordnername.', 'warning')
        return redirect(url_for('email.index'))
    
    # Check if folder exists
    folder = EmailFolder.query.filter_by(name=folder_name).first()
    if not folder:
        flash(f'Ordner "{folder_name}" nicht gefunden.', 'warning')
        return redirect(url_for('email.index'))
    
    emails = EmailMessage.query.filter_by(folder=folder_name).order_by(EmailMessage.received_at.desc()).all()
    
    # Custom folder ordering: Standard folders first, then custom folders
    all_folders = EmailFolder.query.all()
    
    # Define standard folder order
    standard_folder_order = ['INBOX', 'Drafts', 'Sent', 'Archive', 'Trash', 'Spam']
    standard_folder_names = ['Posteingang', 'Entwürfe', 'Gesendet', 'Archiv', 'Papierkorb', 'Spam']
    
    # Separate standard and custom folders
    standard_folders = []
    custom_folders = []
    
    for folder in all_folders:
        if folder.name in standard_folder_order:
            # Find the index in standard order
            try:
                index = standard_folder_order.index(folder.name)
                standard_folders.append((index, folder))
            except ValueError:
                custom_folders.append(folder)
        else:
            custom_folders.append(folder)
    
    # Sort standard folders by predefined order
    standard_folders.sort(key=lambda x: x[0])
    standard_folders = [folder for _, folder in standard_folders]
    
    # Sort custom folders alphabetically
    custom_folders.sort(key=lambda x: x.display_name)
    
    # Combine: standard folders first, then custom folders
    ordered_folders = standard_folders + custom_folders
    
    return render_template('email/index.html', 
                         emails=emails, 
                         folders=ordered_folders, 
                         current_folder=folder_name,
                         standard_folder_names=standard_folder_names)


@email_bp.route('/view/<int:email_id>')
@login_required
def view_email(email_id):
    """View a specific email."""
    if not check_email_permission('read'):
        flash('Sie haben keine Berechtigung, E-Mails zu lesen.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    email = EmailMessage.query.get_or_404(email_id)
    
    # Clean up problematic characters in HTML content
    if email.body_html:
        import re
        # Remove Microsoft Word artifacts
        email.body_html = re.sub(r'<o:p\s*></o:p>', '', email.body_html)
        email.body_html = re.sub(r'<o:p\s*/>', '', email.body_html)
        
        # Make links secure
        email.body_html = re.sub(r'<a\s+([^>]*?)href="([^"]*?)"([^>]*?)>', 
                                r'<a \1href="\2" target="_blank" rel="noopener noreferrer" \3>', 
                                email.body_html)
        
        # Handle inline images - replace cid: references with data URLs or placeholders
        def replace_cid_images(match):
            cid = match.group(1)
            # Look for the attachment with this content-id
            for attachment in email.attachments:
                if attachment.content_id == cid:
                    if attachment.is_large_file and attachment.file_path:
                        # For large files, we can't easily create a data URL
                        return f'<img src="{url_for("email.download_attachment", attachment_id=attachment.id)}" alt="Inline Image" style="max-width: 100%; height: auto;">'
                    elif attachment.content:
                        # Create data URL for small attachments
                        import base64
                        data_url = f"data:{attachment.content_type};base64,{base64.b64encode(attachment.content).decode()}"
                        return f'<img src="{data_url}" alt="Inline Image" style="max-width: 100%; height: auto;">'
            # If no attachment found, return a placeholder
            return f'<div style="border: 1px dashed #ccc; padding: 10px; text-align: center; color: #666;">Inline Image: {cid}</div>'
        
        email.body_html = re.sub(r'<img[^>]*src="cid:([^"]*)"[^>]*>', replace_cid_images, email.body_html)
    
    return render_template('email/view.html', email=email)


@email_bp.route('/download/<int:attachment_id>')
@login_required
def download_attachment(attachment_id):
    """Download an email attachment."""
    if not check_email_permission('read'):
        flash('Sie haben keine Berechtigung, E-Mails zu lesen.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    attachment = EmailAttachment.query.get_or_404(attachment_id)
    
    # Check if user has access to the email
    email = attachment.email
    if not email:
        flash('E-Mail nicht gefunden.', 'error')
        return redirect(url_for('email.index'))
    
    try:
        if attachment.is_large_file and attachment.file_path:
            # Large file stored on disk
            import os
            if os.path.exists(attachment.file_path):
                # Log large file downloads
                file_size = os.path.getsize(attachment.file_path)
                if file_size > 1024 * 1024:  # > 1MB
                    logging.info(f"Downloading large file: {attachment.filename} ({file_size / (1024*1024):.2f} MB)")
                
                def generate():
                    with open(attachment.file_path, 'rb') as f:
                        while True:
                            data = f.read(8192)  # 8KB chunks
                            if not data:
                                break
                            yield data
                
                response = Response(generate(), mimetype=attachment.content_type)
                response.headers['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{urllib.parse.quote(attachment.filename)}'
                response.headers['Content-Length'] = str(file_size)
                response.headers['Accept-Ranges'] = 'bytes'
                return response
            else:
                flash('Datei nicht gefunden.', 'error')
                return redirect(url_for('email.view_email', email_id=email.id))
        else:
            # Small file stored in database
            content = attachment.get_content()
            if content:
                # Log large file downloads
                file_size = len(content)
                if file_size > 1024 * 1024:  # > 1MB
                    logging.info(f"Downloading large file from DB: {attachment.filename} ({file_size / (1024*1024):.2f} MB)")
                
                return send_file(
                    io.BytesIO(content),
                    as_attachment=True,
                    download_name=attachment.filename,
                    mimetype=attachment.content_type
                )
            else:
                flash('Anhang-Inhalt nicht verfügbar.', 'error')
                return redirect(url_for('email.view_email', email_id=email.id))
                
    except Exception as e:
        logging.error(f"Error downloading attachment {attachment_id}: {e}")
        flash('Fehler beim Herunterladen des Anhangs.', 'error')
        return redirect(url_for('email.view_email', email_id=email.id))


@email_bp.route('/compose', methods=['GET', 'POST'])
@login_required
def compose():
    """Compose and send emails."""
    if not check_email_permission('send'):
        flash('Sie haben keine Berechtigung, E-Mails zu senden.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        try:
            to = request.form.get('to', '').strip()
            cc = request.form.get('cc', '').strip()
            subject = request.form.get('subject', '').strip()
            body = request.form.get('body', '').strip()
            in_reply_to = request.form.get('in_reply_to', '').strip()
            references = request.form.get('references', '').strip()
            forward_attachment_ids = request.form.get('forward_attachment_ids', '').strip()
            
            if not to:
                flash('Empfänger ist erforderlich.', 'error')
                return render_template('email/compose.html')
            
            # Get formatted sender from config (with optional display name)
            from config import get_formatted_sender
            sender = get_formatted_sender()
            if not sender:
                flash('Absender nicht konfiguriert.', 'error')
                return render_template('email/compose.html')
            
            # Create message
            msg = Message(
                subject=subject,
                recipients=[to],
                cc=[cc] if cc else None,
                sender=sender,
                body=body
            )
            
            # Threading headers (Flask-Mail: use extra_headers)
            thread_headers = {}
            if in_reply_to:
                thread_headers['In-Reply-To'] = in_reply_to
            if references:
                thread_headers['References'] = references
            if thread_headers:
                # merge with any existing extra headers
                existing = getattr(msg, 'extra_headers', None)
                if existing and isinstance(existing, dict):
                    existing.update(thread_headers)
                    msg.extra_headers = existing
                else:
                    msg.extra_headers = thread_headers
            
            # Handle forwarded attachments
            if forward_attachment_ids:
                attachment_ids = [int(id.strip()) for id in forward_attachment_ids.split(',') if id.strip()]
                for attachment_id in attachment_ids:
                    try:
                        attachment = EmailAttachment.query.get(attachment_id)
                        if attachment:
                            if attachment.is_large_file and attachment.file_path:
                                # Large file from disk
                                import os
                                if os.path.exists(attachment.file_path):
                                    with open(attachment.file_path, 'rb') as f:
                                        msg.attach(attachment.filename, attachment.content_type, f.read())
                            elif attachment.content:
                                # Small file from database
                                msg.attach(attachment.filename, attachment.content_type, attachment.content)
                    except Exception as e:
                        logging.error(f"Error attaching file {attachment_id}: {e}")
                        continue
            
            # Send email
            mail.send(msg)
            
            # Save to database
            email_record = EmailMessage(
                message_id=f"<{datetime.utcnow().strftime('%Y%m%d%H%M%S')}@local>",
                sender=sender,
                recipient=to,
                recipients=to,
                cc=cc,
                subject=subject,
                body_text=body,
                body_html=body,
                sent_at=datetime.utcnow(),
                folder='Sent',
                has_attachments=bool(forward_attachment_ids),
                last_imap_sync=datetime.utcnow(),
                is_deleted_imap=False
            )
            
            db.session.add(email_record)
            db.session.commit()
            
            flash('E-Mail erfolgreich gesendet.', 'success')
            return redirect(url_for('email.index'))
            
        except Exception as e:
            logging.error(f"Error sending email: {e}")
            flash(f'Fehler beim Senden der E-Mail: {str(e)}', 'error')
            return render_template('email/compose.html')
    
    # Handle reply/forward parameters
    reply_to_id = request.args.get('reply_to_id')
    reply_all_id = request.args.get('reply_all_id')
    forward_id = request.args.get('forward_id')
    
    context = {}
    
    if reply_to_id:
        try:
            email = EmailMessage.query.get(int(reply_to_id))
            if email:
                context = build_reply_context(email, 'reply')
        except:
            pass
    elif reply_all_id:
        try:
            email = EmailMessage.query.get(int(reply_all_id))
            if email:
                context = build_reply_context(email, 'reply_all')
        except:
            pass
    elif forward_id:
        try:
            email = EmailMessage.query.get(int(forward_id))
            if email:
                context = build_forward_context(email, include_attachments=True)
        except:
            pass
    
    return render_template('email/compose.html', **context)


@email_bp.route('/reply/<int:email_id>')
@login_required
def reply(email_id: int):
    """Reply to an email."""
    if not check_email_permission('send'):
        flash('Sie haben keine Berechtigung, E-Mails zu senden.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    email = EmailMessage.query.get_or_404(email_id)
    context = build_reply_context(email, 'reply')
    return render_template('email/compose.html', **context)


@email_bp.route('/reply-all/<int:email_id>')
@login_required
def reply_all(email_id: int):
    """Reply to all recipients of an email."""
    if not check_email_permission('send'):
        flash('Sie haben keine Berechtigung, E-Mails zu senden.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    email = EmailMessage.query.get_or_404(email_id)
    context = build_reply_context(email, 'reply_all')
    return render_template('email/compose.html', **context)


@email_bp.route('/forward/<int:email_id>')
@login_required
def forward(email_id: int):
    """Forward an email."""
    if not check_email_permission('send'):
        flash('Sie haben keine Berechtigung, E-Mails zu senden.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    email = EmailMessage.query.get_or_404(email_id)
    context = build_forward_context(email, include_attachments=True)
    return render_template('email/compose.html', **context)


@email_bp.route('/sync')
@login_required
def sync_emails():
    """Manual email sync."""
    if not check_email_permission('read'):
        flash('Sie haben keine Berechtigung, E-Mails zu synchronisieren.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    try:
        # Sync folders first
        folder_success, folder_message = sync_imap_folders()
        if not folder_success:
            flash(f'Ordner-Synchronisation fehlgeschlagen: {folder_message}', 'error')
            return redirect(url_for('email.index'))
        
        # Sync emails
        success, message = sync_all_emails()
        if success:
            flash(f'E-Mail-Synchronisation erfolgreich: {message}', 'success')
        else:
            flash(f'E-Mail-Synchronisation fehlgeschlagen: {message}', 'error')
            
    except Exception as e:
        logging.error(f"Error during manual sync: {e}")
        flash(f'Fehler bei der Synchronisation: {str(e)}', 'error')
    
    return redirect(url_for('email.index'))


def normalize_addresses(addresses):
    """Normalize email addresses - handle both string and list inputs."""
    if isinstance(addresses, str):
        if not addresses.strip():
            return []
        # Split by comma and clean up
        addresses = [addr.strip() for addr in addresses.split(',') if addr.strip()]
    
    if not isinstance(addresses, list):
        return []
    
    # Remove duplicates while preserving order
    seen = set()
    result = []
    for addr in addresses:
        key = addr.lower().strip()
        if key and key not in seen:
            seen.add(key)
            result.append(addr.strip())
    return result


def prefix_subject(subject, prefix):
    """Add prefix to subject if not already present."""
    if not subject:
        return f"{prefix}: "
    
    subject_lower = subject.lower()
    if subject_lower.startswith(f"{prefix.lower()}: "):
        return subject
    
    return f"{prefix}: {subject}"


def build_plain_quote_header(email_msg: EmailMessage) -> str:
    sent_at = email_msg.received_at or email_msg.sent_at or datetime.utcnow()
    header = (
        f"Von: {email_msg.sender}\n"
        f"An: {email_msg.recipients or ''}\n"
        f"{'CC: ' + email_msg.cc + '\n' if email_msg.cc else ''}"
        f"Datum: {sent_at.strftime('%d.%m.%Y %H:%M')}\n"
        f"Betreff: {email_msg.subject}\n\n"
    )
    return header


def quote_plain(email_msg: EmailMessage) -> str:
    # Use text content if available, otherwise convert HTML to plain text
    body = email_msg.body_text or ''
    if not body and email_msg.body_html:
        # Simple HTML to text conversion
        import re
        body = re.sub(r'<[^>]+>', '', email_msg.body_html)
        body = body.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
    
    header = build_plain_quote_header(email_msg)
    
    # Quote each line with >
    quoted_lines = []
    quoted_lines.append(header)
    for line in body.split('\n'):
        quoted_lines.append(f"> {line}")
    
    return '\n'.join(quoted_lines)


def build_reply_context(email_msg: EmailMessage, mode: str):
    # recipients
    to_list = []
    # Absender der Originalmail als primärer Empfänger
    if email_msg.sender:
        to_list += normalize_addresses(email_msg.sender)
    cc_list = []
    if mode == 'reply_all':
        to_list += normalize_addresses(email_msg.recipients)
        cc_list += normalize_addresses(email_msg.cc)
        # Eigene Adresse entfernen
        own = (current_user.email or '').lower()
        to_list = [a for a in to_list if a.lower() != own]
        cc_list = [a for a in cc_list if a.lower() != own]
    # unique again
    to_list = normalize_addresses(to_list)
    cc_list = normalize_addresses(cc_list)

    subject = prefix_subject(email_msg.subject or '', 'Re')
    body_prefill = quote_plain(email_msg)
    return {
        'to': ', '.join(to_list),
        'cc': ', '.join(cc_list),
        'subject': subject,
        'body': body_prefill,
        'in_reply_to': email_msg.message_id or '',
        'references': email_msg.message_id or ''
    }


def build_forward_context(email_msg: EmailMessage, include_attachments: bool):
    subject = prefix_subject(email_msg.subject or '', 'Fwd')
    body_prefill = quote_plain(email_msg)
    attachment_ids = []
    if include_attachments:
        attachment_ids = [str(a.id) for a in email_msg.attachments]
    return {
        'to': '',
        'cc': '',
        'subject': subject,
        'body': body_prefill,
        'forward_attachment_ids': ','.join(attachment_ids)
    }


# Auto-sync function for background thread
def auto_sync_emails():
    """Background function to sync emails periodically."""
    while True:
        try:
            with current_app.app_context():
                logging.info("Starting auto-sync...")
                success, message = sync_all_emails()
                if success:
                    logging.info(f"Auto-sync completed: {message}")
                else:
                    logging.error(f"Auto-sync failed: {message}")
        except Exception as e:
            logging.error(f"Auto-sync error: {e}")
        
        # Wait 5 minutes before next sync
        time.sleep(300)


# Start auto-sync in background thread
def start_auto_sync():
    """Start the auto-sync background thread."""
    sync_thread = threading.Thread(target=auto_sync_emails, daemon=True)
    sync_thread.start()
    logging.info("Auto-sync thread started")
