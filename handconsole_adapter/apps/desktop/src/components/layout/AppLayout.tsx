import { useEffect } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { listen } from "@tauri-apps/api/event";
import { useAirInkStore, type CameraStatus } from "../../stores/airinkStore";
import type { SessionStatusEvent, SidecarErrorEvent, StrokeUpdateEvent } from "../../types/events";
import type { AirInkFrame } from "../../types/frame";

const navItems = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/writing", label: "Writing" },
  { to: "/calibration", label: "Calibration" },
  { to: "/recognition", label: "Recognition" },
  { to: "/playback", label: "Playback" },
  { to: "/settings", label: "Settings" },
];

export default function AppLayout() {
  const frame = useAirInkStore((state) => state.latestFrame);
  const status = useAirInkStore((state) => state.cameraStatus.status);
  const sessionStatus = useAirInkStore((state) => state.sessionStatus.status);
  const sidecarErrorCount = useAirInkStore((state) => state.sidecarErrors.length);

  useEffect(() => {
    const unlistenCamera = listen<CameraStatus>("airink/camera_status", (event) => {
      useAirInkStore.getState().setCameraStatus(event.payload);
    });

    const unlistenFrame = listen<AirInkFrame>("airink/tracking_frame", (event) => {
      useAirInkStore.getState().addFrame(event.payload);
    });

    const unlistenStroke = listen<StrokeUpdateEvent>("airink/stroke_update", (event) => {
      useAirInkStore.getState().applyStrokeUpdate(event.payload);
    });

    const unlistenSession = listen<SessionStatusEvent>("airink/session_status", (event) => {
      useAirInkStore.getState().setSessionStatus(event.payload);
    });

    const unlistenSidecarError = listen<SidecarErrorEvent>("airink/sidecar_error", (event) => {
      useAirInkStore.getState().addSidecarError(event.payload);
    });

    return () => {
      unlistenCamera.then((dispose) => dispose());
      unlistenFrame.then((dispose) => dispose());
      unlistenStroke.then((dispose) => dispose());
      unlistenSession.then((dispose) => dispose());
      unlistenSidecarError.then((dispose) => dispose());
    };
  }, []);

  return (
    <div className="app-shell">
      <aside className="nav-rail">
        <div className="nav-brand">AI</div>
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
          >
            {item.label}
          </NavLink>
        ))}
      </aside>
      <main className="main-area">
        <section className="content-area">
          <Outlet />
        </section>
        <footer className="status-bar">
          <span>Camera: {status}</span>
          <span>Session: {sessionStatus}</span>
          <span>Gesture: {frame?.gesture.state ?? "--"}</span>
          <span>Pinch: {frame?.tracking.pinch_ratio?.toFixed(2) ?? "--"}</span>
          <span>FPS: {frame?.camera.fps?.toFixed(1) ?? "--"}</span>
          <span>Sidecar errors: {sidecarErrorCount}</span>
        </footer>
      </main>
    </div>
  );
}
