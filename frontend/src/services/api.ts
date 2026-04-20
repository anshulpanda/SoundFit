import { TopData, RecommendationsResponse } from "@/types";

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

export async function fetchTopData(accessToken: string): Promise<TopData> {
  const res = await fetch(`${BASE_URL}/outfits/top-data`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  if (!res.ok) throw new Error("Failed to fetch top data");
  return res.json();
}

export async function fetchRecommendations(
  accessToken: string
): Promise<RecommendationsResponse> {
  const res = await fetch(`${BASE_URL}/outfits/recommend`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  if (!res.ok) throw new Error("Failed to fetch recommendations");
  return res.json();
}
