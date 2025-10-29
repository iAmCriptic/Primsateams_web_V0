#!/usr/bin/env python3
"""
Migration script to add is_large_file column to email_attachments table.
This allows storing large attachments on disk instead of in the database.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import text

def migrate_large_attachments():
    """Add is_large_file column to email_attachments table."""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if column already exists
            result = db.session.execute(text("""
                SELECT COUNT(*) as count 
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'email_attachments' 
                AND COLUMN_NAME = 'is_large_file'
            """))
            
            if result.fetchone()[0] == 0:
                # Add the column
                db.session.execute(text("""
                    ALTER TABLE email_attachments 
                    ADD COLUMN is_large_file BOOLEAN DEFAULT FALSE NOT NULL
                """))
                db.session.commit()
                print("[OK] Added is_large_file column to email_attachments table")
            else:
                print("[INFO] Column is_large_file already exists")
            
            # Create attachments directory
            upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
            attachments_dir = os.path.join(upload_folder, 'attachments')
            os.makedirs(attachments_dir, exist_ok=True)
            print(f"[OK] Created attachments directory: {attachments_dir}")
            
        except Exception as e:
            print(f"[ERROR] Migration failed: {e}")
            db.session.rollback()
            return False
    
    return True

if __name__ == '__main__':
    success = migrate_large_attachments()
    if success:
        print("[SUCCESS] Migration completed successfully!")
    else:
        print("[FAILED] Migration failed!")
        sys.exit(1)
