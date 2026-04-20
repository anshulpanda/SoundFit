"use client";

import { useState } from "react";

const STORAGE_KEY = "soundfit_access_token";

function generateRandomString(length: number): string {
  const chars =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~";
  return Array.from(crypto.getRandomValues(new Uint8Array(length)))
    .map((b) => chars[b % chars.length])
    .join("");
}

async function sha256(plain: string): Promise<ArrayBuffer> {
  return crypto.subtle.digest("SHA-256", new TextEncoder().encode(plain));
}

function base64UrlEncode(buffer: ArrayBuffer): string {
  return btoa(String.fromCharCode(...new Uint8Array(buffer)))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=/g, "");
}

export function useAuth() {
  const [accessToken, setAccessToken] = useState<string | null>(() => {
    if (typeof window === "undefined") return null;
    return localStorage.getItem(STORAGE_KEY);
  });

  const login = async () => {
    const codeVerifier = generateRandomString(64);
    const codeChallenge = base64UrlEncode(await sha256(codeVerifier));

    sessionStorage.setItem("pkce_code_verifier", codeVerifier);

    const params = new URLSearchParams({
      client_id: process.env.NEXT_PUBLIC_SPOTIFY_CLIENT_ID!,
      response_type: "code",
      redirect_uri: process.env.NEXT_PUBLIC_REDIRECT_URI!,
      scope: "user-top-read",
      code_challenge_method: "S256",
      code_challenge: codeChallenge,
    });

    window.location.href = `https://accounts.spotify.com/authorize?${params}`;
  };

  const storeToken = (token: string) => {
    localStorage.setItem(STORAGE_KEY, token);
    setAccessToken(token);
  };

  const logout = () => {
    localStorage.removeItem(STORAGE_KEY);
    setAccessToken(null);
  };

  return { accessToken, login, logout, storeToken };
}
