"use client";

import { useEffect, useRef, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type FunctionCall = {
  name: string;
  args: Record<string, unknown>;
};

type Message = {
  role: "user" | "agent";
  text: string;
  functionCalls?: FunctionCall[];
  isError?: boolean;
};

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Αυτόματο scroll στο τέλος κάθε φορά που προστίθεται μήνυμα
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  async function sendMessage() {
    const message = input.trim();
    if (!message || isLoading) return;

    setMessages((previous) => [...previous, { role: "user", text: message }]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });

      if (!response.ok) {
        const problem = await response.json().catch(() => null);
        throw new Error(problem?.detail ?? `HTTP ${response.status}`);
      }

      const data = await response.json();
      setMessages((previous) => [
        ...previous,
        {
          role: "agent",
          text: data.reply,
          functionCalls: data.function_calls,
        },
      ]);
    } catch (error) {
      setMessages((previous) => [
        ...previous,
        {
          role: "agent",
          text: error instanceof Error ? error.message : "Άγνωστο σφάλμα",
          isError: true,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="mx-auto flex h-dvh w-full max-w-3xl flex-col px-4">
      <header className="border-b border-black/10 py-4 dark:border-white/15">
        <h1 className="text-lg font-semibold">AI Agent με RAG</h1>
        <p className="text-sm text-black/60 dark:text-white/60">
          Ρώτησε κάτι — ο agent χρησιμοποιεί εργαλεία όταν χρειάζεται.
        </p>
      </header>

      <div className="flex-1 space-y-4 overflow-y-auto py-6">
        {messages.length === 0 && (
          <p className="text-sm text-black/50 dark:text-white/50">
            Δοκίμασε: «Τι είναι το cosine similarity;» ή «Τι ώρα είναι;»
          </p>
        )}

        {messages.map((message, index) => (
          <div
            key={index}
            className={message.role === "user" ? "flex justify-end" : ""}
          >
            <div
              className={
                message.role === "user"
                  ? "max-w-[80%] rounded-2xl bg-blue-600 px-4 py-2 text-white"
                  : "max-w-[90%]"
              }
            >
              <div
                className={`whitespace-pre-wrap text-sm leading-relaxed ${
                  message.isError ? "text-red-600 dark:text-red-400" : ""
                }`}
              >
                {message.text}
              </div>

              {message.functionCalls && message.functionCalls.length > 0 && (
                <details className="mt-2 rounded-lg border border-black/10 bg-black/[0.03] px-3 py-2 dark:border-white/15 dark:bg-white/5">
                  <summary className="cursor-pointer text-xs font-medium text-black/70 dark:text-white/70">
                    🔧 {message.functionCalls.length} function call
                    {message.functionCalls.length > 1 ? "s" : ""}
                  </summary>
                  <ul className="mt-2 space-y-1">
                    {message.functionCalls.map((call, callIndex) => (
                      <li key={callIndex} className="font-mono text-xs">
                        <span className="font-semibold">{call.name}</span>
                        {Object.keys(call.args).length > 0 && (
                          <span className="text-black/60 dark:text-white/60">
                            {" "}
                            {JSON.stringify(call.args)}
                          </span>
                        )}
                      </li>
                    ))}
                  </ul>
                </details>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <p className="text-sm text-black/50 dark:text-white/50">
            Ο agent σκέφτεται…
          </p>
        )}

        <div ref={bottomRef} />
      </div>

      <form
        onSubmit={(event) => {
          event.preventDefault();
          sendMessage();
        }}
        className="flex gap-2 border-t border-black/10 py-4 dark:border-white/15"
      >
        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={(event) => {
            // Ρητός χειρισμός· δεν βασιζόμαστε στο implicit submit της φόρμας
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              sendMessage();
            }
          }}
          placeholder="Γράψε το μήνυμά σου…"
          className="flex-1 rounded-lg border border-black/15 px-3 py-2 text-sm outline-none focus:border-blue-600 dark:border-white/20"
        />
        <button
          type="submit"
          disabled={isLoading || input.trim() === ""}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-40"
        >
          Send
        </button>
      </form>
    </main>
  );
}
