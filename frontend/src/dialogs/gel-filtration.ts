/**
 * Gel filtration parameter dialog.
 * Spec Section 10.3.
 */

import { showDialog } from "../components/dialog-base";

const MATRICES = [
  { value: "sephadex_g50", label: "Sephadex G-50", excluded: "30,000", included: "1,500" },
  { value: "sephadex_g100", label: "Sephadex G-100", excluded: "150,000", included: "4,000" },
  { value: "sephacryl_s200hr", label: "Sephacryl S-200-HR", excluded: "220,000", included: "5,500" },
  { value: "ultrogel_aca54", label: "Ultrogel ACA 54", excluded: "70,000", included: "6,000" },
  { value: "ultrogel_aca44", label: "Ultrogel ACA 44", excluded: "130,000", included: "12,000" },
  { value: "ultrogel_aca34", label: "Ultrogel ACA 34", excluded: "400,000", included: "20,000" },
  { value: "biogel_p60", label: "Bio-Gel P-60", excluded: "60,000", included: "3,000" },
  { value: "biogel_p150", label: "Bio-Gel P-150", excluded: "150,000", included: "15,000" },
  { value: "biogel_p300", label: "Bio-Gel P-300", excluded: "400,000", included: "60,000" },
];

export async function showGelFiltrationDialog(): Promise<{
  matrix: string;
} | null> {
  const { content, promise } = showDialog("Gel Filtration Chromatography");

  const group = document.createElement("div");
  group.className = "radio-group";

  MATRICES.forEach((m, i) => {
    const row = document.createElement("label");
    row.className = "radio-row";

    const radio = document.createElement("input");
    radio.type = "radio";
    radio.name = "gel-matrix";
    radio.value = m.value;
    if (i === 0) radio.checked = true;

    const text = document.createElement("span");
    text.textContent = `${m.label} (${m.excluded}\u2013${m.included} Da)`;

    row.appendChild(radio);
    row.appendChild(text);
    group.appendChild(row);
  });

  content.appendChild(group);

  const ok = await promise;
  if (!ok) return null;

  const selected = content.querySelector<HTMLInputElement>(
    'input[name="gel-matrix"]:checked',
  );
  return { matrix: selected?.value ?? MATRICES[0].value };
}
