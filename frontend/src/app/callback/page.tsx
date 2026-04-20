import { Suspense } from "react";
import CallbackHandler from "./CallbackHandler";
import styles from "./page.module.css";

export default function CallbackPage() {
  return (
    <main className={styles.container}>
      <Suspense
        fallback={
          <>
            <div className={styles.spinner} aria-label="Loading" />
            <p className="text-muted">Connecting to Spotify…</p>
          </>
        }
      >
        <CallbackHandler />
        <div className={styles.spinner} aria-label="Loading" />
        <p className="text-muted">Connecting to Spotify…</p>
      </Suspense>
    </main>
  );
}
