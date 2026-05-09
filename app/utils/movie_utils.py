import pandas as pd
import json
import os
from typing import List, Dict, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class MovieDataLoader:
    """Load and cache movie data from CSV files"""
    
    def __init__(self, dataset_path: str = "dataset"):
        self.dataset_path = dataset_path
        self.movies_df = None
        self._load_data()
    
    def _load_data(self):
        """Load and preprocess movie data"""
        try:
            csv_files = [
                os.path.join(self.dataset_path, "TMDB_movie_dataset_v11.csv"),
                os.path.join(self.dataset_path, "movie_dataset.csv"),
                os.path.join(self.dataset_path, "HollywoodMovies.csv"),
            ]
            
            for csv_path in csv_files:
                if os.path.exists(csv_path):
                    try:
                        # Try to load with optimal columns for TMDB dataset
                        tmdb_usecols = ['id', 'title', 'genres', 'overview', 'vote_average', 
                                       'vote_count', 'popularity', 'release_date', 'runtime',
                                       'poster_path', 'backdrop_path', 'keywords', 'tagline']
                        try:
                            self.movies_df = pd.read_csv(
                                csv_path, 
                                engine='python', 
                                on_bad_lines='skip',
                                encoding='utf-8',
                                usecols=tmdb_usecols,
                                nrows=5000  # Load more rows for better diversity
                            )
                        except (KeyError, ValueError):
                            # Fallback: try with basic columns
                            basic_usecols = ['title', 'genres', 'overview', 
                                           'vote_average', 'vote_count', 'popularity']
                            try:
                                self.movies_df = pd.read_csv(
                                    csv_path, 
                                    engine='python', 
                                    on_bad_lines='skip',
                                    encoding='utf-8',
                                    usecols=basic_usecols,
                                    nrows=5000
                                )
                            except (KeyError, ValueError):
                                # Load all columns if specific ones don't exist
                                self.movies_df = pd.read_csv(
                                    csv_path, 
                                    engine='python', 
                                    on_bad_lines='skip',
                                    encoding='utf-8',
                                    nrows=5000
                                )
                        
                        if len(self.movies_df) > 0:
                            self.movies_df = self._preprocess_tmdb_data()
                            print(f"✓ Loaded {len(self.movies_df)} movies from {os.path.basename(csv_path)}")
                            return
                    except Exception as e:
                        try:
                            self.movies_df = pd.read_csv(
                                csv_path, 
                                engine='python', 
                                on_bad_lines='skip',
                                encoding='latin-1',
                                nrows=5000
                            )
                            if len(self.movies_df) > 0:
                                self.movies_df = self._preprocess_tmdb_data()
                                print(f"✓ Loaded {len(self.movies_df)} movies from {os.path.basename(csv_path)}")
                                return
                        except Exception as e2:
                            print(f"  Skipping {os.path.basename(csv_path)}: {str(e2)[:50]}")
                            continue
            
            raise FileNotFoundError(f"Could not load any movie dataset from {self.dataset_path}")
        except Exception as e:
            print(f"Error loading movie data: {e}")
            self.movies_df = pd.DataFrame()
    
    def _preprocess_tmdb_data(self) -> pd.DataFrame:
        """Preprocess TMDB dataset with enhanced data handling"""
        df = self.movies_df.copy()
        
        # Ensure title column exists
        if 'title' not in df.columns and 'original_title' in df.columns:
            df['title'] = df['original_title']
        
        if 'title' not in df.columns:
            return pd.DataFrame()  # No title column, can't proceed
        
        # Clean genres - parse JSON arrays if needed
        if 'genres' in df.columns:
            df['genres'] = df['genres'].fillna("").astype(str)
            # Parse JSON genre arrays if present
            try:
                df['genres'] = df['genres'].apply(
                    lambda x: self._parse_json_field(x) if isinstance(x, str) and x.startswith('[') else x
                )
            except:
                pass
        else:
            df['genres'] = ""
        
        # Clean overview/description
        if 'overview' in df.columns:
            df['overview'] = df['overview'].fillna("")
        else:
            df['overview'] = ""
        
        # Parse and clean keywords
        if 'keywords' in df.columns:
            df['keywords'] = df['keywords'].fillna("").astype(str)
            try:
                df['keywords'] = df['keywords'].apply(
                    lambda x: self._parse_json_field(x) if isinstance(x, str) and x.startswith('[') else x
                )
            except:
                df['keywords'] = ""
        else:
            df['keywords'] = ""
        
        # Clean numeric columns
        if 'vote_average' in df.columns:
            df['rating'] = pd.to_numeric(df['vote_average'], errors='coerce').fillna(0)
        elif 'rating' in df.columns:
            df['rating'] = pd.to_numeric(df['rating'], errors='coerce').fillna(0)
        else:
            df['rating'] = 0
        
        if 'vote_count' in df.columns:
            df['vote_count'] = pd.to_numeric(df['vote_count'], errors='coerce').fillna(0)
        else:
            df['vote_count'] = 0
        
        if 'popularity' in df.columns:
            df['popularity'] = pd.to_numeric(df['popularity'], errors='coerce').fillna(0)
        else:
            df['popularity'] = 0
        
        # Handle release date
        if 'release_date' in df.columns:
            df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')
        else:
            df['release_date'] = None
        
        # Handle runtime
        if 'runtime' in df.columns:
            df['runtime'] = pd.to_numeric(df['runtime'], errors='coerce').fillna(0)
        else:
            df['runtime'] = 0
        
        # Keep poster and backdrop paths for UI
        if 'poster_path' not in df.columns:
            df['poster_path'] = ""
        if 'backdrop_path' not in df.columns:
            df['backdrop_path'] = ""
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['title'], keep='first')
        
        # Remove invalid movies
        df = df[df['title'].notna() & (df['title'] != "")]
        df = df[(df['rating'] > 0) | (df['popularity'] > 0)]  # Keep movies with rating or popularity
        
        # Sort by rating and popularity, keep top movies
        df['score'] = df['rating'] * 0.7 + (df['popularity'] / 100) * 0.3
        df = df.nlargest(1500, 'score')  # Keep more movies for better diversity
        
        return df.reset_index(drop=True)
    
    def _parse_json_field(self, field_str: str) -> str:
        """Parse JSON array field and extract names/values"""
        try:
            import json
            data = json.loads(field_str)
            if isinstance(data, list):
                # Extract names or values from JSON array
                names = [item.get('name', str(item)) if isinstance(item, dict) else str(item) for item in data]
                return ", ".join(names)
            return str(data)
        except:
            return str(field_str)
    
    def get_all_movies(self) -> pd.DataFrame:
        """Return all movies"""
        return self.movies_df if self.movies_df is not None else pd.DataFrame()
    
    def get_movie_count(self) -> int:
        """Return total movie count"""
        return len(self.movies_df) if self.movies_df is not None else 0


