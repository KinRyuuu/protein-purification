/**
 * Affinity chromatography parameter dialog (2-step).
 * Spec Section 10.6.
 */

import { showDialog } from "../components/dialog-base";

const LIGANDS = [
  { value: "antibody_a", label: "Antibody A" },
  { value: "antibody_b", label: "Antibody B" },
  { value: "antibody_c", label: "Antibody C" },
  { value: "polyclonal", label: "Polyclonal antibody" },
  { value: "immobilized_inhibitor", label: "Immobilized inhibitor" },
  { value: "ni_nta_agarose", label: "NiNTA-agarose" },
];

const ELUTION_METHODS = [
  { value: "tris_buffer", label: "Tris buffer" },
  { value: "acid_glycine", label: "Acid (glycine)" },
  { value: "inhibitor", label: "Inhibitor" },
  { value: "imidazole", label: "Imidazole" },
];

export async function showAffinityDialog(): Promise<{
  ligand: string;
  elutionMethod: string;
} | null> {
  // Step 1: Ligand selection
  const step1 = showDialog("Affinity Chromatography - Select Ligand");

  const ligandGroup = document.createElement("div");
  ligandGroup.className = "radio-group";

  LIGANDS.forEach((lig, i) => {
    const row = document.createElement("label");
    row.className = "radio-row";
    const radio = document.createElement("input");
    radio.type = "radio";
    radio.name = "aff-ligand";
    radio.value = lig.value;
    if (i === 0) radio.checked = true;
    const text = document.createElement("span");
    text.textContent = lig.label;
    row.appendChild(radio);
    row.appendChild(text);
    ligandGroup.appendChild(row);
  });
  step1.content.appendChild(ligandGroup);

  const ok1 = await step1.promise;
  if (!ok1) return null;

  const selectedLigand =
    step1.content.querySelector<HTMLInputElement>(
      'input[name="aff-ligand"]:checked',
    )?.value ?? LIGANDS[0].value;

  // Step 2: Elution method
  const step2 = showDialog("Affinity Chromatography - Elution Method");

  const elutionGroup = document.createElement("div");
  elutionGroup.className = "radio-group";

  ELUTION_METHODS.forEach((em, i) => {
    const row = document.createElement("label");
    row.className = "radio-row";
    const radio = document.createElement("input");
    radio.type = "radio";
    radio.name = "aff-elution";
    radio.value = em.value;
    if (i === 0) radio.checked = true;
    const text = document.createElement("span");
    text.textContent = em.label;
    row.appendChild(radio);
    row.appendChild(text);
    elutionGroup.appendChild(row);
  });
  step2.content.appendChild(elutionGroup);

  const ok2 = await step2.promise;
  if (!ok2) return null;

  const selectedElution =
    step2.content.querySelector<HTMLInputElement>(
      'input[name="aff-elution"]:checked',
    )?.value ?? ELUTION_METHODS[0].value;

  return { ligand: selectedLigand, elutionMethod: selectedElution };
}
