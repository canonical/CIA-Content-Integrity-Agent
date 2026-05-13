import { useEffect, useRef, useCallback, useState } from "react";
import { io, Socket } from "socket.io-client";
import type { ScanStatus } from "../api/types";

interface ScanProgressEvent {
  scan_id: number;
  status: ScanStatus;
  progress: number;
  current_agent: string | null;
}

interface UseScanProgressOptions {
  scanId: number | null;
  onProgress?: (event: ScanProgressEvent) => void;
  onComplete?: (scanId: number) => void;
  onFailed?: (scanId: number, error: string) => void;
}

export function useScanProgress({
  scanId,
  onProgress,
  onComplete,
  onFailed,
}: UseScanProgressOptions) {
  const socketRef = useRef<Socket | null>(null);
  const [connected, setConnected] = useState(false);

  const connect = useCallback(() => {
    if (socketRef.current) return;
    const socket = io({ transports: ["websocket", "polling"] });
    socketRef.current = socket;
    socket.on("connect", () => setConnected(true));
    socket.on("disconnect", () => setConnected(false));
  }, []);

  const disconnect = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.disconnect();
      socketRef.current = null;
      setConnected(false);
    }
  }, []);

  useEffect(() => {
    if (!scanId || !socketRef.current) return;
    const socket = socketRef.current;
    socket.emit("scan:subscribe", { scan_id: scanId });

    const handleProgress = (event: ScanProgressEvent) => {
      if (event.scan_id === scanId && onProgress) onProgress(event);
    };
    const handleComplete = (data: { scan_id: number }) => {
      if (data.scan_id === scanId && onComplete) onComplete(scanId);
    };
    const handleFailed = (data: { scan_id: number; error_message: string }) => {
      if (data.scan_id === scanId && onFailed) onFailed(scanId, data.error_message);
    };

    socket.on("scan:progress", handleProgress);
    socket.on("scan:complete", handleComplete);
    socket.on("scan:failed", handleFailed);

    return () => {
      socket.emit("scan:unsubscribe", { scan_id: scanId });
      socket.off("scan:progress", handleProgress);
      socket.off("scan:complete", handleComplete);
      socket.off("scan:failed", handleFailed);
    };
  }, [scanId, onProgress, onComplete, onFailed]);

  return { connect, disconnect, connected };
}