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

  const markers = widgetData?.widget?.markers || [];

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
        <div className="max-w-5xl mx-auto">
          <h1 className="text-3xl font-bold mb-6">Store Locator</h1>

          <div className="huggies-map-container">
            <div className="w-full h-64 md:h-80 flex items-center justify-center bg-gray-100 text-gray-500 rounded-xl">
              Map visualization would go here
              {markers.length > 0 && (
                <div className="ml-4 text-sm">
                  {markers.length} locations found
                </div>
              )}
            </div>
          </div>

          {markers.length > 0 && (
            <div className="mt-4 space-y-2 text-sm">
              {markers.map((m, idx) => (
                <div key={idx} className="huggies-location-row">
                  <strong>{m.name}</strong> — {m.address} ({m.distance_miles} mi)
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

const rootEl = document.getElementById("huggies-map-root");

if (rootEl) {
  createRoot(rootEl).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
} else {
  console.error("huggies-map-root not found");
}
