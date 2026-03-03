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
  } else {
    hideView("elution-view");
    hideView("gel-view");
    hideView("record-view");
  }

  // Status banner
  const banner = document.getElementById("status-banner")!;
  if (state.successMessage) {
    banner.textContent = state.successMessage;
    banner.className = "status-complete";
  } else if (state.failureMessage) {
    banner.textContent = state.failureMessage;
    banner.className = "status-failed";
  } else {
    banner.textContent = "";
    banner.className = "hidden";
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
  document.addEventListener("pp-restart", async (e: Event) => {
    const { sessionId } = (e as CustomEvent).detail as { sessionId: string };
    try {
      if (sessionId) await deleteSession(sessionId);
    } catch { /* ignore */ }
    initState();
    hideView("elution-view");
    hideView("gel-view");
    hideView("record-view");
    const banner = document.getElementById("status-banner")!;
    banner.textContent = "";
    banner.className = "hidden";
    showView("splash-view");
    renderSplash(document.getElementById("splash-view")!);
  });

  // Listen for pool requests from elution view drag-select
  document.addEventListener("pool-request", ((e: CustomEvent) => {
    const { start, end } = e.detail as { start: number; end: number };
    handlePool(start, end);
  }) as EventListener);
}

main();
