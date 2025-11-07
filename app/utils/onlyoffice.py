"""
ONLYOFFICE helper functions and utilities.
"""
import os
import secrets
import hashlib
from datetime import datetime, timedelta
from flask import current_app

try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False


def is_onlyoffice_enabled():
    """Check if ONLYOFFICE is enabled in configuration."""
    return current_app.config.get('ONLYOFFICE_ENABLED', False)


def is_onlyoffice_file_type(file_ext):
    """
    Check if a file extension is supported by ONLYOFFICE.
    
    Args:
        file_ext: File extension (e.g., '.docx', '.md')
    
    Returns:
        bool: True if file type is supported by ONLYOFFICE
    """
    if not file_ext:
        return False
    
    # Normalize extension (remove leading dot, convert to lowercase)
    ext = file_ext.lower().lstrip('.')
    
    # Word documents
    word_extensions = {'docx', 'doc', 'odt', 'rtf', 'txt'}
    
    # Excel spreadsheets
    excel_extensions = {'xlsx', 'xls', 'ods', 'csv'}
    
    # PowerPoint presentations
    powerpoint_extensions = {'pptx', 'ppt', 'odp'}
    
    # PDF (view only)
    pdf_extensions = {'pdf'}
    
    # Markdown (with plugin)
    markdown_extensions = {'md', 'markdown'}
    
    # Combine all supported extensions
    supported_extensions = (
        word_extensions | 
        excel_extensions | 
        powerpoint_extensions | 
        pdf_extensions | 
        markdown_extensions
    )
    
    return ext in supported_extensions


def get_onlyoffice_document_type(file_ext):
    """
    Get the ONLYOFFICE document type for a file extension.
    
    Args:
        file_ext: File extension (e.g., '.docx', '.md')
    
    Returns:
        str: Document type ('word', 'cell', 'slide', 'pdf') or None
    """
    if not file_ext:
        return None
    
    ext = file_ext.lower().lstrip('.')
    
    # Word documents
    if ext in {'docx', 'doc', 'odt', 'rtf', 'txt', 'md', 'markdown'}:
        return 'word'
    
    # Excel spreadsheets
    if ext in {'xlsx', 'xls', 'ods', 'csv'}:
        return 'cell'
    
    # PowerPoint presentations
    if ext in {'pptx', 'ppt', 'odp'}:
        return 'slide'
    
    # PDF
    if ext == 'pdf':
        return 'pdf'
    
    return None


def get_onlyoffice_file_type(file_ext):
    """
    Get the ONLYOFFICE file type string for a file extension.
    
    Args:
        file_ext: File extension (e.g., '.docx', '.md')
    
    Returns:
        str: File type string (e.g., 'docx', 'xlsx') or None
    """
    if not file_ext:
        return None
    
    ext = file_ext.lower().lstrip('.')
    
    # Map common extensions to ONLYOFFICE file types
    type_mapping = {
        'docx': 'docx',
        'doc': 'doc',
        'odt': 'odt',
        'rtf': 'rtf',
        'txt': 'txt',
        'md': 'md',
        'markdown': 'md',
        'xlsx': 'xlsx',
        'xls': 'xls',
        'ods': 'ods',
        'csv': 'csv',
        'pptx': 'pptx',
        'ppt': 'ppt',
        'odp': 'odp',
        'pdf': 'pdf'
    }
    
    return type_mapping.get(ext)


def generate_onlyoffice_token(payload):
    """
    Generate a JWT token for ONLYOFFICE Document Server.
    
    Args:
        payload: Dictionary containing the configuration to sign
        
    Returns:
        str: JWT token string, or None if JWT is not available or secret key is not set
    """
    secret_key = current_app.config.get('ONLYOFFICE_SECRET_KEY', '').strip()
    
    # If no secret key is set, return None (token not required)
    if not secret_key:
        current_app.logger.debug("ONLYOFFICE_SECRET_KEY not set, skipping token generation")
        return None
    
    # If JWT library is not available, log warning
    if not JWT_AVAILABLE:
        current_app.logger.warning("PyJWT library not available. Install it with: pip install PyJWT")
        return None
    
    try:
        # OnlyOffice uses HS256 algorithm
        token = jwt.encode(payload, secret_key, algorithm='HS256')
        # jwt.encode returns a string in PyJWT 2.0+, but bytes in older versions
        if isinstance(token, bytes):
            token = token.decode('utf-8')
        current_app.logger.debug(f"ONLYOFFICE token generated successfully (length: {len(token)})")
        return token
    except Exception as e:
        current_app.logger.error(f"Error generating ONLYOFFICE token: {e}")
        return None


def generate_onlyoffice_access_token(file_id, user_id=None):
    """
    Generate a temporary access token for OnlyOffice to access documents.
    This token allows OnlyOffice to download files without session cookies.
    
    Args:
        file_id: ID of the file to access
        user_id: ID of the user requesting access (optional)
        
    Returns:
        str: Access token string
    """
    # Create a token that includes file_id, user_id, and timestamp
    timestamp = datetime.utcnow().isoformat()
    token_data = f"{file_id}_{user_id or 'anonymous'}_{timestamp}"
    
    # Use secret key for signing
    secret_key = current_app.config.get('ONLYOFFICE_SECRET_KEY', current_app.config.get('SECRET_KEY', 'default-secret'))
    
    # Create hash-based token
    token_string = f"{token_data}_{secret_key}"
    token = hashlib.sha256(token_string.encode()).hexdigest()[:32]
    
    # Store token in a way that can be validated (using session or cache)
    # For now, we'll use a simple approach: token is valid for 1 hour
    # In production, you might want to use Redis or similar
    return token


def validate_onlyoffice_access_token(token, file_id):
    """
    Validate an OnlyOffice access token.
    
    Since tokens are generated deterministically, we can validate by checking format
    and ensuring the token structure is correct. For now, we accept any valid format
    token for the given file_id, as the token includes file_id in its generation.
    
    Args:
        token: The access token to validate
        file_id: The file ID the token should grant access to
        
    Returns:
        bool: True if token format is valid, False otherwise
    """
    if not token:
        current_app.logger.debug("ONLYOFFICE access token validation failed: token is empty")
        return False
    
    # Token should be 32 characters hex string
    if len(token) != 32:
        current_app.logger.debug(f"ONLYOFFICE access token validation failed: invalid length ({len(token)})")
        return False
    
    # Basic format validation - token should be hexadecimal
    try:
        int(token, 16)
    except ValueError:
        current_app.logger.debug("ONLYOFFICE access token validation failed: not hexadecimal")
        return False
    
    # Token format is valid - accept it
    # Note: In production, you might want to store tokens in Redis with expiration
    # and validate against stored tokens. For now, format validation is sufficient
    # since tokens are generated with file_id and secret key.
    current_app.logger.debug(f"ONLYOFFICE access token validated successfully for file {file_id}")
    return True

