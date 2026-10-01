import React, { useCallback, useEffect, useRef, useState } from "react";
import { FiAlertTriangle, FiCheckCircle, FiClock, FiEdit3, FiMessageCircle, FiPlus, FiSend, FiX } from "react-icons/fi";
import { useAuth } from "provider/auth";
import useFeedback from "provider/feedback";
import { draftReflection, getConversation, listConversations, saveReflection, streamChat } from "handler/teachmate";
import Markdown from "./Markdown";
import ReflectionCard from "./ReflectionCard";
import "assets/styles/teachmate.scss";

const STARTERS = [
  "Which concept confused students the most?",
  "Why did engagement drop?",
  "Which video in this course needs revision?",
  "What in-class activities could address the hardest part?",
];

let localId = 0;
const nextId = () => `local-${++localId}`;

function GroundingBadge({ grounding, repaired }) {
  if (!grounding) return null;
  if (grounding.grounded) {
    return (
      <span className="tm-grounding ok" title={`${grounding.checked_numbers} numbers checked against the cited evidence${repaired ? " (corrected once automatically)" : ""}`}>
        <FiCheckCircle /> Numbers checked against your data
      </span>
    );
  }
  return (
    <span className="tm-grounding warn" title="Some numbers couldn't be matched to the cited evidence. Please verify them on the dashboard.">
      <FiAlertTriangle /> {grounding.unsupported.length + grounding.unknown_ids.length} claim(s) couldn't be verified
    </span>
  );
}

