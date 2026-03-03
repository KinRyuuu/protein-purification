/**
 * Purification record table view.
 * Spec Section 8.
 */

import type { StepRecord } from "../state";

const METHOD_LABELS: Record<string, string> = {
  Initial: "Initial",
  "Ammonium sulfate": "Ammonium sulfate",
  "Heat treatment": "Heat treatment",
  "Gel filtration": "Gel filtration",
  "Ion exchange": "Ion exchange",
  HIC: "Hydrophobic interaction",
  Affinity: "Affinity chromatography",
};

export function renderRecord(
  container: HTMLElement,
  records: StepRecord[],
  mixtureName?: string,
  enzymeIndex?: number,
): void {
  container.innerHTML = "";

  const titleEl = document.createElement("h2");
  titleEl.className = "record-title";
  if (enzymeIndex !== undefined && mixtureName) {
    titleEl.textContent = `Purification of protein ${enzymeIndex + 1} from ${mixtureName}`;
  } else {
    titleEl.textContent = "Purification Record";
  }
  container.appendChild(titleEl);

  if (records.length === 0) {
    const empty = document.createElement("p");
    empty.className = "record-empty";
    empty.textContent =
      "Records of subsequent purification steps will be added here.";
    container.appendChild(empty);
    return;
  }

  const table = document.createElement("table");
  table.className = "record-table";

  const thead = document.createElement("thead");
  const headerRow = document.createElement("tr");
  const headers = [
    "Method",
    "Protein (mg)",
    "Enzyme (Units)",
    "Yield (%)",
    "Enrichment",
    "Cost",
  ];
  headers.forEach((h) => {
    const th = document.createElement("th");
    th.textContent = h;
    headerRow.appendChild(th);
  });
  thead.appendChild(headerRow);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  records.forEach((rec) => {
    const tr = document.createElement("tr");

    const methodTd = document.createElement("td");
    methodTd.textContent = METHOD_LABELS[rec.stepType] ?? rec.stepType;
    tr.appendChild(methodTd);

    const proteinTd = document.createElement("td");
    proteinTd.textContent = rec.proteinAmount.toFixed(2);
    tr.appendChild(proteinTd);

    const enzymeTd = document.createElement("td");
    enzymeTd.textContent = rec.enzymeUnits.toFixed(2);
    tr.appendChild(enzymeTd);

    const yieldTd = document.createElement("td");
    yieldTd.textContent = rec.enzymeYield.toFixed(1);
    tr.appendChild(yieldTd);

    const enrichTd = document.createElement("td");
    enrichTd.textContent = rec.enrichment.toFixed(2);
    tr.appendChild(enrichTd);

    const costTd = document.createElement("td");
    costTd.textContent = rec.costPerUnit.toFixed(2);
    tr.appendChild(costTd);

    tbody.appendChild(tr);
  });
  table.appendChild(tbody);

  container.appendChild(table);
}

export function showStepResultDialog(record: StepRecord): void {
  const overlay = document.getElementById("dialog-overlay")!;
  overlay.innerHTML = "";
  overlay.classList.remove("hidden");

  const dialog = document.createElement("div");
  dialog.className = "dialog-box";

  const title = document.createElement("div");
  title.className = "dialog-title";
  title.textContent = "Step Result";
  dialog.appendChild(title);

  const content = document.createElement("div");
  content.className = "dialog-content";

  const rows = [
    ["Protein amount:", `${record.proteinAmount.toFixed(2)} mg`],
    ["Enzyme units:", record.enzymeUnits.toFixed(2)],
    ["Enrichment:", `${record.enrichment.toFixed(2)} fold`],
    ["Enzyme yield:", `${record.enzymeYield.toFixed(1)}%`],
    ["Cost per unit:", record.costPerUnit.toFixed(2)],
  ];

  rows.forEach(([label, value]) => {
    const row = document.createElement("div");
    row.className = "result-row";
    const labelSpan = document.createElement("span");
    labelSpan.className = "result-label";
    labelSpan.textContent = label;
    const valueSpan = document.createElement("span");
    valueSpan.className = "result-value";
    valueSpan.textContent = value;
    row.appendChild(labelSpan);
    row.appendChild(valueSpan);
    content.appendChild(row);
  });

  dialog.appendChild(content);

  const buttonRow = document.createElement("div");
  buttonRow.className = "dialog-buttons";
  const okBtn = document.createElement("button");
  okBtn.className = "dialog-btn dialog-btn-ok";
  okBtn.textContent = "OK";
  okBtn.addEventListener("click", () => {
    overlay.classList.add("hidden");
    overlay.innerHTML = "";
  });
  buttonRow.appendChild(okBtn);
  dialog.appendChild(buttonRow);

  overlay.appendChild(dialog);
}
