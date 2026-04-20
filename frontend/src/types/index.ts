export interface Artist {
  id: string;
  name: string;
  genres: string[];
  image_url: string | null;
}

export interface Track {
  id: string;
  name: string;
  artist_name: string;
}

export interface TopData {
  top_artists: Artist[];
  top_tracks: Track[];
}

export interface OutfitItem {
  name: string;
  description: string;
  search_links: {
    asos: string;
    depop: string;
    amazon: string;
  };
}

export interface Outfit {
  name: string;
  vibe: string;
  items: OutfitItem[];
}

export interface OutfitRecommendation {
  track_name: string;
  artist_name: string;
  style_profile: string;
  outfits: Outfit[];
}

export interface RecommendationsResponse {
  recommendations: OutfitRecommendation[];
}

export interface SpotifyTokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  refresh_token?: string;
  scope: string;
}
