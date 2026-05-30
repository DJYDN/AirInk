import { useAirInkStore } from "../stores/airinkStore";

export default function Recognition() {
  const recognition = useAirInkStore((state) => state.recognition);

  return (
    <div className="page">
      <h1>Recognition</h1>
      <section className="panel">
        <h2>Recognition candidates</h2>
        {recognition ? (
          <ul>
            {recognition.candidates.map((candidate) => (
              <li key={candidate.id}>
                {candidate.text} {candidate.confidence == null ? "" : `(${candidate.confidence.toFixed(2)})`}
              </li>
            ))}
          </ul>
        ) : (
          <p>No recognition result yet.</p>
        )}
      </section>
    </div>
  );
}