class RecommendationEngine:
    """Movie recommendation engine with multiple algorithms"""
    
    def __init__(self, movies_df: pd.DataFrame = None):
        self.movies_df = movies_df
        self.content_similarity_matrix = None
        self._build_similarity_matrix()
    
    def _build_similarity_matrix(self):
        """Build content-based similarity matrix using genres, keywords, and overview"""
        if self.movies_df is None or len(self.movies_df) == 0:
            return
        
        try:
            # Combine genres, keywords, and overview for richer content similarity
            features = (
                self.movies_df['genres'].fillna("") + " " + 
                self.movies_df.get('keywords', pd.Series([""] * len(self.movies_df))).fillna("") + " " +
                self.movies_df['overview'].fillna("")
            )
            
            # Use TF-IDF vectorizer with optimized parameters
            tfidf = TfidfVectorizer(
                max_features=200, 
                stop_words='english',
                min_df=1,
                max_df=0.8
            )
            feature_matrix = tfidf.fit_transform(features)
            
            # Compute cosine similarity
            self.content_similarity_matrix = cosine_similarity(feature_matrix)
        except Exception as e:
            print(f"Error building similarity matrix: {e}")
    
    def get_content_based_recommendations(
        self, 
        movie_title: str, 
        n_recommendations: int = 5
    ) -> List[Dict]:
        """Get recommendations based on similar movies"""
        if self.movies_df is None or len(self.movies_df) == 0:
            return []
        
        try:
            # Find movie index by title (case-insensitive)
            matches = self.movies_df[
                self.movies_df['title'].str.contains(movie_title, case=False, na=False)
            ]
            
            if matches.empty:
                return []
            
            movie_idx = matches.index[0]
            
            # Get similarity scores
            similarity_scores = self.content_similarity_matrix[movie_idx]
            similar_indices = np.argsort(similarity_scores)[::-1][1:n_recommendations+1]
            
            return self._format_recommendations(similar_indices)
        except Exception as e:
            print(f"Error in content-based recommendation: {e}")
            return []
    
    def get_genre_recommendations(
        self, 
        genre: str, 
        n_recommendations: int = 5,
        sort_by: str = "rating"
    ) -> List[Dict]:
        """Get recommendations by genre"""
        if self.movies_df is None or len(self.movies_df) == 0:
            return []
        
        try:
            # Filter by genre (case-insensitive)
            filtered = self.movies_df[
                self.movies_df['genres'].str.contains(genre, case=False, na=False)
            ]
            
            if filtered.empty:
                return []
            
            # Sort by rating/popularity
            if sort_by == "rating":
                sorted_movies = filtered.nlargest(n_recommendations, 'rating')
            else:  # popularity
                sorted_movies = filtered.nlargest(n_recommendations, 'popularity')
            
            return self._format_recommendations(sorted_movies.index)
        except Exception as e:
            print(f"Error in genre-based recommendation: {e}")
            return []
    
    def get_trending_recommendations(
        self, 
        n_recommendations: int = 5
    ) -> List[Dict]:
        """Get trending/popular movies"""
        if self.movies_df is None or len(self.movies_df) == 0:
            return []
        
        try:
            # Sort by popularity and rating
            trending = self.movies_df.nlargest(n_recommendations * 2, 'popularity')
            trending = trending.nlargest(n_recommendations, 'rating')
            
            return self._format_recommendations(trending.index)
        except Exception as e:
            print(f"Error in trending recommendation: {e}")
            return []
    
    def get_top_rated_recommendations(
        self, 
        n_recommendations: int = 5,
        min_votes: int = 50
    ) -> List[Dict]:
        """Get top-rated movies with minimum vote threshold"""
        if self.movies_df is None or len(self.movies_df) == 0:
            return []
        
        try:
            # Filter by minimum votes if available
            filtered = self.movies_df
            if 'vote_count' in filtered.columns:
                filtered = filtered[pd.to_numeric(filtered['vote_count'], errors='coerce').fillna(0) >= min_votes]
            
            top_rated = filtered.nlargest(n_recommendations, 'rating')
            
            return self._format_recommendations(top_rated.index)
        except Exception as e:
            print(f"Error in top-rated recommendation: {e}")
            return []
    
    def search_movies(
        self, 
        query: str, 
        n_recommendations: int = 5
    ) -> List[Dict]:
        """Search for movies by title or keywords"""
        if self.movies_df is None or len(self.movies_df) == 0:
            return []
        
        try:
            # Search in title and overview
            title_matches = self.movies_df[
                self.movies_df['title'].str.contains(query, case=False, na=False)
            ]
            
            if title_matches.empty:
                # Fall back to overview search
                overview_matches = self.movies_df[
                    self.movies_df['overview'].str.contains(query, case=False, na=False)
                ]
                results = overview_matches.nlargest(n_recommendations, 'rating')
            else:
                results = title_matches.head(n_recommendations)
            
            return self._format_recommendations(results.index)
        except Exception as e:
            print(f"Error in movie search: {e}")
            return []
    
    def _format_recommendations(self, indices) -> List[Dict]:
        """Format recommendations for output with TMDB data"""
        recommendations = []
        
        for idx in indices:
            if idx not in self.movies_df.index:
                continue
            
            movie = self.movies_df.loc[idx]
            
            # Format release year
            release_year = ""
            if pd.notna(movie.get('release_date')):
                try:
                    release_year = str(pd.to_datetime(movie.get('release_date')).year)
                except:
                    release_year = ""
            
            # Format runtime
            runtime_str = ""
            runtime = movie.get('runtime', 0)
            if pd.notna(runtime) and runtime > 0:
                runtime_str = f"{int(runtime)} min"
            
            recommendations.append({
                'id': int(movie.get('id', 0)) if pd.notna(movie.get('id')) else 0,
                'title': movie.get('title', 'Unknown'),
                'rating': float(movie.get('rating', 0)) if pd.notna(movie.get('rating')) else 0,
                'genres': str(movie.get('genres', 'Unknown')),
                'overview': str(movie.get('overview', ''))[:200] if pd.notna(movie.get('overview')) else '',
                'popularity': float(movie.get('popularity', 0)) if pd.notna(movie.get('popularity')) else 0,
                'vote_count': int(movie.get('vote_count', 0)) if pd.notna(movie.get('vote_count')) else 0,
                'keywords': str(movie.get('keywords', '')) if 'keywords' in movie and pd.notna(movie.get('keywords')) else '',
                'release_date': str(movie.get('release_date', ''))[:10] if pd.notna(movie.get('release_date')) else '',
                'release_year': release_year,
                'runtime': runtime_str,
                'poster_path': str(movie.get('poster_path', '')) if pd.notna(movie.get('poster_path')) else '',
                'backdrop_path': str(movie.get('backdrop_path', '')) if pd.notna(movie.get('backdrop_path')) else '',
                'tagline': str(movie.get('tagline', '')) if 'tagline' in movie and pd.notna(movie.get('tagline')) else '',
            })
        
        return recommendations


# Global instances
_data_loader = None
_recommendation_engine = None


def get_data_loader() -> MovieDataLoader:
    """Get or create data loader instance"""
    global _data_loader
    if _data_loader is None:
        _data_loader = MovieDataLoader()
    return _data_loader


def get_recommendation_engine() -> RecommendationEngine:
    """Get or create recommendation engine instance"""
    global _recommendation_engine
    if _recommendation_engine is None:
        loader = get_data_loader()
        _recommendation_engine = RecommendationEngine(loader.get_all_movies())
    return _recommendation_engine
