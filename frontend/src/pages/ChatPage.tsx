import { useEffect, useRef, useState } from "react";
import { sendChat } from "../api/client";
import type { ChatMessage } from "../types";

export function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      content:
        "Ask questions about your uploaded PDFs. Answers are built from the most relevant document passages.",
    },
  ]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async () => {
    const text = input.trim();
    if (!text || sending) return;

    setMessages((prev) => [
      ...prev,
      { id: crypto.randomUUID(), role: "user", content: text },
    ]);
    setInput("");
    setSending(true);
    setError(null);

    try {
      const { answer, sources } = await sendChat(text, 5);
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: answer,
          sources,
        },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Chat failed");
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="flex h-full min-h-0 flex-1 flex-col">
      <header className="shrink-0 border-b border-slate-800 px-8 py-5">
        <h2 className="text-2xl font-semibold text-white">Chat</h2>
        <p className="mt-1 text-sm text-slate-400">
          Local semantic search over your indexed PDF chunks.
        </p>
      </header>

      <div className="flex-1 space-y-4 overflow-y-auto px-8 py-6">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={[
                "max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap",
                msg.role === "user"
                  ? "bg-indigo-600 text-white"
                  : "border border-slate-800 bg-slate-900 text-slate-200",
              ].join(" ")}
            >
              {msg.content}
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-4 space-y-2 border-t border-slate-700 pt-3">
                  <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                    Sources
                  </p>
                  {msg.sources.map((s) => (
                    <div
                      key={s.chunk_id}
                      className="rounded-lg bg-slate-950/60 p-2 text-xs text-slate-400"
                    >
                      <span className="font-medium text-indigo-300">
                        {s.filename}
                      </span>{" "}
                      · chunk {s.chunk_index} ·{" "}
                      {(s.score * 100).toFixed(0)}% match
                      <p className="mt-1 line-clamp-3 text-slate-500">
                        {s.content}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {sending && (
          <div className="flex justify-start">
            <div className="rounded-2xl border border-slate-800 bg-slate-900 px-4 py-3 text-sm text-slate-500">
              Searching your documents…
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {error && (
        <p className="shrink-0 px-8 pb-2 text-sm text-red-400">{error}</p>
      )}

      <form
        className="shrink-0 border-t border-slate-800 bg-slate-900/80 px-8 py-4"
        onSubmit={(e) => {
          e.preventDefault();
          void send();
        }}
      >
        <div className="flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about your documents…"
            disabled={sending}
            className="flex-1 rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white placeholder:text-slate-600 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={sending || !input.trim()}
            className="rounded-xl bg-indigo-600 px-5 py-3 text-sm font-medium text-white hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
}
