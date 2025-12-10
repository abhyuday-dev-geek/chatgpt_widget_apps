import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { Maximize2 } from "lucide-react";

import { useOpenAiGlobal } from "../use-openai-global";
import { useMaxHeight } from "../use-max-height";
import "./index.css";

function App() {
  const toolOutput = useOpenAiGlobal("toolOutput");
  const displayMode = useOpenAiGlobal("displayMode");
  const maxHeight = useMaxHeight() ?? undefined;
  const [widgetData, setWidgetData] = useState(null);

  useEffect(() => {
    if (toolOutput) setWidgetData(toolOutput);
  }, [toolOutput]);

  // backend now returns:
  // structuredContent = { text, results, widget: { widget_type: "cards", cards: [...] } }
  const cards =
    widgetData?.widget?.cards ||
    widgetData?.results ||
    [];

  const containerHeight =
    displayMode === "fullscreen"
      ? (maxHeight ?? 520) - 40
      : 480;

  return (
    <div
      style={{ maxHeight, height: containerHeight }}
      className={
        "relative antialiased w-full min-h-[480px] overflow-auto " +
        (displayMode === "fullscreen"
          ? "rounded-none border-0"
          : "border border-black/10 dark:border-white/10 rounded-2xl sm:rounded-3xl")
      }
    >
      {/* Fullscreen button */}
      {displayMode !== "fullscreen" && (
        <button
          aria-label="Enter fullscreen"
          className="absolute top-4 right-4 z-30 rounded-full bg-white text-black shadow-lg ring ring-black/5 p-2.5 pointer-events-auto"
          onClick={() => {
            if (window?.webplus?.requestDisplayMode) {
              window.webplus.requestDisplayMode({ mode: "fullscreen" });
            }
          }}
        >
          <Maximize2
            strokeWidth={1.5}
            className="h-4.5 w-4.5"
            aria-hidden="true"
          />
        </button>
      )}

      <div className="huggies-container w-full h-full p-4">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-3xl font-bold mb-6">Huggies FAQs</h1>

          {cards.length > 0 ? (
            <div className="huggies-cards-grid">
              {cards.map((card, idx) => (
                <div key={idx} className="huggies-card">
                  <h3 className="huggies-card-title">
                    {card.title || card.question}
                  </h3>
                  <p className="huggies-card-text">
                    {card.text || card.answer}
                  </p>
                  {(card.meta?.source_url || card.source_url) && (
                    <a
                      href={card.meta?.source_url || card.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="huggies-card-link"
                    >
                      Learn more
                    </a>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="huggies-empty">
              <p>{widgetData?.text || "No FAQs found"}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

const rootEl = document.getElementById("huggies-cards-root");

if (rootEl) {
  createRoot(rootEl).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
} else {
  console.error("huggies-cards-root not found");
}
