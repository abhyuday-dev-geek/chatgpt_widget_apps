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

  const prediction =
    widgetData?.widget?.prediction || widgetData?.backend?.prediction || "unknown";

  const containerHeight =
    displayMode === "fullscreen"
      ? (maxHeight ?? 520) - 40
      : 480;

  const label =
    prediction === "boy"
      ? "👶 Boy"
      : prediction === "girl"
      ? "👶 Girl"
      : "❓ Unknown";

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
        <div className="max-w-3xl mx-auto text-center">
          <h1 className="text-3xl font-bold mb-6">Gender Prediction</h1>
          <div className={`huggies-gender-result ${prediction}`}>
            {label}
          </div>
          <p className="huggies-gender-disclaimer mt-4">
            This is a playful prediction and not medically accurate.
          </p>
        </div>
      </div>
    </div>
  );
}

const rootEl = document.getElementById("huggies-gender-root");

if (rootEl) {
  createRoot(rootEl).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
} else {
  console.error("huggies-gender-root not found");
}
