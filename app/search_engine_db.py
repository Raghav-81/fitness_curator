"""
Database-adapted search engine for the Workout Video Search System.
Integrates with SQLAlchemy database models for efficient search operations.
"""

import logging
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
import pickle
import json
from pathlib import Path

# Core search functionality
from .database import DatabaseManager, WorkoutVideoModel

# Import search components with fallbacks
try:
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("scikit-learn not available. TF-IDF search will be disabled.")

try:
    from fuzzywuzzy import fuzz
    FUZZ_AVAILABLE = True
except ImportError:
    FUZZ_AVAILABLE = False
    logging.warning("fuzzywuzzy not available. Fuzzy search will be disabled.")

from .utils import extract_keywords, normalize_text

logger = logging.getLogger(__name__)

@dataclass
class DatabaseSearchResult:
    """Search result with database video model."""
    video: WorkoutVideoModel
    score: float
    method: str
    match_details: Dict[str, Any]

class DatabaseSearchEngine:
    """Database-integrated search engine with multiple search strategies."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.tfidf_vectorizer = None
        self.tfidf_matrix = None
        self.video_texts = []
        self.video_ids = []
        self._cache_dir = Path(__file__).parent.parent / "data" / "cache"
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize search indices
        self.refresh_indices()
    
    def refresh_indices(self):
        """Refresh search indices from database."""
        try:
            logger.info("Refreshing search indices from database...")
            
            # Get all videos from database
            videos = self.db_manager.get_all_videos()
            
            if not videos:
                logger.warning("No videos found in database")
                return
            
            # Prepare text data for TF-IDF
            self.video_texts = []
            self.video_ids = []
            
            for video in videos:
                # Combine searchable text fields
                text_parts = [
                    video.title or "",
                    video.category or "",
                    video.description or "",
                    " ".join(video.tags or []),
                    " ".join(video.keywords or []),
                    " ".join(video.equipment_needed or [])
                ]
                
                combined_text = " ".join(text_parts).strip()
                self.video_texts.append(combined_text)
                self.video_ids.append(video.id)
            
            # Build TF-IDF matrix if scikit-learn is available
            if SKLEARN_AVAILABLE and self.video_texts:
                self.tfidf_vectorizer = TfidfVectorizer(
                    stop_words='english',
                    max_features=5000,
                    ngram_range=(1, 2),
                    min_df=1,
                    max_df=0.95
                )
                self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.video_texts)
                logger.info(f"TF-IDF matrix created with shape: {self.tfidf_matrix.shape}")
            
            logger.info(f"Search indices refreshed for {len(videos)} videos")
            
        except Exception as e:
            logger.error(f"Error refreshing indices: {e}")
    
    def search(self, 
               query: str, 
               category_filter: Optional[str] = None,
               equipment_filter: Optional[List[str]] = None,
               difficulty_filter: Optional[str] = None,
               top_k: int = 10,
               min_score: float = 0.0) -> List[DatabaseSearchResult]:
        """
        Perform multi-strategy search combining TF-IDF, keyword, and fuzzy matching.
        """
        if not query.strip():
            return []
        
        try:
            # Get all videos (with basic filtering)
            videos = self._get_filtered_videos(category_filter, equipment_filter, difficulty_filter)
            
            if not videos:
                return []
            
            # Perform different search strategies
            tfidf_results = self._tfidf_search(query, videos, top_k * 2)
            keyword_results = self._keyword_search(query, videos, top_k * 2)
            fuzzy_results = self._fuzzy_search(query, videos, top_k * 2)
            
            # Combine and rank results
            combined_results = self._combine_results(
                tfidf_results, keyword_results, fuzzy_results
            )
            
            # Filter by minimum score and return top results
            filtered_results = [r for r in combined_results if r.score >= min_score]
            return filtered_results[:top_k]
            
        except Exception as e:
            logger.error(f"Error in search: {e}")
            return []
    
    def _get_filtered_videos(self, 
                            category_filter: Optional[str] = None,
                            equipment_filter: Optional[List[str]] = None,
                            difficulty_filter: Optional[str] = None) -> List[WorkoutVideoModel]:
        """Get videos with basic database filtering."""
        try:
            session = self.db_manager.get_session()
            query = session.query(WorkoutVideoModel)
            
            if category_filter:
                query = query.filter(WorkoutVideoModel.category.ilike(f"%{category_filter}%"))
            
            if difficulty_filter:
                query = query.filter(WorkoutVideoModel.difficulty_level.ilike(f"%{difficulty_filter}%"))
            
            videos = query.all()
            
            # Filter by equipment (JSON field requires client-side filtering)
            if equipment_filter:
                filtered_videos = []
                for video in videos:
                    video_equipment = video.equipment_needed or []
                    if any(eq.lower() in [e.lower() for e in video_equipment] for eq in equipment_filter):
                        filtered_videos.append(video)
                videos = filtered_videos
            
            return videos
            
        except Exception as e:
            logger.error(f"Error filtering videos: {e}")
            return []
        finally:
            session.close()
    
    def _tfidf_search(self, query: str, videos: List[WorkoutVideoModel], top_k: int) -> List[DatabaseSearchResult]:
        """TF-IDF similarity search."""
        if not SKLEARN_AVAILABLE or self.tfidf_vectorizer is None or self.tfidf_matrix is None:
            return []
        
        try:
            # Create video ID to index mapping for current video set
            video_id_to_index = {}
            for i, video_id in enumerate(self.video_ids):
                video_id_to_index[video_id] = i
            
            # Filter videos that are in our TF-IDF matrix
            searchable_videos = [v for v in videos if v.id in video_id_to_index]
            
            if not searchable_videos:
                return []
            
            # Expand query with keywords
            expanded_query = self._expand_query(query)
            
            # Transform query
            query_vector = self.tfidf_vectorizer.transform([expanded_query.lower()])
            
            # Calculate similarities for all videos in matrix
            similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
            
            # Create results for searchable videos
            results = []
            for video in searchable_videos:
                matrix_idx = video_id_to_index[video.id]
                score = float(similarities[matrix_idx])  # Convert to Python float
                
                if score > 0:
                    results.append(DatabaseSearchResult(
                        video=video,
                        score=score,
                        method="tfidf",
                        match_details={"tfidf_score": score}
                    ))
            
            # Sort by score and return top results
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Error in TF-IDF search: {e}")
            return []
    
    def _keyword_search(self, query: str, videos: List[WorkoutVideoModel], top_k: int) -> List[DatabaseSearchResult]:
        """Keyword-based search."""
        try:
            query_words = normalize_text(query).split()
            results = []
            
            for video in videos:
                score = 0
                matches = []
                
                # Search in different fields with different weights
                search_fields = [
                    (video.title or "", 2.0, "title"),
                    (video.category or "", 1.5, "category"),
                    (video.description or "", 1.0, "description"),
                    (" ".join(video.keywords or []), 1.8, "keywords"),
                    (" ".join(video.tags or []), 1.3, "tags"),
                    (" ".join(video.equipment_needed or []), 1.2, "equipment")
                ]
                
                for field_text, weight, field_name in search_fields:
                    field_normalized = normalize_text(field_text)
                    field_words = field_normalized.split()
                    
                    for query_word in query_words:
                        if query_word in field_words:
                            score += weight
                            matches.append({"field": field_name, "word": query_word})
                        
                        # Partial matches (word contains query word)
                        partial_matches = [w for w in field_words if query_word in w and len(query_word) > 2]
                        for match in partial_matches:
                            score += weight * 0.5
                            matches.append({"field": field_name, "partial_word": match})
                
                if score > 0:
                    results.append(DatabaseSearchResult(
                        video=video,
                        score=score / len(query_words),  # Normalize by query length
                        method="keyword",
                        match_details={"matches": matches, "raw_score": score}
                    ))
            
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Error in keyword search: {e}")
            return []
    
    def _fuzzy_search(self, query: str, videos: List[WorkoutVideoModel], top_k: int) -> List[DatabaseSearchResult]:
        """Fuzzy string matching search."""
        if not FUZZ_AVAILABLE:
            return []
        
        try:
            results = []
            query_normalized = normalize_text(query)
            
            for video in videos:
                max_score = 0
                best_match = {}
                
                # Check different fields
                search_texts = [
                    (video.title or "", "title"),
                    (video.description or "", "description"),
                    (" ".join(video.keywords or []), "keywords")
                ]
                
                for text, field_name in search_texts:
                    text_normalized = normalize_text(text)
                    
                    # Different fuzzy matching strategies
                    ratio_score = fuzz.ratio(query_normalized, text_normalized) / 100.0
                    partial_score = fuzz.partial_ratio(query_normalized, text_normalized) / 100.0
                    token_score = fuzz.token_set_ratio(query_normalized, text_normalized) / 100.0
                    
                    best_field_score = max(ratio_score, partial_score, token_score)
                    
                    if best_field_score > max_score:
                        max_score = best_field_score
                        best_match = {
                            "field": field_name,
                            "ratio": ratio_score,
                            "partial": partial_score,
                            "token": token_score
                        }
                
                if max_score > 0.3:  # Minimum fuzzy threshold
                    results.append(DatabaseSearchResult(
                        video=video,
                        score=max_score,
                        method="fuzzy",
                        match_details=best_match
                    ))
            
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Error in fuzzy search: {e}")
            return []
    
    def _combine_results(self, 
                        tfidf_results: List[DatabaseSearchResult],
                        keyword_results: List[DatabaseSearchResult], 
                        fuzzy_results: List[DatabaseSearchResult]) -> List[DatabaseSearchResult]:
        """Combine results from different search methods."""
        
        # Weights for different methods
        weights = {"tfidf": 0.4, "keyword": 0.4, "fuzzy": 0.2}
        
        # Create a dictionary to combine scores by video ID
        combined_scores = {}
        
        for results, method in [(tfidf_results, "tfidf"), (keyword_results, "keyword"), (fuzzy_results, "fuzzy")]:
            for result in results:
                video_id = result.video.id
                weighted_score = result.score * weights[method]
                
                if video_id not in combined_scores:
                    combined_scores[video_id] = {
                        "video": result.video,
                        "total_score": weighted_score,
                        "methods": {method: result},
                        "method_scores": {method: result.score}
                    }
                else:
                    combined_scores[video_id]["total_score"] += weighted_score
                    combined_scores[video_id]["methods"][method] = result
                    combined_scores[video_id]["method_scores"][method] = result.score
        
        # Convert to final results
        final_results = []
        for data in combined_scores.values():
            # Determine primary method (highest individual score)
            primary_method = max(data["method_scores"].items(), key=lambda x: x[1])[0]
            primary_result = data["methods"][primary_method]
            
            final_results.append(DatabaseSearchResult(
                video=data["video"],
                score=data["total_score"],
                method=f"combined_{primary_method}",
                match_details={
                    "primary_method": primary_method,
                    "method_scores": data["method_scores"],
                    "primary_details": primary_result.match_details
                }
            ))
        
        final_results.sort(key=lambda x: x.score, reverse=True)
        return final_results
    
    def _expand_query(self, query: str) -> str:
        """Expand query with synonyms and related terms."""
        # Simple expansion - can be enhanced with word embeddings
        expansions = {
            "arm": ["arms", "bicep", "tricep", "shoulder"],
            "leg": ["legs", "quad", "hamstring", "calf", "thigh"],
            "core": ["abs", "abdominal", "stomach"],
            "cardio": ["aerobic", "running", "cycling"],
            "strength": ["weight", "resistance", "muscle"],
        }
        
        expanded_terms = [query]
        query_lower = query.lower()
        
        for key, synonyms in expansions.items():
            if key in query_lower:
                expanded_terms.extend(synonyms)
        
        return " ".join(expanded_terms)
    
    def get_search_suggestions(self, partial_query: str, max_suggestions: int = 5) -> List[str]:
        """Get search suggestions based on partial query."""
        try:
            suggestions = set()
            partial_lower = partial_query.lower()
            
            # Get unique words from all video data
            all_words = set()
            videos = self.db_manager.get_all_videos()
            
            for video in videos:
                # Extract words from various fields
                text_fields = [
                    video.title or "",
                    video.category or "",
                    " ".join(video.keywords or []),
                    " ".join(video.tags or []),
                    " ".join(video.equipment_needed or [])
                ]
                
                for field in text_fields:
                    words = normalize_text(field).split()
                    all_words.update(words)
            
            # Find matching suggestions
            for word in all_words:
                if (word.startswith(partial_lower) or partial_lower in word) and len(word) > 2:
                    suggestions.add(word)
                
                if len(suggestions) >= max_suggestions:
                    break
            
            return sorted(list(suggestions))[:max_suggestions]
            
        except Exception as e:
            logger.error(f"Error getting suggestions: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get search engine statistics."""
        return {
            "tfidf_available": SKLEARN_AVAILABLE,
            "fuzzy_available": FUZZ_AVAILABLE,
            "indexed_videos": len(self.video_ids),
            "tfidf_matrix_shape": self.tfidf_matrix.shape if self.tfidf_matrix is not None else None,
            "vectorizer_features": len(self.tfidf_vectorizer.vocabulary_) if self.tfidf_vectorizer else 0
        }
