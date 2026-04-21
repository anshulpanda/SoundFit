"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { useAuth } from "@/hooks/useAuth";
import { fetchTopData, fetchRecommendations } from "@/services/api";
import { TopData, RecommendationsResponse } from "@/types";
import styles from "./page.module.css";

export default function DashboardPage() {
  const { accessToken, logout } = useAuth();
  const router = useRouter();

  const [topData, setTopData] = useState<TopData | null>(null);
  const [recs, setRecs] = useState<RecommendationsResponse | null>(null);
  const [topError, setTopError] = useState<string | null>(null);
  const [recsLoading, setRecsLoading] = useState(true);
  const [recsError, setRecsError] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken) { router.push("/"); return; }

    // Phase 1 — fetch top artists + songs immediately
    fetchTopData(accessToken)
      .then(setTopData)
      .catch((e: Error) => setTopError(e.message));

    // Phase 2 — fetch recommendations (slow, LLM + Serper)
    fetchRecommendations(accessToken)
      .then(setRecs)
      .catch((e: Error) => setRecsError(e.message))
      .finally(() => setRecsLoading(false));
  }, [accessToken, router]);

  const handleLogout = () => { logout(); router.push("/"); };

  // Full-page loading only if top data hasn't arrived yet
  if (!topData && !topError) {
    return (
      <main className={styles.statusPage}>
        <div className={styles.spinner} />
        <p className={styles.statusText}>Loading your music profile…</p>
      </main>
    );
  }

  if (topError) {
    return (
      <main className={styles.statusPage}>
        <p className={styles.errorText}>{topError}</p>
        <button className="btn-outlined" onClick={handleLogout}>Back to Login</button>
      </main>
    );
  }

  return (
    <main className={styles.page}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerLogo}>
          <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor" style={{ color: "var(--accent)" }}>
            <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z" />
          </svg>
          <span>SoundFit</span>
        </div>
        <button className="btn-outlined" onClick={handleLogout}>Log out</button>
      </header>

      <div className={styles.content}>
        {/* ── Taste profile section ── */}
        <section className={styles.profileSection}>
          {/* Top artists */}
          <div className={styles.profileBlock}>
            <h2 className={styles.profileLabel}>Top Artists</h2>
            <div className={styles.artistRow}>
              {topData!.top_artists.map((artist) => (
                <div key={artist.id} className={styles.artistChip}>
                  <div className={styles.artistAvatar}>
                    {artist.image_url ? (
                      <Image src={artist.image_url} alt={artist.name} fill sizes="40px" className={styles.artistAvatarImg} unoptimized />
                    ) : (
                      <div className={styles.artistAvatarPlaceholder} />
                    )}
                  </div>
                  <span className={styles.artistChipName}>{artist.name}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Top songs */}
          <div className={styles.profileBlock}>
            <h2 className={styles.profileLabel}>Top Songs</h2>
            <ol className={styles.songList}>
              {topData!.top_tracks.map((track, i) => (
                <li key={track.id} className={styles.songRow}>
                  <span className={styles.songNumber}>{i + 1}</span>
                  <div className={styles.songThumb}>
                    {track.artist_image_url ? (
                      <Image src={track.artist_image_url} alt={track.name} fill sizes="36px" className={styles.songThumbImg} unoptimized />
                    ) : (
                      <div className={styles.songThumbPlaceholder} />
                    )}
                  </div>
                  <div className={styles.songInfo}>
                    <span className={styles.songName}>{track.name}</span>
                    <span className={styles.songArtist}>
                      {track.artist_name}
                      {track.featured_artists.length > 0 && (
                        <> ft. {track.featured_artists.join(", ")}</>
                      )}
                    </span>
                  </div>
                </li>
              ))}
            </ol>
          </div>

          {/* Taste summary — shows placeholder until recs arrive */}
          <div className={styles.tasteSummaryBox}>
            <p className={styles.profileLabel}>Your Style DNA</p>
            {recsLoading && !recs ? (
              <div className={styles.summaryLoading}>
                <div className={styles.shimmerLine} style={{ width: "90%" }} />
                <div className={styles.shimmerLine} style={{ width: "75%" }} />
                <div className={styles.shimmerLine} style={{ width: "60%" }} />
              </div>
            ) : (
              <p className={styles.tasteSummaryText}>
                {recs?.taste_summary ?? "Could not generate summary."}
              </p>
            )}
          </div>
        </section>

        {/* ── Recommendations section ── */}
        <section className={styles.recsSection}>
          <h2 className={styles.sectionTitle}>Outfit Recommendations</h2>

          {recsLoading && (
            <div className={styles.recsLoadingState}>
              <div className={styles.spinner} />
              <p className={styles.statusText}>Analyzing your taste and finding products…</p>
            </div>
          )}

          {recsError && (
            <p className={styles.errorText}>{recsError}</p>
          )}

          {recs && recs.recommendations.map((rec, ri) => (
            <div key={ri} className={styles.trackBlock}>
              {/* Track header */}
              <div className={styles.trackHeader}>
                <div className={styles.trackHeaderThumb}>
                  {rec.artist_image_url ? (
                    <Image src={rec.artist_image_url} alt={rec.track_name} fill sizes="48px" className={styles.songThumbImg} unoptimized />
                  ) : (
                    <div className={styles.songThumbPlaceholder} />
                  )}
                </div>
                <div>
                  <p className={styles.trackHeaderName}>{rec.track_name}</p>
                  <p className={styles.trackHeaderArtist}>
                    {rec.artist_name}
                    {rec.featured_artists.length > 0 && <> ft. {rec.featured_artists.join(", ")}</>}
                  </p>
                </div>
              </div>

              {/* Style profile with lyric reference */}
              <p className={styles.styleProfile}>{rec.style_profile}</p>

              {/* Queries + products */}
              {rec.queries.map((rq, qi) => (
                <div key={qi} className={styles.queryBlock}>
                  <div className={styles.queryHeader}>
                    <span className={styles.queryIndex}>{qi + 1}</span>
                    <span className={styles.queryText}>{rq.query}</span>
                  </div>
                  <div className={styles.productGrid}>
                    {rq.products.map((product, pi) => (
                      <a
                        key={pi}
                        href={product.link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={styles.productCard}
                      >
                        <div className={styles.productImageWrap}>
                          {product.image_url ? (
                            <Image src={product.image_url} alt={product.title} fill sizes="160px" className={styles.productImage} unoptimized />
                          ) : (
                            <div className={styles.productImagePlaceholder} />
                          )}
                          {pi === 0 && <span className={styles.topPickBadge}>Top Pick</span>}
                          {/* Song attribution badge */}
                          <div className={styles.songBadge}>
                            {rec.artist_image_url && (
                              <div className={styles.songBadgeThumb}>
                                <Image src={rec.artist_image_url} alt={rec.track_name} fill sizes="16px" className={styles.songThumbImg} unoptimized />
                              </div>
                            )}
                            <span className={styles.songBadgeText}>{rec.track_name}</span>
                          </div>
                        </div>
                        <div className={styles.productInfo}>
                          <p className={styles.productTitle}>{product.title}</p>
                          <div className={styles.productMeta}>
                            {product.price && <span className={styles.productPrice}>{product.price}</span>}
                            {product.source && <span className={styles.productSource}>{product.source}</span>}
                          </div>
                        </div>
                      </a>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ))}
        </section>
      </div>
    </main>
  );
}
