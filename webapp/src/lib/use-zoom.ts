import { useCallback, useEffect, useState } from "react";

const ZOOM_LEVELS = [0.5, 0.6, 0.7, 0.8, 1.0, 1.25, 1.5, 2.0, 3.0];
const DEFAULT_ZOOM_INDEX = ZOOM_LEVELS.indexOf(1.0);

export function useZoom() {
  const [zoomIndex, setZoomIndex] = useState(() => {
    try {
      const saved = localStorage.getItem("tauri-zoom");
      const idx = saved ? ZOOM_LEVELS.indexOf(Number.parseFloat(saved)) : -1;
      return idx >= 0 ? idx : DEFAULT_ZOOM_INDEX;
    } catch {
      return DEFAULT_ZOOM_INDEX;
    }
  });

  const applyZoom = useCallback(async (level: number) => {
    localStorage.setItem("tauri-zoom", String(level));
    try {
      const { getCurrentWebview } = await import("@tauri-apps/api/webview");
      await getCurrentWebview().setZoom(level);
      return;
    } catch {
      /* dev browser - fall through to CSS zoom */
    }
    document.documentElement.style.zoom = String(level);
  }, []);

  useEffect(() => {
    const handler = (e: WheelEvent) => {
      if (!e.ctrlKey) return;
      e.preventDefault();
      setZoomIndex((prev) => {
        const next =
          e.deltaY < 0 ? Math.min(prev + 1, ZOOM_LEVELS.length - 1) : Math.max(prev - 1, 0);
        if (next !== prev) void applyZoom(ZOOM_LEVELS[next]);
        return next;
      });
    };
    const reset = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key.toLowerCase() === "0") {
        e.preventDefault();
        setZoomIndex(DEFAULT_ZOOM_INDEX);
        void applyZoom(1.0);
      }
    };
    window.addEventListener("wheel", handler, { passive: false });
    window.addEventListener("keydown", reset);
    const saved = localStorage.getItem("tauri-zoom");
    if (saved) void applyZoom(Number.parseFloat(saved));
    return () => {
      window.removeEventListener("wheel", handler);
      window.removeEventListener("keydown", reset);
    };
  }, [applyZoom]);

  return { zoomPercent: Math.round(ZOOM_LEVELS[zoomIndex] * 100) };
}
