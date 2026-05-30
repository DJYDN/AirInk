import { Route, Routes } from "react-router-dom";
import AppLayout from "./components/layout/AppLayout";
import AirInkDashboard from "./pages/AirInkDashboard";
import AirWriting from "./pages/AirWriting";
import Calibration from "./pages/Calibration";
import Recognition from "./pages/Recognition";
import Playback from "./pages/Playback";
import Settings from "./pages/Settings";

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<AirInkDashboard />} />
        <Route path="/dashboard" element={<AirInkDashboard />} />
        <Route path="/writing" element={<AirWriting />} />
        <Route path="/calibration" element={<Calibration />} />
        <Route path="/recognition" element={<Recognition />} />
        <Route path="/playback" element={<Playback />} />
        <Route path="/settings" element={<Settings />} />
      </Route>
    </Routes>
  );
}
