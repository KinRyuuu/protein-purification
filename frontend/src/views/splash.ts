/**
 * Splash screen view.
 * Shows title, author credits, and session start buttons.
 * Spec Section 14.
 */

import {
  createSession,
  loadSession,
  listMixtures,
  chooseMixture,
  chooseEnzyme,
} from "../api";
import { showDialog, showAlert } from "../components/dialog-base";
import { updateState, type SessionState } from "../state";

export function renderSplash(container: HTMLElement): void {
  container.innerHTML = "";

  const splash = document.createElement("div");
  splash.className = "splash-screen";

  const titleShadow = document.createElement("h1");
  titleShadow.className = "splash-title-shadow";
  titleShadow.textContent = "Protein Purification";
  splash.appendChild(titleShadow);

  const title = document.createElement("h1");
  title.className = "splash-title";
  title.textContent = "Protein Purification";
  splash.appendChild(title);

  const author = document.createElement("p");
  author.className = "splash-author";
  author.textContent = "Prof. Andrew Booth";
  splash.appendChild(author);

  const institution = document.createElement("div");
  institution.className = "splash-institution";
  institution.innerHTML =
    "Faculty of Biological Sciences<br>University of Leeds<br>United Kingdom";
  splash.appendChild(institution);

  const buttons = document.createElement("div");
  buttons.className = "splash-buttons";

  const newBtn = document.createElement("button");
  newBtn.className = "splash-btn";
  newBtn.textContent = "New Session";
  newBtn.addEventListener("click", () => startNewSession());

  const loadBtn = document.createElement("button");
  loadBtn.className = "splash-btn";
  loadBtn.textContent = "Load Saved";
  loadBtn.addEventListener("click", () => loadSavedSession());

  buttons.appendChild(newBtn);
  buttons.appendChild(loadBtn);
  splash.appendChild(buttons);

  container.appendChild(splash);
}

async function startNewSession(): Promise<void> {
  try {
    let state = await createSession();
    updateState(state);

    // Show mixture selection dialog
    const mixtures = await listMixtures();
    const mixtureName = await showMixtureDialog(mixtures);
    if (!mixtureName) return;

    state = await chooseMixture(state.sessionId, mixtureName);
    updateState(state);

    // Show enzyme selection dialog
    const enzymeIndex = await showEnzymeDialog(state);
    if (enzymeIndex === null) return;

    state = await chooseEnzyme(state.sessionId, enzymeIndex);
    updateState(state);
  } catch (err) {
    await showAlert("Error", String(err));
  }
}

async function loadSavedSession(): Promise<void> {
  const input = document.createElement("input");
  input.type = "file";
  input.accept = ".ppmixture";

  const file = await new Promise<File | null>((resolve) => {
    input.addEventListener("change", () =>
      resolve(input.files?.[0] ?? null),
    );
    input.click();
  });

  if (!file) return;

  try {
    let state = await loadSession(file);
    updateState(state);

    if (state.phase === "enzyme_selection") {
      const enzymeIndex = await showEnzymeDialog(state);
      if (enzymeIndex === null) return;
      state = await chooseEnzyme(state.sessionId, enzymeIndex);
      updateState(state);
    }
  } catch (err) {
    await showAlert("Error", String(err));
  }
}

async function showMixtureDialog(
  mixtures: string[],
): Promise<string | null> {
  const { content, promise } = showDialog("Select Mixture");

  const group = document.createElement("div");
  group.className = "radio-group";

  mixtures.forEach((name, i) => {
    const row = document.createElement("label");
    row.className = "radio-row";
    const radio = document.createElement("input");
    radio.type = "radio";
    radio.name = "mixture";
    radio.value = name;
    if (i === 0) radio.checked = true;
    const text = document.createElement("span");
    text.textContent = name;
    row.appendChild(radio);
    row.appendChild(text);
    group.appendChild(row);
  });

  content.appendChild(group);

  const ok = await promise;
  if (!ok) return null;

  const selected = content.querySelector<HTMLInputElement>(
    'input[name="mixture"]:checked',
  );
  return selected?.value ?? mixtures[0];
}

async function showEnzymeDialog(
  state: SessionState,
): Promise<number | null> {
  const { content, promise } = showDialog("Select Target Enzyme");

  const info = document.createElement("p");
  info.textContent = "Select the protein you wish to purify:";
  info.style.marginBottom = "0.5rem";
  content.appendChild(info);

  const group = document.createElement("div");
  group.className = "radio-group";

  state.proteins.forEach((p) => {
    const row = document.createElement("label");
    row.className = "radio-row";
    const radio = document.createElement("input");
    radio.type = "radio";
    radio.name = "enzyme";
    radio.value = String(p.index);
    if (p.index === 0) radio.checked = true;
    const text = document.createElement("span");
    text.textContent = `${p.name} (MW: ${p.molWt.toLocaleString()} Da, Amount: ${p.amount.toFixed(1)} mg)`;
    row.appendChild(radio);
    row.appendChild(text);
    group.appendChild(row);
  });

  content.appendChild(group);

  // Show stability info
  const stabilityDiv = document.createElement("div");
  stabilityDiv.className = "stability-info";
  stabilityDiv.style.marginTop = "1rem";
  stabilityDiv.style.fontSize = "0.85em";
  stabilityDiv.style.color = "#666";

  const updateStability = () => {
    const selectedIdx = parseInt(
      content.querySelector<HTMLInputElement>(
        'input[name="enzyme"]:checked',
      )?.value ?? "0",
    );
    const prot = state.proteins[selectedIdx];
    if (prot) {
      stabilityDiv.textContent = `Stability: Temp < ${prot.stability.temp}\u00b0C, pH ${prot.stability.ph1}\u2013${prot.stability.ph2}`;
    }
  };

  group.addEventListener("change", updateStability);
  updateStability();
  content.appendChild(stabilityDiv);

  const ok = await promise;
  if (!ok) return null;

  const selected = content.querySelector<HTMLInputElement>(
    'input[name="enzyme"]:checked',
  );
  return selected ? parseInt(selected.value) : 0;
}
