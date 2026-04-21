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
  featured_artists: string[];
  artist_image_url: string | null;
}

export interface TopData {
  top_artists: Artist[];
  top_tracks: Track[];
}

export interface Product {
  title: string;
  link: string;
  image_url: string | null;
  price: string | null;
  source: string | null;
}

export interface RankedQuery {
  query: string;
  products: Product[];
}

export interface TrackRecommendation {
  track_name: string;
  artist_name: string;
  featured_artists: string[];
  artist_image_url: string | null;
  style_profile: string;
  queries: RankedQuery[];
}

export interface RecommendationsResponse {
  taste_summary: string;
  recommendations: TrackRecommendation[];
}

export interface SpotifyTokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  refresh_token?: string;
  scope: string;
}
