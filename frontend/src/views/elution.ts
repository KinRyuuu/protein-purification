/**
 * Elution profile (chromatogram) view using Plotly.js.
 * Spec Section 7.
 */

import * as Plotly from "plotly.js-dist-min";
import type { SessionState } from "../state";

const DISPLAY_FRACTIONS = 125;
const INTERNAL_FRACTIONS = 250;

export function renderElutionProfile(
  container: HTMLElement,
  state: SessionState,
): void {
  container.innerHTML = "";

  const plotDiv = document.createElement("div");
  plotDiv.id = "elution-plot";
  plotDiv.style.width = "100%";
  plotDiv.style.height = "450px";
  container.appendChild(plotDiv);

  if (!state.fractions || state.fractions.length === 0) return;

  const fractions = state.fractions;
  const x: number[] = [];
  const absorbance: number[] = [];

  for (let i = 0; i < Math.min(fractions.length, INTERNAL_FRACTIONS); i++) {
    x.push((i + 1) / 2);
    absorbance.push(fractions[i][0] / state.scale);
  }

  const traces: Partial<Plotly.PlotData>[] = [
    {
      x,
      y: absorbance,
      type: "scatter",
      mode: "lines",
      name: "Absorbance at 280 nm",
      line: { color: "blue", width: 1.5 },
      yaxis: "y",
      hoverinfo: "x+y",
      showlegend: true,
    },
  ];

  // Red enzyme activity trace (when assayed)
  if (state.assayed && state.enzymeIndex >= 0) {
    const enzymeY: number[] = [];
    const protIdx = state.enzymeIndex + 1;
    for (
      let i = 0;
      i < Math.min(fractions.length, INTERNAL_FRACTIONS);
      i++
    ) {
      const val =
        protIdx < fractions[i].length ? fractions[i][protIdx] : 0;
      enzymeY.push((val * 4.0) / state.scale);
    }
    traces.push({
      x,
      y: enzymeY,
      type: "scatter",
      mode: "lines",
      name: "Enzyme activity",
      line: { color: "red", width: 1.5 },
      yaxis: "y2",
      hoverinfo: "x+y",
      showlegend: true,
    });
  }

  // Magenta gradient line
  if (state.hasGradient) {
    const gradLabel =
      state.gradientType === "salt"
        ? "Salt concentration (molar)"
        : "pH";
    traces.push({
      x: [0, DISPLAY_FRACTIONS],
      y: [state.gradientStart, state.gradientEnd],
      type: "scatter",
      mode: "lines",
      name: gradLabel,
      line: { color: "magenta", width: 1.5, dash: "dash" },
      yaxis: "y2",
      hoverinfo: "x+y",
      showlegend: true,
    });
  }

  const maxY = Math.max(...absorbance, 0.1);
  const yRange: [number, number] = [0, maxY * 1.1];

  const shapes: Partial<Plotly.Shape>[] = [];

  const tickvals = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120];
  const ticktext = tickvals.map(String);

  const layout: Partial<Plotly.Layout> = {
    title: { text: state.separationTitle || "Elution Profile" },
    xaxis: {
      title: "Fraction number",
      range: [0, DISPLAY_FRACTIONS],
      tickvals,
      ticktext,
    },
    yaxis: {
      title: { text: "Absorbance at 280 nm", font: { color: "blue" } },
      range: yRange,
      side: "left",
      color: "blue",
    },
    showlegend: true,
    margin: { l: 70, r: 70, t: 50, b: 50 },
    height: 420,
    dragmode: "select",
    selectdirection: "h",
    shapes,
  };

  if (state.assayed || state.hasGradient) {
    const rightTitle = state.assayed
      ? "Enzyme activity (Units/fraction)"
      : state.gradientType === "salt"
        ? "Salt concentration (molar)"
        : "pH";
    const rightColor = state.assayed ? "red" : "magenta";
    layout.yaxis2 = {
      title: { text: rightTitle, font: { color: rightColor } },
      side: "right",
      overlaying: "y",
      showgrid: false,
      color: rightColor,
    };
  }

  const config: Partial<Plotly.Config> = {
    responsive: true,
    displayModeBar: true,
    modeBarButtonsToRemove: ["lasso2d", "autoScale2d"],
  };

  Plotly.newPlot(plotDiv, traces, layout, config).then((gd) => {
    gd.on("plotly_selected", (eventData) => {
      if (eventData?.range) {
        const start = Math.max(1, Math.round(eventData.range.x[0]));
        const end = Math.min(
          DISPLAY_FRACTIONS,
          Math.round(eventData.range.x[1]),
        );
        document.dispatchEvent(
          new CustomEvent("pool-request", { detail: { start, end } }),
        );
      }
    });
  });
}

export function updateElutionScale(_scale: number): void {
  // Scale is handled during full re-render in renderElutionProfile
}
