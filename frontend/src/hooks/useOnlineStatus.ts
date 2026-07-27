import { useEffect, useState } from "react";

/**
 * Tracks network connectivity. Returns:
 *  - online: boolean (live)
 *  - lastSync: Date | null — set externally via markSynced() after successful API hits
 *
 * Logistics apps used in the field (rural / unstable networks) should surface this.
 */
export function useOnlineStatus() {
  const [online, setOnline] = useState<boolean>(
    typeof navigator === "undefined" ? true : navigator.onLine,
  );
  const [lastSync, setLastSync] = useState<Date | null>(null);

  useEffect(() => {
    const goOnline = () => setOnline(true);
    const goOffline = () => setOnline(false);
    window.addEventListener("online", goOnline);
    window.addEventListener("offline", goOffline);
    return () => {
      window.removeEventListener("online", goOnline);
      window.removeEventListener("offline", goOffline);
    };
  }, []);

  const markSynced = () => setLastSync(new Date());

  return { online, lastSync, markSynced };
}
