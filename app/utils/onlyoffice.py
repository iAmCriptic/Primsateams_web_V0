"""
ONLYOFFICE helper functions and utilities.
"""
import os
from flask import current_app


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

