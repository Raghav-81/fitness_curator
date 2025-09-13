"""
Utility functions for the workout video search system.
"""

import re
import logging
from typing import List, Set, Dict, Any
from pathlib import Path
from .config import IngestionConfig

# Set up logging
logger = logging.getLogger(__name__)

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
    for ext in IngestionConfig.SUPPORTED_EXTENSIONS:
        if title_lower.endswith(ext):
            title_lower = title_lower[:-len(ext)]
    
    # Split by common separators and clean
    # Handle patterns like: "Arms- Tricep DB Overhead", "RB- Bicep Curls", etc.
    keywords = []
    
    # Split by various delimiters
    parts = re.split(r'[-_\s\(\)]+', title_lower)
    
    # Filter and clean parts
    for part in parts:
        part = part.strip()
        if len(part) >= IngestionConfig.MIN_KEYWORD_LENGTH:
            # Remove special characters but keep alphanumeric
            clean_part = re.sub(r'[^a-zA-Z0-9]', '', part)
            if clean_part:
                keywords.append(clean_part)
    
    # Remove category prefixes if requested
    if remove_category_prefixes:
        keywords = [kw for kw in keywords if kw not in IngestionConfig.CATEGORY_STOPWORDS]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_keywords = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            unique_keywords.append(kw)
    
    return unique_keywords

def normalize_category(category: str) -> str:
    """
    Normalize category names for consistency.
    
    Args:
        category: Raw category name
    
    Returns:
        Normalized category name
    """
    if not category:
        return "Other"
    
    # Basic normalization
    normalized = category.strip()
    
    # Handle common variations
    category_mappings = {
        'cardio + hiit + functional + body weight': 'Cardio & Functional',
        'rehab + recovery': 'Rehab & Recovery',
        'shoulder workouts': 'Shoulders',
        'back workouts': 'Back',
        'chest workouts': 'Chest',
        'core workouts': 'Core',
        'leg workouts': 'Legs',
        'mobility routine': 'Mobility'
    }
    
    return category_mappings.get(normalized.lower(), normalized)

def validate_video_title(title: str) -> bool:
    """
    Validate if a video title is acceptable.
    
    Args:
        title: The video title to validate
    
    Returns:
        True if valid, False otherwise
    """
    if not title or not title.strip():
        return False
    
    # Check minimum length
    if len(title.strip()) < 3:
        return False
    
    # Check for suspicious patterns
    suspicious_patterns = [
        r'^test',
        r'^example',
        r'^sample',
        r'^\d+$',  # Just numbers
    ]
    
    title_lower = title.lower()
    for pattern in suspicious_patterns:
        if re.match(pattern, title_lower):
            return False
    
    return True

def clean_filename(filename: str) -> str:
    """
    Clean filename for safe storage.
    
    Args:
        filename: Original filename
    
    Returns:
        Cleaned filename
    """
    # Remove or replace unsafe characters
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove excessive whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # Ensure reasonable length
    if len(cleaned) > 255:
        name, ext = os.path.splitext(cleaned)
        cleaned = name[:255-len(ext)] + ext
    
    return cleaned

def create_search_document(title: str, keywords: List[str], category: str) -> str:
    """
    Create a searchable document string from video metadata.
    
    Args:
        title: Video title
        keywords: List of keywords
        category: Video category
    
    Returns:
        Combined document string for search indexing
    """
    # Combine all searchable text
    document_parts = [
        title.lower(),
        ' '.join(keywords),
        category.lower()
    ]
    
    return ' '.join(part for part in document_parts if part)

