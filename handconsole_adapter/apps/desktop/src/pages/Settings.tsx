export default function Settings() {
  return (
    <div className="page">
      <h1>Settings</h1>
      <section className="panel">
        <h2>Planned settings</h2>
        <ul>
          <li>Camera index, resolution, FPS</li>
          <li>Tracking confidence and smoothing</li>
          <li>Pinch down/up thresholds</li>
          <li>Stroke filter parameters</li>
          <li>Canvas and recognition options</li>
        </ul>
      </section>
    </div>
  );
}
