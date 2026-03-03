/**
 * HIC parameter dialog.
 * Spec Section 10.5.
 */

import { showDialog } from "../components/dialog-base";
import { createSpinner } from "../components/spinner";

export async function showHICDialog(): Promise<{
  medium: string;
  startGrad: number;
  endGrad: number;
} | null> {
  const { content, promise } = showDialog(
    "Hydrophobic Interaction Chromatography",
  );

  const mediaGroup = document.createElement("div");
  mediaGroup.className = "radio-group";
  mediaGroup.style.marginBottom = "1rem";

  const phenylLabel = document.createElement("label");
  phenylLabel.className = "radio-row";
  const phenylRadio = document.createElement("input");
  phenylRadio.type = "radio";
  phenylRadio.name = "hic-medium";
  phenylRadio.value = "phenyl_sepharose";
  phenylRadio.checked = true;
  phenylLabel.appendChild(phenylRadio);
  phenylLabel.appendChild(document.createTextNode("Phenyl-Sepharose"));
  mediaGroup.appendChild(phenylLabel);

  const octylLabel = document.createElement("label");
  octylLabel.className = "radio-row";
  const octylRadio = document.createElement("input");
  octylRadio.type = "radio";
  octylRadio.name = "hic-medium";
  octylRadio.value = "octyl_sepharose";
  octylLabel.appendChild(octylRadio);
  octylLabel.appendChild(document.createTextNode("Octyl-Sepharose"));
  mediaGroup.appendChild(octylLabel);

  content.appendChild(mediaGroup);

  const heading = document.createElement("p");
  heading.textContent = "Salt gradient (M ammonium sulfate):";
  heading.style.fontWeight = "bold";
  heading.style.marginBottom = "0.5rem";
  content.appendChild(heading);

  const startSpinner = createSpinner({
    min: 0.0,
    max: 3.9,
    step: 0.1,
    value: 2.0,
    label: "Start (M)",
    decimals: 1,
  });
  content.appendChild(startSpinner.element);

  const endSpinner = createSpinner({
    min: 0.0,
    max: 3.9,
    step: 0.1,
    value: 0.0,
    label: "End (M)",
    decimals: 1,
  });
  content.appendChild(endSpinner.element);

  const ok = await promise;
  if (!ok) return null;

  const selected = content.querySelector<HTMLInputElement>(
    'input[name="hic-medium"]:checked',
  );

  return {
    medium: selected?.value ?? "phenyl_sepharose",
    startGrad: startSpinner.getValue(),
    endGrad: endSpinner.getValue(),
  };
}
