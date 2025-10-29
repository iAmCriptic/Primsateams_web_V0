from app import create_app, db
from app.models import *
import os

# Create the Flask application
app = create_app(os.getenv('FLASK_ENV', 'development'))

# SSL Zertifikat Pfade
SSL_CERT_PATH = r'C:\Users\ermat\127.0.0.1.pem'
SSL_KEY_PATH = r'C:\Users\ermat\127.0.0.1-key.pem'


@app.shell_context_processor
def make_shell_context():
    """Make database and models available in Flask shell."""
    return {
        'db': db,
        'User': User,
        'Chat': Chat,
        'ChatMessage': ChatMessage,
        'ChatMember': ChatMember,
        'File': File,
        'FileVersion': FileVersion,
        'Folder': Folder,
        'CalendarEvent': CalendarEvent,
        'EventParticipant': EventParticipant,
        'EmailMessage': EmailMessage,
        'EmailPermission': EmailPermission,
        'EmailAttachment': EmailAttachment,
        'Credential': Credential,
        'Manual': Manual,
        'Canvas': Canvas,
        'CanvasTextField': CanvasTextField,
        'SystemSettings': SystemSettings,
        'WhitelistEntry': WhitelistEntry,
        'NotificationSettings': NotificationSettings,
        'ChatNotificationSettings': ChatNotificationSettings,
        'PushSubscription': PushSubscription,
        'NotificationLog': NotificationLog,
    }


if __name__ == '__main__':
    # Prüfe ob SSL-Zertifikate existieren
    ssl_context = None
    if os.path.exists(SSL_CERT_PATH) and os.path.exists(SSL_KEY_PATH):
        ssl_context = (SSL_CERT_PATH, SSL_KEY_PATH)
        print(f"SSL-Zertifikate gefunden. Starte HTTPS-Server auf https://127.0.0.1:5000")
    else:
        print(f"SSL-Zertifikate nicht gefunden. Starte HTTP-Server auf http://0.0.0.0:5000")
        print(f"Erwartete Pfade: {SSL_CERT_PATH}, {SSL_KEY_PATH}")
    
    app.run(
        host='127.0.0.1' if ssl_context else '0.0.0.0',
        port=5000,
        debug=True,
        ssl_context=ssl_context
    )



