/**
 * Application entry point.
 * Initializes i18n, connects to backend API, and renders splash screen.
 */

import { initApi, deleteSession } from "./api";
import { initState, onStateChange, type SessionState } from "./state";
import { renderSplash } from "./views/splash";
import { renderRecord } from "./views/record";
import { renderElutionProfile } from "./views/elution";
import { renderGel } from "./views/gel";
import {
  renderToolbar,
  updateToolbarState,
  handlePool,
  gelVisible,
} from "./components/toolbar";
import { showAlert } from "./components/dialog-base";

function showView(id: string): void {
  document.getElementById(id)?.classList.remove("hidden");
}

function hideView(id: string): void {
  document.getElementById(id)?.classList.add("hidden");
}

function handleStateChange(state: SessionState): void {
  const toolbarEl = document.getElementById("toolbar")!;
  if (toolbarEl.children.length === 0) {
    renderToolbar(toolbarEl);
  }
  updateToolbarState(state);

  if (state.phase === "running" || state.phase === "finished") {
    hideView("splash-view");

    // Elution profile
    if (state.hasFractions && state.fractions.length > 0) {
      showView("elution-view");
      const elutionView = document.getElementById("elution-view")!;
      renderElutionProfile(elutionView, state);
    } else {
      hideView("elution-view");
    }

    // Gel view
    if (state.gelData && gelVisible) {
      showView("gel-view");
      const gelView = document.getElementById("gel-view")!;
      renderGel(gelView, state);
    } else if (!gelVisible) {
      hideView("gel-view");
    }

    // Record view
    showView("record-view");
    const recordView = document.getElementById("record-view")!;
    renderRecord(
      recordView,
      state.records,
      state.mixtureName,
      state.enzymeIndex,
    );

    // Failure detection
    if (state.failureMessage) {
      showAlert("Oops!", state.failureMessage);
    }

  } else {
    hideView("elution-view");
    hideView("gel-view");
    hideView("record-view");
  }
}

async function main(): Promise<void> {
  initApi();
  initState();

  // Render splash screen
  const splashView = document.getElementById("splash-view")!;
  renderSplash(splashView);

  // Listen for state changes
  onStateChange(handleStateChange);

  // Listen for restart requests from toolbar
  document.addEventListener("pp-restart", (async (e: CustomEvent) => {
    const { sessionId } = e.detail as { sessionId: string };
    try {
      if (sessionId) await deleteSession(sessionId);
    } catch { /* ignore */ }
    initState();
    hideView("elution-view");
    hideView("gel-view");
    hideView("record-view");
    showView("splash-view");
    renderSplash(document.getElementById("splash-view")!);
  }) as EventListener);

  // Listen for pool requests from elution view drag-select
  document.addEventListener("pool-request", ((e: CustomEvent) => {
    const { start, end } = e.detail as { start: number; end: number };
    handlePool(start, end);
  }) as EventListener);
}

main();
