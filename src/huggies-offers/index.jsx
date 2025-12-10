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

  const offers = widgetData?.widget?.offers || widgetData?.backend?.offers || [];

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
        <div className="max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold mb-6">Coupons & Offers</h1>

          {offers.length > 0 ? (
            <div className="huggies-offers-list">
              {offers.map((offer, idx) => (
                <div key={idx} className="huggies-offer-item">
                  <div className="huggies-offer-type">{offer.type}</div>
                  <h3 className="huggies-offer-title">{offer.title}</h3>
                  {offer.expires && (
                    <div className="huggies-offer-expires">
                      Expires: {offer.expires}
                    </div>
                  )}
                  {offer.source_url && (
                    <a
                      href={offer.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="huggies-card-link mt-2 inline-block"
                    >
                      View offer
                    </a>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="huggies-empty">
              <p>{widgetData?.text || "No offers available right now."}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

const rootEl = document.getElementById("huggies-offers-root");

if (rootEl) {
  createRoot(rootEl).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
} else {
  console.error("huggies-offers-root not found");
}
