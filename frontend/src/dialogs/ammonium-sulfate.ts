/**
 * Ammonium sulfate parameter dialog.
 * Spec Section 10.1.
 */

import { showDialog } from "../components/dialog-base";
import { createSpinner } from "../components/spinner";

export async function showAmmoniumSulfateDialog(): Promise<{
  saturation: number;
} | null> {
  const { content, promise } = showDialog("Ammonium Sulfate Fractionation");

  const spinner = createSpinner({
    min: 0,
    max: 100,
    step: 5,
    value: 50,
    label: "Saturation (%)",
  });
  content.appendChild(spinner.element);

  const ok = await promise;
  if (!ok) return null;
  return { saturation: spinner.getValue() };
}

export async function showASChoiceDialog(): Promise<
  "soluble" | "insoluble" | null
> {
  const { content, promise, close } = showDialog(
    "Ammonium Sulfate - Choose Fraction",
    { showCancel: false },
  );

  let choice: "soluble" | "insoluble" | null = null;

  const msg = document.createElement("p");
  msg.textContent = "Which fraction do you want to keep?";
  content.appendChild(msg);

  const btnRow = document.createElement("div");
  btnRow.style.display = "flex";
  btnRow.style.gap = "1rem";
  btnRow.style.marginTop = "1rem";

  const insolBtn = document.createElement("button");
  insolBtn.className = "dialog-btn dialog-btn-ok";
  insolBtn.textContent = "Use insoluble fraction";
  insolBtn.addEventListener("click", () => {
    choice = "insoluble";
    close();
  });

  const solBtn = document.createElement("button");
  solBtn.className = "dialog-btn dialog-btn-ok";
  solBtn.textContent = "Use soluble fraction";
  solBtn.addEventListener("click", () => {
    choice = "soluble";
    close();
  });

  btnRow.appendChild(insolBtn);
  btnRow.appendChild(solBtn);
  content.appendChild(btnRow);

  await promise;
  return choice;
}
