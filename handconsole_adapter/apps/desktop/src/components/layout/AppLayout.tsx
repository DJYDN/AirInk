import { NavLink, Outlet } from "react-router-dom";
import { useAirInkStore } from "../../stores/airinkStore";

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
          <span>Gesture: {frame?.gesture.state ?? "--"}</span>
          <span>Pinch: {frame?.tracking.pinch_ratio?.toFixed(2) ?? "--"}</span>
          <span>FPS: {frame?.camera.fps?.toFixed(1) ?? "--"}</span>
        </footer>
      </main>
    </div>
  );
}
