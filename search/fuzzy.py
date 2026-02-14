"""Fuzzy search engine for tracks."""
from typing import List, Tuple
from rapidfuzz import fuzz, process
from player.mpv_backend import Track


class FuzzySearcher:
    """Fuzzy search for music tracks."""
    
    def __init__(self):
        self.tracks: List[Track] = []
        self._cache: dict = {}
    
    def index(self, tracks: List[Track]):
        """Index tracks for searching."""
        self.tracks = tracks
        self._cache.clear()
    
    def search(self, query: str, limit: int = 20, threshold: int = 50) -> List[Tuple[Track, float]]:
        """Fuzzy search tracks.
        
        Returns list of (track, score) tuples sorted by score.
        """
        if not query or not self.tracks:
            return []
        
        query = query.lower()
        results = []
        
        for track in self.tracks:
            # Create searchable strings
            search_strings = [
                track.title.lower(),
                track.artist.lower(),
                f"{track.artist} {track.title}".lower(),
                f"{track.title} {track.artist}".lower(),
            ]
            
            # Get best score across all search strings
            best_score = 0
            for s in search_strings:
                score = fuzz.partial_ratio(query, s)
                if score > best_score:
                    best_score = score
            
            if best_score >= threshold:
                results.append((track, best_score))
        
        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]
    
    def search_fast(self, query: str, limit: int = 20) -> List[Track]:
        """Fast fuzzy search using rapidfuzz's process."""
        if not query or not self.tracks:
            return []
        
        # Create search corpus
        choices = [(track, str(track).lower()) for track in self.tracks]
        
        # Perform fuzzy matching
        matches = process.extract(
            query.lower(),
            choices,
            scorer=fuzz.partial_ratio,
            limit=limit
        )
        
        return [match[0][0] for match in matches]
    
    def search_multi_field(self, query: str, limit: int = 20) -> List[Tuple[Track, float]]:
        """Search across multiple fields with weighted scoring."""
        if not query or not self.tracks:
            return []
        
        query = query.lower()
        results = []
        
        for track in self.tracks:
            # Calculate weighted scores
            title_score = fuzz.partial_ratio(query, track.title.lower())
            artist_score = fuzz.partial_ratio(query, track.artist.lower())
            combined_score = fuzz.partial_ratio(query, f"{track.artist} {track.title}".lower())
            
            # Weight: title = 40%, artist = 35%, combined = 25%
            final_score = (title_score * 0.4 + artist_score * 0.35 + combined_score * 0.25)
            
            if final_score >= 40:  # Lower threshold for multi-field
                results.append((track, final_score))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]


# Convenience function
def fuzzy_search_tracks(tracks: List[Track], query: str, limit: int = 20) -> List[Track]:
    """Quick fuzzy search without creating a searcher instance."""
    searcher = FuzzySearcher()
    searcher.index(tracks)
    return searcher.search_fast(query, limit)
