"use client";

import { useEffect, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";

export default function CallbackHandler() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { storeToken } = useAuth();
  const didRun = useRef(false);

  useEffect(() => {
    if (didRun.current) return;
    didRun.current = true;

    // Spotify returns ?error=access_denied if the user cancels
    const spotifyError = searchParams?.get("error");
    if (spotifyError) {
      console.error("[SoundFit] Spotify auth error:", spotifyError);
      router.push(`/?error=${encodeURIComponent(spotifyError)}`);
      return;
    }

    const code = searchParams?.get("code");
    const codeVerifier = sessionStorage.getItem("pkce_code_verifier");

    if (!code) {
      console.error("[SoundFit] Missing authorization code in callback URL");
      router.push("/?error=missing_code");
      return;
    }

    if (!codeVerifier) {
      console.error("[SoundFit] Missing PKCE code verifier in sessionStorage");
      router.push("/?error=missing_verifier");
      return;
    }

    fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/auth/callback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code, code_verifier: codeVerifier }),
    })
      .then(async (res) => {
        if (!res.ok) {
          const body = await res.text();
          throw new Error(`${res.status} — ${body}`);
        }
        return res.json();
      })
      .then((data) => {
        console.log("[SoundFit] Auth successful");
        sessionStorage.removeItem("pkce_code_verifier");
        storeToken(data.access_token);
        router.push("/dashboard");
      })
      .catch((err: Error) => {
        console.error("[SoundFit] Token exchange failed:", err.message);
        router.push(`/?error=${encodeURIComponent("token_exchange_failed")}`);
      });
  }, [searchParams, router, storeToken]);

  return null;
}
