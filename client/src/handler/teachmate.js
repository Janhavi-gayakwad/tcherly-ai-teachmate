// Client for the TeachMate FastAPI service (teachmate/). Uses the teacher's Tcherly access token.
const BASE_URL = (process.env.REACT_APP_TEACHMATE_URL || "http://localhost:8000").replace(/\/$/, "");

async function errorMessage(response) {
  try {
    const body = await response.json();
    if (typeof body.detail === "string") return body.detail;
  } catch (e) {
    // not JSON
  }
  if (response.status === 401) return "Your session expired. Please refresh the page.";
  if (response.status === 403) return "You don't have access to this lesson.";
  return `TeachMate is unavailable right now (HTTP ${response.status}).`;
}

async function call(auth, method, path, body) {
  let response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      method,
      headers: { Authorization: auth, ...(body ? { "Content-Type": "application/json" } : {}) },
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch (e) {
    throw new Error("Can't reach TeachMate. Is the TeachMate service running on " + BASE_URL + "?");
  }
  if (!response.ok) throw new Error(await errorMessage(response));
  return response.json();
}

export const listConversations = (auth, lessonId) => call(auth, "GET", `/conversations?lesson_id=${encodeURIComponent(lessonId)}`);
export const getConversation = (auth, conversationId) => call(auth, "GET", `/conversations/${conversationId}`);
export const draftReflection = (auth, conversationId) => call(auth, "POST", "/reflections/draft", { conversation_id: conversationId });
export const saveReflection = (auth, reflection) => call(auth, "POST", "/reflections", reflection);

/**
 * Stream a chat turn. `onEvent` receives each server-sent event:
 * start | status | delta | reset | proposal | replace | done | error
 */
export async function streamChat(auth, body, onEvent, signal) {
  let response;
  try {
    response = await fetch(`${BASE_URL}/chat/stream`, {
      method: "POST",
      headers: { Authorization: auth, "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal,
    });
  } catch (e) {
    if (e.name === "AbortError") return;
    throw new Error("Can't reach TeachMate. Is the TeachMate service running on " + BASE_URL + "?");
  }
  if (!response.ok) throw new Error(await errorMessage(response));

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    let chunk;
    try {
      chunk = await reader.read();
    } catch (e) {
      if (e.name === "AbortError" || (signal && signal.aborted)) return; // user closed the drawer / left the page
      throw new Error("The connection to TeachMate was interrupted. Please try again.");
    }
    const { value, done } = chunk;
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let boundary;
    while ((boundary = buffer.indexOf("\n\n")) >= 0) {
      const event = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      const line = event.split("\n").find((l) => l.startsWith("data: "));
      if (line) onEvent(JSON.parse(line.slice(6)));
    }
  }
}
