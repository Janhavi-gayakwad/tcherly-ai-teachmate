import React, { useState } from "react";
import { FiBookmark, FiCheckCircle } from "react-icons/fi";

const STATES = ["difficult", "easy", "boring", "engaging"];

// Editable reflection proposed by TeachMate. Nothing is saved until the teacher clicks Save.
export default function ReflectionCard({ proposal, maxMinutes, onSave, onDismiss }) {
  const [form, setForm] = useState({
    topic: proposal.topic || "",
    start_min: proposal.start_min || 0,
    end_min: proposal.end_min || maxMinutes || 1,
    states: proposal.states || [],
    question: proposal.question || "",
    action: proposal.action || "",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  if (proposal.status === "saved") {
    return (
      <div className="tm-card tm-card-saved">
        <FiCheckCircle /> Saved to your bookmarks: <strong>{proposal.topic}</strong> (min {proposal.start_min}–{proposal.end_min})
      </div>
    );
  }
  if (proposal.status === "dismissed") return null;

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));
  const toggleState = (state) =>
    setForm((f) => ({ ...f, states: f.states.includes(state) ? f.states.filter((s) => s !== state) : [...f.states, state] }));

  const save = async () => {
    const start = parseInt(form.start_min, 10);
    const end = parseInt(form.end_min, 10);
    if (!form.topic.trim() || !form.question.trim()) return setError("Please add a topic and a question.");
    if (isNaN(start) || isNaN(end) || end <= start) return setError("The end minute must be after the start minute.");
    setSaving(true);
    setError(null);
    try {
      await onSave({ ...form, start_min: start, end_min: end });
    } catch (e) {
      setError(e.message);
      setSaving(false);
    }
  };

  return (
    <div className="tm-card">
      <div className="tm-card-title">
        <FiBookmark /> Save this reflection?
      </div>
      <label>
        Topic
        <input value={form.topic} maxLength={120} onChange={set("topic")} />
      </label>
      <div className="tm-card-row">
        <label>
          From min
          <input type="number" min={0} max={maxMinutes} value={form.start_min} onChange={set("start_min")} />
        </label>
        <label>
          To min
          <input type="number" min={1} max={maxMinutes} value={form.end_min} onChange={set("end_min")} />
        </label>
      </div>
      <div className="tm-card-states">
        {STATES.map((state) => (
          <button
            type="button"
            key={state}
            className={`tm-state tm-state-${state}` + (form.states.includes(state) ? " active" : "")}
            onClick={() => toggleState(state)}
          >
            {state}
          </button>
        ))}
      </div>
      <label>
        Question / finding
        <textarea rows={2} value={form.question} onChange={set("question")} />
      </label>
      <label>
        Action (optional)
        <textarea rows={2} value={form.action} placeholder="What will you try next time?" onChange={set("action")} />
      </label>
      {error && <div className="tm-error">{error}</div>}
      <div className="tm-card-buttons">
        <button type="button" className="tm-btn tm-btn-primary" disabled={saving} onClick={save}>
          {saving ? "Saving…" : "Save to bookmarks"}
        </button>
        <button type="button" className="tm-btn" disabled={saving} onClick={onDismiss}>
          Not now
        </button>
      </div>
    </div>
  );
}
