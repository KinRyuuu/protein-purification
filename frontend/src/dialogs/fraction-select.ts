/**
 * Fraction selection dialogs.
 * Spec Section 10.7.
 */

import { showDialog } from "../components/dialog-base";
import { createSpinner } from "../components/spinner";

/** Multi-select fractions for 1D PAGE. */
export async function showFractionMultiSelect(
  maxFraction: number,
): Promise<number[] | null> {
  const { content, promise } = showDialog("Select Fractions for 1D PAGE", {
    wide: true,
  });

  const instructions = document.createElement("p");
  instructions.textContent = "Select fractions to load on the gel:";
  instructions.style.marginBottom = "0.5rem";
  content.appendChild(instructions);

  const grid = document.createElement("div");
  grid.className = "fraction-grid";

  const checkboxes: HTMLInputElement[] = [];
  const step = Math.max(1, Math.floor(maxFraction / 25));
  for (let f = 1; f <= maxFraction; f += step) {
    const label = document.createElement("label");
    label.className = "fraction-checkbox";
    const cb = document.createElement("input");
    cb.type = "checkbox";
    cb.value = String(f);
    checkboxes.push(cb);
    label.appendChild(cb);
    label.appendChild(document.createTextNode(` ${f}`));
    grid.appendChild(label);
  }
  content.appendChild(grid);

  const ok = await promise;
  if (!ok) return null;

  const selected = checkboxes
    .filter((cb) => cb.checked)
    .map((cb) => parseInt(cb.value));
  return selected.length > 0 ? selected : null;
}

/** Single fraction select for 2D PAGE. */
export async function showFractionSingleSelect(
  maxFraction: number,
): Promise<number | null> {
  const { content, promise } = showDialog("Select Fraction for 2D PAGE");

  const spinner = createSpinner({
    min: 1,
    max: maxFraction,
    step: 1,
    value: 1,
    label: "Fraction number",
  });
  content.appendChild(spinner.element);

  const ok = await promise;
  if (!ok) return null;
  return spinner.getValue();
}

/** Pool range selection. */
export async function showPoolRangeDialog(
  maxFraction: number,
  preStart?: number,
  preEnd?: number,
): Promise<{ start: number; end: number } | null> {
  const { content, promise } = showDialog("Pool Fractions");

  const startSpinner = createSpinner({
    min: 1,
    max: maxFraction,
    step: 1,
    value: preStart ?? 1,
    label: "Start fraction",
  });
  content.appendChild(startSpinner.element);

  const endSpinner = createSpinner({
    min: 1,
    max: maxFraction,
    step: 1,
    value: preEnd ?? maxFraction,
    label: "End fraction",
  });
  content.appendChild(endSpinner.element);

  const ok = await promise;
  if (!ok) return null;

  const start = startSpinner.getValue();
  const end = endSpinner.getValue();
  if (start > end) return null;
  return { start, end };
}
