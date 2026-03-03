declare module "plotly.js-dist-min" {
  export function newPlot(
    root: HTMLElement,
    data: Partial<PlotData>[],
    layout?: Partial<Layout>,
    config?: Partial<Config>,
  ): Promise<PlotlyHTMLElement>;

  export function react(
    root: HTMLElement,
    data: Partial<PlotData>[],
    layout?: Partial<Layout>,
    config?: Partial<Config>,
  ): Promise<PlotlyHTMLElement>;

  export function purge(root: HTMLElement): void;

  interface PlotData {
    x: number[];
    y: number[];
    type: string;
    mode: string;
    name: string;
    line: { color: string; width: number; dash?: string };
    fill: string;
    fillcolor: string;
    yaxis: string;
    hoverinfo: string;
    showlegend: boolean;
  }

  interface Layout {
    title: string | { text: string; font?: { size?: number } };
    xaxis: Partial<AxisLayout>;
    yaxis: Partial<AxisLayout>;
    yaxis2: Partial<AxisLayout>;
    showlegend: boolean;
    dragmode: string;
    selectdirection: string;
    margin: { l: number; r: number; t: number; b: number };
    height: number;
    shapes: Partial<Shape>[];
  }

  interface AxisLayout {
    title: string | { text: string; font?: { color?: string } };
    range: [number, number];
    tickvals: number[];
    ticktext: string[];
    side: string;
    overlaying: string;
    showgrid: boolean;
    zeroline: boolean;
    color: string;
  }

  interface Shape {
    type: string;
    x0: number;
    x1: number;
    y0: number;
    y1: number;
    fillcolor: string;
    opacity: number;
    line: { width: number };
    layer: string;
  }

  interface Config {
    responsive: boolean;
    displayModeBar: boolean;
    modeBarButtonsToRemove: string[];
  }

  interface PlotlyHTMLElement extends HTMLElement {
    on(event: string, callback: (data: SelectionEvent) => void): void;
  }

  interface SelectionEvent {
    range?: { x: [number, number]; y: [number, number] };
  }
}
