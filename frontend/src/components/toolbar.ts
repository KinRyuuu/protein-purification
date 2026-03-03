/**
 * Horizontal toolbar replacing traditional menus.
 * Sections: Separation, Analysis, Fractions.
 * Buttons enabled/disabled by session state.
 */

import {
  runSeparation,
  asChoice,
  runAssay,
  dilute,
  poolFractions,
  abandonStep,
  run1dPage,
  run2dPage,
  toggleStain,
  downloadSave,
} from "../api";
import type { SessionState } from "../state";
import { getState, updateState } from "../state";
import { showAlert, showConfirm } from "./dialog-base";
import {
  showAmmoniumSulfateDialog,
  showASChoiceDialog,
} from "../dialogs/ammonium-sulfate";
import { showHeatTreatmentDialog } from "../dialogs/heat-treatment";
import { showGelFiltrationDialog } from "../dialogs/gel-filtration";
import { showIonExchangeDialog } from "../dialogs/ion-exchange";
import { showHICDialog } from "../dialogs/hic";
import { showAffinityDialog } from "../dialogs/affinity";
import {
  showFractionMultiSelect,
  showFractionSingleSelect,
  showPoolRangeDialog,
} from "../dialogs/fraction-select";
import { showStepResultDialog } from "../views/record";

interface ToolbarButton {
  id: string;
  label: string;
  handler: () => Promise<void>;
}

let buttons: Map<string, HTMLButtonElement> = new Map();
let gelVisible = false;

function sid(): string {
  return getState()?.sessionId ?? "";
}

async function handleError(fn: () => Promise<void>): Promise<void> {
  try {
    await fn();
  } catch (err) {
    await showAlert("Error", String(err));
  }
}

async function handleAmmoniumSulfate(): Promise<void> {
  const params = await showAmmoniumSulfateDialog();
  if (!params) return;

  const state = await runSeparation(sid(), {
    type: "ammonium_sulfate",
    saturation: params.saturation,
  });
  updateState(state);

  if (state.asResult) {
    const choice = await showASChoiceDialog();
    if (!choice) return;
    const newState = await asChoice(sid(), choice);
    updateState(newState);
    showLatestStepResult(newState);
  }
}

async function handleHeatTreatment(): Promise<void> {
  const params = await showHeatTreatmentDialog();
  if (!params) return;

  const state = await runSeparation(sid(), {
    type: "heat_treatment",
    temperature: params.temperature,
    duration: params.duration,
  });
  updateState(state);
  showLatestStepResult(state);
}

async function handleGelFiltration(): Promise<void> {
  const params = await showGelFiltrationDialog();
  if (!params) return;

  const state = await runSeparation(sid(), {
    type: "gel_filtration",
    matrix: params.matrix,
  });
  updateState(state);
}

async function handleIonExchange(): Promise<void> {
  const params = await showIonExchangeDialog();
  if (!params) return;

  const state = await runSeparation(sid(), {
    type: "ion_exchange",
    media: params.media,
    ph: params.ph,
    gradientType: params.gradientType,
    startGrad: params.startGrad,
    endGrad: params.endGrad,
  });
  updateState(state);
}

async function handleHIC(): Promise<void> {
  const params = await showHICDialog();
  if (!params) return;

  let state = await runSeparation(sid(), {
    type: "hic",
    medium: params.medium,
    startGrad: params.startGrad,
    endGrad: params.endGrad,
  });

  if (state.hicPrecipitation && state.hicPrecipitation >= 0.001) {
    const proceed = await showConfirm(
      "Precipitation Warning",
      `${(state.hicPrecipitation * 100).toFixed(1)}% of protein will precipitate at this salt concentration. Continue?`,
    );
    if (!proceed) return;

    state = await runSeparation(sid(), {
      type: "hic",
      medium: params.medium,
      startGrad: params.startGrad,
      endGrad: params.endGrad,
      confirmed: true,
    });
  }

  updateState(state);
}

async function handleAffinity(): Promise<void> {
  const params = await showAffinityDialog();
  if (!params) return;

  const state = await runSeparation(sid(), {
    type: "affinity",
    ligand: params.ligand,
    elution: params.elutionMethod,
  });
  updateState(state);
}

async function handle1dPage(): Promise<void> {
  const fractions = await showFractionMultiSelect(125);
  if (!fractions) return;

  const state = await run1dPage(sid(), fractions);
  updateState(state);
  gelVisible = true;
}

async function handle2dPage(): Promise<void> {
  const fraction = await showFractionSingleSelect(125);
  if (fraction === null) return;

  const state = await run2dPage(sid(), fraction);
  updateState(state);
  gelVisible = true;
}

async function handleToggleStain(): Promise<void> {
  const state = await toggleStain(sid());
  updateState(state);
}

function handleHideGel(): void {
  gelVisible = false;
  const gelView = document.getElementById("gel-view");
  if (gelView) gelView.classList.add("hidden");
}

async function handleAssay(): Promise<void> {
  const state = await runAssay(sid());
  updateState(state);
}

async function handleDilute(): Promise<void> {
  const state = await dilute(sid());
  updateState(state);
}

export async function handlePool(
  preStart?: number,
  preEnd?: number,
): Promise<void> {
  const range = await showPoolRangeDialog(125, preStart, preEnd);
  if (!range) return;

  const state = await poolFractions(sid(), range.start, range.end);
  updateState(state);
  showLatestStepResult(state);
}

async function handleAbandonStep(): Promise<void> {
  const proceed = await showConfirm(
    "Abandon Step",
    "Discard the current separation and return to the previous state?",
  );
  if (!proceed) return;

  const state = await abandonStep(sid());
  updateState(state);
  gelVisible = false;
}

