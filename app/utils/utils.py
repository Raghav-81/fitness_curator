"""Utility functions for the Fitness Curator system."""

import re
import logging
import string
from typing import List, Set, Dict, Any
from pathlib import Path

# Set up logging
logger = logging.getLogger(__name__)

# Common fitness equipment list
COMMON_EQUIPMENT = [
    'dumbbell', 'db', 'barbell', 'bb', 'kettlebell', 'kb', 'resistance band', 'rb',
    'mat', 'ball', 'bench', 'cable', 'machine', 'weight', 'rope', 'strap', 'box',
    'plate', 'rack', 'band', 'medicine ball', 'foam roller', 'pull-up bar'
]

# Common workout prefixes to strip
PREFIX_PATTERNS = [
    r'^\d+\.\s*',  # Remove numbering like "1. "
    r'^[A-Z]{1,3}\d*[-:]\s*',  # Handle patterns like: "AB-" or "A1:"
    r'^\w+[-:]\s*',  # Handle patterns like: "Arms- " or "Legs: "
]

def extract_keywords(title: str, remove_category_prefixes: bool = True) -> List[str]:
    """
    Extract keywords from a video title for better searchability.
    
    Args:
        title: The video title to process
        remove_category_prefixes: Whether to remove common category prefixes
    
    Returns:
        List of extracted keywords
    """
    if not title:
        return []
    
    # Convert to lowercase for processing
    title_lower = title.lower()
    
    # Remove file extensions
    for ext in [".mp4", ".mov", ".avi", ".wmv"]:
        if title_lower.endswith(ext):
            title_lower = title_lower[:-len(ext)]
    
    # Split by common separators and clean
    # Handle patterns like: "Arms- Tricep DB Overhead", "RB- Bicep Curls", etc.
    keywords = []
    
    # Split by various delimiters
    for part in re.split(r'[\s;,_\-\+\|/\\]+', title_lower):
        # Clean up the part
        part = part.strip(string.punctuation + string.whitespace)
        
        if part and len(part) > 1:  # Only keep non-trivial words
            keywords.append(part)
    
    # Remove common prefixes if requested
    if remove_category_prefixes:
        cleaned_title = title_lower
        for pattern in PREFIX_PATTERNS:
            cleaned_title = re.sub(pattern, '', cleaned_title)
        
        # Add keywords from the cleaned title
        for part in re.split(r'[\s;,_\-\+\|/\\]+', cleaned_title):
            part = part.strip(string.punctuation + string.whitespace)
            if part and len(part) > 1 and part not in keywords:
                keywords.append(part)
    
    return keywords

def normalize_text(text: str) -> str:
    """
    Normalize text for consistent searching.
    
    Args:
        text: The text to normalize
    
    Returns:
        Normalized text
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove punctuation and extra whitespace
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def normalize_category(category: str) -> str:
    """
    Normalize category names for consistency.
    
    Args:
        category: Raw category name
    
    Returns:
        Normalized category name
    """
    if not category:
        return "Uncategorized"
    
    # Lowercase and strip
    norm_cat = category.lower().strip()
    
    # Map common variations to standard categories
    category_mapping = {
        'ab': 'core', 'abs': 'core', 'core': 'core',
        'arm': 'arms', 'arms': 'arms', 'bicep': 'arms', 'tricep': 'arms',
        'back': 'back', 'lats': 'back',
        'chest': 'chest', 'pec': 'chest', 'pecs': 'chest',
        'leg': 'legs', 'legs': 'legs', 'quad': 'legs', 'hamstring': 'legs', 'calf': 'legs',
        'shoulder': 'shoulders', 'shoulders': 'shoulders', 'delt': 'shoulders',
        'cardio': 'cardio', 'hiit': 'cardio', 'conditioning': 'cardio',
        'full body': 'full body', 'fullbody': 'full body', 'total body': 'full body',
        'stretch': 'recovery', 'mobility': 'recovery', 'recovery': 'recovery'
    }
    
    # Try to match the normalized category with our standard categories
    for key, value in category_mapping.items():
        if key in norm_cat:
            return value.title()
    
    # If no match, capitalize the first letter of each word
    return ' '.join(word.capitalize() for word in norm_cat.split())

def extract_equipment_from_title(title: str) -> List[str]:
    """
    Extract equipment mentioned in video title.
    
    Args:
        title: Video title
    
    Returns:
        List of equipment identified
    """
    if not title:
        return []
    
    title_lower = title.lower()
    found_equipment = []
    
    # Check for common equipment abbreviations and full names
    for equipment in COMMON_EQUIPMENT:
        # Check for the equipment as a standalone word
        pattern = r'\b' + re.escape(equipment) + r'\b'
        if re.search(pattern, title_lower):
            # Convert abbreviations to full names
            if equipment == 'db':
                found_equipment.append('dumbbell')
            elif equipment == 'bb':
                found_equipment.append('barbell')
            elif equipment == 'kb':
                found_equipment.append('kettlebell')
            elif equipment == 'rb':
                found_equipment.append('resistance band')
            else:
                found_equipment.append(equipment)
    
    return list(set(found_equipment))  # Remove duplicates
