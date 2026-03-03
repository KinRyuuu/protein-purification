/**
 * PAGE gel visualization using HTML5 Canvas.
 * Spec Section 6.
 */

import type { GelBand, GelSpot, SessionState } from "../state";

const GEL_BG = "rgb(208, 208, 224)";
const SHADOW_OFFSET = 4;
const LANE_WIDTH = 30;
const LANE_START_X = 4;
const GEL_PADDING = 20;

const MW_MARKERS = [80000, 60000, 50000, 40000, 30000, 20000, 10000, 5000];
const MW_LABELS = ["80K", "60K", "50K", "40K", "30K", "20K", "10K", "5K"];

function mobility(mw: number): number {
  return 120.0 * (11.5 - Math.log(mw));
}

function isGelBand(item: GelBand | GelSpot): item is GelBand {
  return "lane" in item;
}

export function renderGel(
  container: HTMLElement,
  state: SessionState,
): void {
  if (!state.gelData || state.gelData.length === 0) return;

  container.innerHTML = "";

  const canvas = document.createElement("canvas");
  canvas.className = "gel-canvas";
  container.appendChild(canvas);

  if (state.twoDGel) {
    renderGel2D(canvas, state.gelData as GelSpot[], state);
  } else {
    renderGel1D(canvas, state.gelData as GelBand[], state);
  }
}

function renderGel1D(
  canvas: HTMLCanvasElement,
  bands: GelBand[],
  state: SessionState,
): void {
  const lanes = new Set(bands.map((b) => b.lane));
  const numLanes = lanes.size;
  const markerLaneWidth = 40;

  const width = markerLaneWidth + numLanes * LANE_WIDTH + LANE_START_X * 2 + GEL_PADDING * 2;
  const height = 420;

  canvas.width = width;
  canvas.height = height;

  const ctx = canvas.getContext("2d")!;

  // 3D shadow
  ctx.fillStyle = "rgba(0, 0, 0, 0.3)";
  ctx.fillRect(
    SHADOW_OFFSET + GEL_PADDING,
    SHADOW_OFFSET + GEL_PADDING,
    width - GEL_PADDING * 2,
    height - GEL_PADDING * 2,
  );

  // Gel background
  ctx.fillStyle = GEL_BG;
  ctx.fillRect(
    GEL_PADDING,
    GEL_PADDING,
    width - GEL_PADDING * 2,
    height - GEL_PADDING * 2,
  );

  const gelTop = GEL_PADDING + 10;
  const gelHeight = height - GEL_PADDING * 2 - 20;

  // Map position range to gel area
  const minPos = mobility(80000);
  const maxPos = mobility(5000);
  const posRange = maxPos - minPos;

  const mapY = (pos: number) =>
    gelTop + ((pos - minPos) / posRange) * gelHeight;

  // Draw MW markers
  const markerX = GEL_PADDING + 5;
  ctx.fillStyle = "#333";
  ctx.font = "10px monospace";
  ctx.textAlign = "right";

  ctx.fillText("Mr", markerX + 25, gelTop - 2);

  MW_MARKERS.forEach((mw, i) => {
    const y = mapY(mobility(mw));
    ctx.fillStyle = "#666";
    ctx.fillRect(markerX, y, 30, 1);
    ctx.fillStyle = "#333";
    ctx.fillText(MW_LABELS[i], markerX + 25, y - 2);
  });

  // Draw bands
  const bandColor = state.showBlot ? "rgb(0, 0, 0)" : "rgb(0, 0, 255)";
  const sortedLanes = Array.from(lanes).sort((a, b) => a - b);

  sortedLanes.forEach((lane, laneIdx) => {
    const laneX =
      GEL_PADDING + markerLaneWidth + LANE_START_X + laneIdx * LANE_WIDTH;

    // Lane separator
    ctx.strokeStyle = "rgba(0, 0, 0, 0.1)";
    ctx.beginPath();
    ctx.moveTo(laneX, gelTop);
    ctx.lineTo(laneX, gelTop + gelHeight);
    ctx.stroke();

    // Lane label
    ctx.fillStyle = "#333";
    ctx.font = "9px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(String(lane), laneX + LANE_WIDTH / 2, gelTop - 2);

    const laneBands = bands.filter((b) => b.lane === lane);
    laneBands.forEach((band) => {
      // Immunoblot: only show enzyme
      if (state.showBlot && band.proteinIndex !== state.enzymeIndex) return;

      if (band.intensity < 0.001) return;

      const y = mapY(band.position);
      let bandHeight: number;
      if (band.intensity < 0.05) {
        bandHeight = 1;
      } else if (band.intensity < 0.2) {
        bandHeight = 2;
      } else if (band.intensity < 0.5) {
        bandHeight = 3;
      } else {
        bandHeight = 4;
      }

      ctx.fillStyle = bandColor;
      const bandWidth = LANE_WIDTH - 6;
      ctx.fillRect(
        laneX + 3,
        y - bandHeight / 2,
        bandWidth,
        bandHeight,
      );
    });
  });
}