async function handleSave(): Promise<void> {
  await downloadSave(sid());
}

async function handleRestart(): Promise<void> {
  const proceed = await showConfirm(
    "Restart",
    "Return to the main menu? Your current session will be lost.",
  );
  if (!proceed) return;

  const sessionId = sid();
  document.dispatchEvent(
    new CustomEvent("pp-restart", { detail: { sessionId } }),
  );
}

function showLatestStepResult(state: SessionState): void {
  if (state.records.length > 1) {
    showStepResultDialog(state.records[state.records.length - 1]);
  }
}

const SEPARATION_BUTTONS: ToolbarButton[] = [
  { id: "btn-as", label: "Ammonium Sulfate", handler: () => handleError(handleAmmoniumSulfate) },
  { id: "btn-heat", label: "Heat Treatment", handler: () => handleError(handleHeatTreatment) },
  { id: "btn-gel", label: "Gel Filtration", handler: () => handleError(handleGelFiltration) },
  { id: "btn-ion", label: "Ion Exchange", handler: () => handleError(handleIonExchange) },
  { id: "btn-hic", label: "HIC", handler: () => handleError(handleHIC) },
  { id: "btn-affinity", label: "Affinity", handler: () => handleError(handleAffinity) },
];

const ANALYSIS_BUTTONS: ToolbarButton[] = [
  { id: "btn-1d", label: "1D PAGE", handler: () => handleError(handle1dPage) },
  { id: "btn-2d", label: "2D PAGE", handler: () => handleError(handle2dPage) },
  { id: "btn-stain", label: "Coomassie", handler: () => handleError(handleToggleStain) },
  { id: "btn-hide-gel", label: "Hide Gel", handler: async () => handleHideGel() },
];

const FRACTION_BUTTONS: ToolbarButton[] = [
  { id: "btn-assay", label: "Assay", handler: () => handleError(handleAssay) },
  { id: "btn-dilute", label: "Dilute", handler: () => handleError(handleDilute) },
  { id: "btn-pool", label: "Pool", handler: () => handleError(() => handlePool()) },
  { id: "btn-abandon", label: "Abandon Step", handler: () => handleError(handleAbandonStep) },
];

const FILE_BUTTONS: ToolbarButton[] = [
  { id: "btn-save", label: "Save", handler: () => handleError(handleSave) },
  { id: "btn-restart", label: "Restart", handler: () => handleError(handleRestart) },
];

function createSection(
  label: string,
  btns: ToolbarButton[],
): HTMLElement {
  const section = document.createElement("div");
  section.className = "toolbar-section";

  const sectionLabel = document.createElement("span");
  sectionLabel.className = "toolbar-section-label";
  sectionLabel.textContent = label;
  section.appendChild(sectionLabel);

  btns.forEach((b) => {
    const btn = document.createElement("button");
    btn.className = "toolbar-btn";
    btn.id = b.id;
    btn.textContent = b.label;
    btn.disabled = true;
    btn.addEventListener("click", b.handler);
    buttons.set(b.id, btn);
    section.appendChild(btn);
  });

  return section;
}

export function renderToolbar(container: HTMLElement): void {
  container.innerHTML = "";
  buttons = new Map();

  container.appendChild(createSection("Separation", SEPARATION_BUTTONS));
  container.appendChild(createSection("Analysis", ANALYSIS_BUTTONS));
  container.appendChild(createSection("Fractions", FRACTION_BUTTONS));
  container.appendChild(createSection("File", FILE_BUTTONS));
}

export function updateToolbarState(state: SessionState): void {
  const isRunning = state.phase === "running";

  // Separation buttons: enabled when running and pooled (ready for next step)
  const canSep = isRunning && state.canSeparate;
  ["btn-as", "btn-heat", "btn-gel", "btn-ion", "btn-hic", "btn-affinity"].forEach(
    (id) => {
      const btn = buttons.get(id);
      if (btn) btn.disabled = !canSep;
    },
  );

  // Analysis buttons
  const hasFrac = isRunning && state.hasFractions;
  const btn1d = buttons.get("btn-1d");
  if (btn1d) btn1d.disabled = !hasFrac || state.gelData != null;

  const btn2d = buttons.get("btn-2d");
  if (btn2d) btn2d.disabled = !hasFrac || !state.gelData || state.twoDGel;

  const btnStain = buttons.get("btn-stain");
  if (btnStain) {
    btnStain.disabled = !state.gelData;
    btnStain.textContent = state.showBlot ? "Coomassie" : "Immunoblot";
  }

  const btnHideGel = buttons.get("btn-hide-gel");
  if (btnHideGel) btnHideGel.disabled = !gelVisible;

  // Fraction buttons
  const btnAssay = buttons.get("btn-assay");
  if (btnAssay) btnAssay.disabled = !(isRunning && state.canAssay);

  const btnDilute = buttons.get("btn-dilute");
  if (btnDilute) btnDilute.disabled = !(isRunning && state.canDilute);

  const btnPool = buttons.get("btn-pool");
  if (btnPool) btnPool.disabled = !(isRunning && state.canPool);

  const btnAbandon = buttons.get("btn-abandon");
  if (btnAbandon) btnAbandon.disabled = !(isRunning && hasFrac);

  // File buttons
  const btnSave = buttons.get("btn-save");
  if (btnSave) btnSave.disabled = !isRunning;

  const btnRestart = buttons.get("btn-restart");
  if (btnRestart) btnRestart.disabled = !(isRunning || state.phase === "finished");
}

export { gelVisible };