export default function TeachMate() {
  const { getAuthHeader } = useAuth();
  const { lesson, range, setBookmarks } = useFeedback();
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [conversationId, setConversationId] = useState(null);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState(null);
  const [expandedCite, setExpandedCite] = useState(null);
  const scrollRef = useRef(null);
  const abortRef = useRef(null);

  const lessonId = lesson && (lesson.id || lesson._id);
  const maxMinutes = (lesson && lesson.minutes) || 1;

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages]);

  useEffect(() => () => abortRef.current && abortRef.current.abort(), []);

  const updateMessage = (id, patch) => setMessages((ms) => ms.map((m) => (m.id === id ? { ...m, ...(typeof patch === "function" ? patch(m) : patch) } : m)));

  const send = async (text) => {
    const message = (text || "").trim();
    if (!message || busy || !lessonId) return;
    setInput("");
    setError(null);
    setBusy(true);
    const assistantId = nextId();
    setMessages((ms) => [
      ...ms,
      { id: nextId(), role: "teacher", text: message },
      { id: assistantId, role: "assistant", text: "", status: "Thinking", streaming: true, proposals: [] },
    ]);

    const controller = new AbortController();
    abortRef.current = controller;
    const body = { lesson_id: lessonId, message, conversation_id: conversationId };
    if (range && range[1] > range[0]) body.range = range;

    try {
      await streamChat(
        getAuthHeader(),
        body,
        (event) => {
          switch (event.type) {
            case "start":
              setConversationId(event.conversation_id);
              break;
            case "status":
              updateMessage(assistantId, { status: event.text });
              break;
            case "delta":
              updateMessage(assistantId, (m) => ({ text: m.text + event.text, status: null }));
              break;
            case "reset":
              updateMessage(assistantId, { text: "", proposals: [], status: "Switching to a backup model" });
              break;
            case "replace":
              updateMessage(assistantId, { text: event.text });
              break;
            case "proposal":
              updateMessage(assistantId, (m) => ({
                proposals: [...m.proposals.filter((p) => p.id !== event.proposal.id), { ...event.proposal, key: nextId() }],
              }));
              break;
            case "done":
              setConversationId(event.conversation_id);
              updateMessage(assistantId, (m) => ({
                text: event.message.text,
                citations: event.message.citations,
                grounding: event.message.grounding,
                repaired: event.message.repaired,
                model: event.message.model,
                streaming: false,
                status: null,
                proposals: m.proposals,
              }));
              break;
            case "error":
              updateMessage(assistantId, { streaming: false, status: null, error: event.message });
              break;
            default:
          }
        },
        controller.signal
      );
    } catch (e) {
      if (e.name !== "AbortError") updateMessage(assistantId, { streaming: false, status: null, error: e.message });
    } finally {
      updateMessage(assistantId, (m) => (m.streaming ? { streaming: false, status: null } : {}));
      setBusy(false);
    }
  };

  const newChat = () => {
    if (busy) return;
    setMessages([]);
    setConversationId(null);
    setHistory(null);
    setError(null);
  };

  const toggleHistory = async () => {
    if (history) return setHistory(null);
    try {
      setHistory(await listConversations(getAuthHeader(), lessonId));
    } catch (e) {
      setError(e.message);
    }
  };

  const openConversation = async (id) => {
    try {
      const conversation = await getConversation(getAuthHeader(), id);
      const status = Object.fromEntries((conversation.proposals || []).map((p) => [p.id, p.status]));
      setMessages(
        conversation.messages.map((m) => ({
          ...m,
          id: nextId(),
          proposals: (m.proposals || []).map((p) => ({ ...p, status: status[p.id] || p.status, key: nextId() })),
        }))
      );
      setConversationId(id);
      setHistory(null);
    } catch (e) {
      setError(e.message);
    }
  };

  const saveProposal = useCallback(
    async (messageId, proposal, form) => {
      const { bookmark } = await saveReflection(getAuthHeader(), {
        lesson_id: lessonId,
        conversation_id: conversationId,
        proposal_id: proposal.id,
        ...form,
      });
      setBookmarks((bs) => [...(bs || []), bookmark]);
      updateMessage(messageId, (m) => ({
        proposals: m.proposals.map((p) => (p.key === proposal.key ? { ...p, ...form, status: "saved" } : p)),
      }));
    },
    [conversationId, getAuthHeader, lessonId, setBookmarks]
  );

  const dismissProposal = (messageId, proposal) =>
    updateMessage(messageId, (m) => ({ proposals: m.proposals.map((p) => (p.key === proposal.key ? { ...p, status: "dismissed" } : p)) }));

  const draftFromConversation = async (messageId) => {
    if (!conversationId) return;
    updateMessage(messageId, { drafting: true });
    try {
      const draft = await draftReflection(getAuthHeader(), conversationId);
      updateMessage(messageId, (m) => ({ drafting: false, proposals: [...m.proposals, { ...draft, id: null, key: nextId(), status: "proposed" }] }));
    } catch (e) {
      updateMessage(messageId, { drafting: false, error: e.message });
    }
  };

  const onKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send(input);
    }
  };

  if (!lessonId) return null;

  if (!open) {
    return (
      <button type="button" className="tm-launcher" onClick={() => setOpen(true)} title="Talk through your class data with TeachMate">
        <FiMessageCircle /> <span>Ask TeachMate</span>
      </button>
    );
  }

  return (
    <aside className="tm-drawer" aria-label="TeachMate assistant">
      <header className="tm-header">
        <div>
          <div className="tm-title">TeachMate</div>
          <div className="tm-subtitle">{lesson.name}</div>
        </div>
        <div className="tm-header-actions">
          <button type="button" className="tm-icon" title="Previous conversations" onClick={toggleHistory}>
            <FiClock />
          </button>
          <button type="button" className="tm-icon" title="New conversation" onClick={newChat} disabled={busy}>
            <FiPlus />
          </button>
          <button type="button" className="tm-icon" title="Close" onClick={() => setOpen(false)}>
            <FiX />
          </button>
        </div>
      </header>

      {history && (
        <div className="tm-history">
          {history.length === 0 && <div className="tm-muted">No earlier conversations for this lesson.</div>}
          {history.map((c) => (
            <button type="button" key={c.id} className="tm-history-item" onClick={() => openConversation(c.id)}>
              <span>{c.title}</span>
              <small>{new Date(c.updated_at).toLocaleString()}</small>
            </button>
          ))}
        </div>
      )}

      <div className="tm-messages" ref={scrollRef}>
        {messages.length === 0 && (
          <div className="tm-empty">
            <p>
              Ask about your class's feedback on this lecture. I'll point to the evidence and help you think it through. The decisions stay
              yours.
            </p>
            <div className="tm-starters">
              {STARTERS.map((s) => (
                <button type="button" key={s} className="tm-starter" onClick={() => send(s)}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m) =>
          m.role === "teacher" ? (
            <div key={m.id} className="tm-msg tm-msg-teacher">
              {m.text}
            </div>
          ) : (
            <div key={m.id} className="tm-msg tm-msg-assistant">
              {m.status && <div className="tm-status">{m.status}</div>}
              {m.text && (
                <Markdown
                  text={m.text}
                  citations={m.citations}
                  onCite={(id) => setExpandedCite(expandedCite && expandedCite.id === id && expandedCite.msg === m.id ? null : { id, msg: m.id })}
                />
              )}
              {expandedCite && expandedCite.msg === m.id && m.citations && (
                <div className="tm-evidence">
                  <strong>{expandedCite.id}</strong> {m.citations[expandedCite.id] || "Evidence details are available once the answer is complete."}
                </div>
              )}
              {m.error && <div className="tm-error">{m.error}</div>}
              {!m.streaming && m.text && (
                <div className="tm-msg-footer">
                  <GroundingBadge grounding={m.grounding} repaired={m.repaired} />
                  {conversationId && (
                    <button type="button" className="tm-link" onClick={() => draftFromConversation(m.id)} disabled={m.drafting}>
                      <FiEdit3 /> {m.drafting ? "Drafting…" : "Save as reflection"}
                    </button>
                  )}
                </div>
              )}
              {(m.proposals || []).map((p) => (
                <ReflectionCard
                  key={p.key}
                  proposal={p}
                  maxMinutes={maxMinutes}
                  onSave={(form) => saveProposal(m.id, p, form)}
                  onDismiss={() => dismissProposal(m.id, p)}
                />
              ))}
            </div>
          )
        )}
      </div>

      {error && <div className="tm-error tm-error-bar">{error}</div>}

      <footer className="tm-footer">
        {range && range[1] > range[0] && (
          <div className="tm-range">
            Looking at min {range[0]}–{range[1]}
          </div>
        )}
        <div className="tm-input">
          <textarea
            rows={2}
            value={input}
            placeholder="Ask about your class… (Enter to send, Shift+Enter for a new line)"
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            disabled={busy}
          />
          <button type="button" className="tm-send" onClick={() => send(input)} disabled={busy || !input.trim()} title="Send">
            <FiSend />
          </button>
        </div>
      </footer>
    </aside>
  );
}
