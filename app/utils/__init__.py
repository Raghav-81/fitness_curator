"""Utils package for the Fitness Curator system."""

# Import and expose utility functions properly
from .utils import (
    extract_keywords,
    normalize_text,
    normalize_category,
    extract_equipment_from_title
)

# For convenient imports
__all__ = [
    'extract_keywords',
    'normalize_text',
    'normalize_category',
    'extract_equipment_from_title'
]
