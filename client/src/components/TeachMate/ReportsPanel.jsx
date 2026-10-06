import React, { useEffect, useRef, useState } from "react";
import { FiAlertTriangle, FiCheckCircle, FiExternalLink, FiFileText } from "react-icons/fi";
import { createReport, listReports } from "handler/teachmate";

// Shown while a report is being written (about 10-40 seconds on the free Gemini tier).
const STEPS = ["Collecting the lesson's analytics", "Finding the key moments", "Writing the report", "Checking every number against your data"];

const reportUrl = (lessonId, reportId) => `/l/${lessonId}/report/${reportId}`;

// Lesson reports inside the TeachMate drawer: generate a new one, or open an earlier one (opens a printable page in a new tab).
export default function ReportsPanel({ lessonId, getAuthHeader }) {
  const [reports, setReports] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [step, setStep] = useState(0);
  const [latestId, setLatestId] = useState(null);
  const [error, setError] = useState(null);
  const timer = useRef(null);

  useEffect(() => {
    let active = true;
    listReports(getAuthHeader(), lessonId)
      .then((list) => active && setReports(list))
      .catch((e) => active && setError(e.message));
    return () => {
      active = false;
      clearInterval(timer.current);
    };
  }, [getAuthHeader, lessonId]);

  const generate = async () => {
    setGenerating(true);
    setError(null);
    setStep(0);
    timer.current = setInterval(() => setStep((s) => Math.min(s + 1, STEPS.length - 1)), 5000);
    try {
      const report = await createReport(getAuthHeader(), lessonId);
      setReports((list) => [
        { id: report.id, created_at: report.created_at, headline: report.sections.headline, grounded: report.grounding.grounded },
        ...(list || []),
      ]);
      setLatestId(report.id);
    } catch (e) {
      setError(e.message);
    } finally {
      clearInterval(timer.current);
      setGenerating(false);
    }
  };

  return (
    <div className="tm-reports">
      <p>
        A one-to-two-page summary of this lesson: key moments, what students said, your saved reflections, questions to explore and options to
        consider. Every number is checked against your data, and you can save it as a PDF.
      </p>
      <button type="button" className="tm-btn tm-btn-primary tm-report-generate" onClick={generate} disabled={generating}>
        <FiFileText /> {generating ? "Generating…" : "Generate a new report"}
      </button>
      {generating && <div className="tm-status">{STEPS[step]}</div>}
      {error && <div className="tm-error">{error}</div>}

      <div className="tm-report-list">
        {reports && reports.length === 0 && !generating && <div className="tm-muted">No reports for this lesson yet.</div>}
        {(reports || []).map((r) => (
          <a key={r.id} className={"tm-report-item" + (r.id === latestId ? " new" : "")} href={reportUrl(lessonId, r.id)} target="_blank" rel="noopener noreferrer">
            <div className="tm-report-item-head">
              <span>
                {r.id === latestId && <span className="tm-new">New</span>}
                {new Date(r.created_at).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" })}
              </span>
              <span className={"tm-grounding " + (r.grounded ? "ok" : "warn")} title={r.grounded ? "Numbers checked against your data" : "Some statements couldn't be verified"}>
                {r.grounded ? <FiCheckCircle /> : <FiAlertTriangle />}
              </span>
            </div>
            <div className="tm-report-item-headline">{r.headline.replace(/\s*\[E\d+(?:\s*,\s*E\d+)*\]/g, "")}</div>
            <div className="tm-report-item-open">
              Open report <FiExternalLink />
            </div>
          </a>
        ))}
      </div>
    </div>
  );
}