function renderGel2D(
  canvas: HTMLCanvasElement,
  spots: GelSpot[],
  state: SessionState,
): void {
  const width = 550;
  const height = 450;

  canvas.width = width;
  canvas.height = height;

  const ctx = canvas.getContext("2d")!;

  const gelLeft = 50;
  const gelTop = 40;
  const gelWidth = width - 80;
  const gelHeight = height - 80;

  // 3D shadow
  ctx.fillStyle = "rgba(0, 0, 0, 0.3)";
  ctx.fillRect(
    gelLeft + SHADOW_OFFSET,
    gelTop + SHADOW_OFFSET,
    gelWidth,
    gelHeight,
  );

  // Gel background
  ctx.fillStyle = GEL_BG;
  ctx.fillRect(gelLeft, gelTop, gelWidth, gelHeight);

  // pH axis labels (top)
  ctx.fillStyle = "#333";
  ctx.font = "11px sans-serif";
  ctx.textAlign = "center";

  const phMin = 4.0;
  const phMax = 9.0;
  for (let ph = 4; ph <= 9; ph++) {
    const xFrac = (ph - phMin) / (phMax - phMin);
    const px = gelLeft + xFrac * gelWidth;
    ctx.fillText(String(ph), px, gelTop - 5);
    ctx.fillStyle = "rgba(0, 0, 0, 0.15)";
    ctx.fillRect(px, gelTop, 1, gelHeight);
    ctx.fillStyle = "#333";
  }

  ctx.textAlign = "left";
  ctx.fillText("pH", gelLeft - 20, gelTop - 5);

  // MW labels (left side)
  const minPos = mobility(80000);
  const maxPos = mobility(5000);
  const posRange = maxPos - minPos;

  const mapY = (pos: number) =>
    gelTop + ((pos - minPos) / posRange) * gelHeight;

  ctx.font = "9px monospace";
  ctx.textAlign = "right";
  MW_MARKERS.forEach((mw, i) => {
    const y = mapY(mobility(mw));
    ctx.fillStyle = "#333";
    ctx.fillText(MW_LABELS[i], gelLeft - 5, y + 3);
    ctx.fillStyle = "rgba(0, 0, 0, 0.1)";
    ctx.fillRect(gelLeft, y, gelWidth, 1);
  });

  // X range for spots: x values are (isopoint - 4.0) * 100.0
  // So x ranges from 0 (pI=4) to 500 (pI=9)
  const xRange = (phMax - phMin) * 100.0;

  const spotColor = state.showBlot ? "rgb(0, 0, 0)" : "rgb(0, 0, 255)";

  spots.forEach((spot) => {
    if (state.showBlot && spot.proteinIndex !== state.enzymeIndex) return;
    if (spot.intensity < 0.0005) return;

    const px = gelLeft + (spot.x / xRange) * gelWidth;
    const py = mapY(spot.y);

    ctx.fillStyle = spotColor;

    if (spot.intensity < 0.001) {
      // Line
      ctx.fillRect(px - 1, py - 1, 2, 2);
    } else if (spot.intensity < 0.01) {
      // Small hexagon
      drawPolygon(ctx, px, py, 3, 6);
    } else if (spot.intensity < 0.1) {
      // Medium hexagon
      drawPolygon(ctx, px, py, 5, 6);
    } else if (spot.intensity < 0.2) {
      // Octagon
      drawPolygon(ctx, px, py, 7, 8);
    } else if (spot.intensity < 0.5) {
      // Large polygon
      drawPolygon(ctx, px, py, 9, 10);
    } else {
      // Complex starburst
      drawPolygon(ctx, px, py, 11, 16);
    }
  });
}

function drawPolygon(
  ctx: CanvasRenderingContext2D,
  cx: number,
  cy: number,
  radius: number,
  sides: number,
): void {
  ctx.beginPath();
  for (let i = 0; i < sides; i++) {
    const angle = (i / sides) * Math.PI * 2 - Math.PI / 2;
    const x = cx + radius * Math.cos(angle);
    const y = cy + radius * Math.sin(angle);
    if (i === 0) {
      ctx.moveTo(x, y);
    } else {
      ctx.lineTo(x, y);
    }
  }
  ctx.closePath();
  ctx.fill();
}

export { isGelBand };