def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Calculate simple text similarity using basic metrics.
    
    Args:
        text1: First text string
        text2: Second text string
    
    Returns:
        Similarity score between 0 and 1
    """
    if not text1 or not text2:
        return 0.0
    
    # Convert to lowercase and split into words
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    # Calculate Jaccard similarity
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    return intersection / union if union > 0 else 0.0

def extract_equipment_from_title(title: str) -> List[str]:
    """
    Extract equipment mentioned in video title.
    
    Args:
        title: Video title
    
    Returns:
        List of equipment identified
    """
    equipment_patterns = {
        'dumbbell': ['db', 'dumbbell', 'dumbell'],
        'barbell': ['bb', 'barbell'],
        'resistance_band': ['rb', 'resistance band', 'band'],
        'machine': ['machine'],
        'cable': ['cable'],
        'kettlebell': ['kettle bell', 'kettlebell'],
        'bodyweight': ['body weight', 'bodyweight', 'bw'],
        'ez_bar': ['ez bar', 'ezbar'],
        'medicine_ball': ['medicine ball', 'med ball'],
        'trx': ['trx'],
        'bosu': ['bosu'],
        'stability_ball': ['stability ball', 'exercise ball']
    }
    
    title_lower = title.lower()
    equipment = []
    
    for equipment_name, patterns in equipment_patterns.items():
        for pattern in patterns:
            if pattern in title_lower:
                equipment.append(equipment_name.replace('_', ' ').title())
                break
    
    return list(set(equipment))  # Remove duplicates

def format_search_results(results: List[Dict[str, Any]], max_title_length: int = 50) -> str:
    """
    Format search results for display.
    
    Args:
        results: List of search results
        max_title_length: Maximum title length for display
    
    Returns:
        Formatted string representation
    """
    if not results:
        return "No results found."
    
    output_lines = []
    for i, result in enumerate(results, 1):
        video = result.get('video', {})
        title = video.get('title', 'Unknown')
        category = video.get('category', 'Unknown')
        score = result.get('score', 0.0)
        
        # Truncate title if too long
        if len(title) > max_title_length:
            title = title[:max_title_length-3] + '...'
        
        line = f"{i:2d}. {title:<{max_title_length}} | {category:<15} | Score: {score:.3f}"
        output_lines.append(line)
    
    return '\n'.join(output_lines)

def get_file_size(filepath: str) -> int:
    """
    Get file size in bytes.
    
    Args:
        filepath: Path to the file
    
    Returns:
        File size in bytes, or 0 if file doesn't exist
    """
    try:
        return Path(filepath).stat().st_size
    except (OSError, FileNotFoundError):
        return 0

def create_abbreviation_map() -> Dict[str, str]:
    """
    Create a mapping of common fitness abbreviations to full terms.
    
    Returns:
        Dictionary mapping abbreviations to full terms
    """
    return {
        'db': 'dumbbell',
        'bb': 'barbell',
        'rb': 'resistance band',
        'ez': 'ez bar',
        'bw': 'bodyweight',
        'hiit': 'high intensity interval training',
        'trx': 'suspension trainer',
        'hr': 'heart rate',
        'reps': 'repetitions',
        'max': 'maximum',
        'min': 'minimum',
        'lbs': 'pounds',
        'kg': 'kilograms'
    }

def expand_abbreviations(text: str) -> str:
    """
    Expand common abbreviations in text.
    
    Args:
        text: Input text with potential abbreviations
    
    Returns:
        Text with abbreviations expanded
    """
    abbrev_map = create_abbreviation_map()
    words = text.lower().split()
    
    expanded_words = []
    for word in words:
        # Remove punctuation for matching
        clean_word = re.sub(r'[^a-zA-Z0-9]', '', word)
        expanded = abbrev_map.get(clean_word, word)
        expanded_words.append(expanded)
    
    return ' '.join(expanded_words)

def normalize_text(text: str) -> str:
    """
    Normalize text for consistent searching.
    """
    if not text:
        return ""
    
    # Convert to lowercase and remove extra whitespace
    normalized = re.sub(r'\s+', ' ', text.lower().strip())
    
    # Remove punctuation except hyphens and apostrophes
    normalized = re.sub(r'[^\w\s\-\']', ' ', normalized)
    
    # Remove extra spaces
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized