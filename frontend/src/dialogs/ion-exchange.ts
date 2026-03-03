/**
 * Ion exchange parameter dialog (3-step chain).
 * Spec Section 10.4.
 */

import { showDialog } from "../components/dialog-base";
import { createSpinner } from "../components/spinner";

export interface IonExchangeParams {
  media: string;
  ph: number;
  gradientType: "salt" | "ph";
  startGrad: number;
  endGrad: number;
}

const MEDIA_OPTIONS = [
  { value: "deae_cellulose", label: "DEAE-cellulose" },
  { value: "cm_cellulose", label: "CM-cellulose" },
  { value: "q_sepharose", label: "Q-Sepharose" },
  { value: "s_sepharose", label: "S-Sepharose" },
];

export async function showIonExchangeDialog(): Promise<IonExchangeParams | null> {
  // Step 1: Media selection
  const step1 = showDialog("Ion Exchange - Select Media");
  const mediaGroup = document.createElement("div");
  mediaGroup.className = "radio-group";

  MEDIA_OPTIONS.forEach((m, i) => {
    const row = document.createElement("label");
    row.className = "radio-row";
    const radio = document.createElement("input");
    radio.type = "radio";
    radio.name = "ix-media";
    radio.value = m.value;
    if (i === 0) radio.checked = true;
    const text = document.createElement("span");
    text.textContent = m.label;
    row.appendChild(radio);
    row.appendChild(text);
    mediaGroup.appendChild(row);
  });
  step1.content.appendChild(mediaGroup);

  const ok1 = await step1.promise;
  if (!ok1) return null;

  const selectedMedia =
    step1.content.querySelector<HTMLInputElement>(
      'input[name="ix-media"]:checked',
    )?.value ?? MEDIA_OPTIONS[0].value;

  // Step 2: pH selection
  const step2 = showDialog("Ion Exchange - Set pH");
  const phSpinner = createSpinner({
    min: 4.0,
    max: 10.0,
    step: 0.5,
    value: 7.0,
    label: "pH",
    decimals: 1,
  });
  step2.content.appendChild(phSpinner.element);

  const ok2 = await step2.promise;
  if (!ok2) return null;

  const ph = phSpinner.getValue();

  // Step 3: Gradient type and values
  const step3 = showDialog("Ion Exchange - Gradient");

  const gradTypeGroup = document.createElement("div");
  gradTypeGroup.className = "radio-group";
  gradTypeGroup.style.marginBottom = "1rem";

  const saltLabel = document.createElement("label");
  saltLabel.className = "radio-row";
  const saltRadio = document.createElement("input");
  saltRadio.type = "radio";
  saltRadio.name = "ix-grad-type";
  saltRadio.value = "salt";
  saltRadio.checked = true;
  saltLabel.appendChild(saltRadio);
  saltLabel.appendChild(document.createTextNode("Salt gradient (M NaCl)"));
  gradTypeGroup.appendChild(saltLabel);

  const phLabel = document.createElement("label");
  phLabel.className = "radio-row";
  const phRadio = document.createElement("input");
  phRadio.type = "radio";
  phRadio.name = "ix-grad-type";
  phRadio.value = "ph";
  phLabel.appendChild(phRadio);
  phLabel.appendChild(document.createTextNode("pH gradient"));
  gradTypeGroup.appendChild(phLabel);

  step3.content.appendChild(gradTypeGroup);

  const startSpinner = createSpinner({
    min: 0.0,
    max: 1.0,
    step: 0.05,
    value: 0.0,
    label: "Start",
    decimals: 2,
  });
  const endSpinner = createSpinner({
    min: 0.0,
    max: 1.0,
    step: 0.05,
    value: 0.5,
    label: "End",
    decimals: 2,
  });

  const updateSpinnerRanges = () => {
    const isSalt = saltRadio.checked;
    if (isSalt) {
      startSpinner.setValue(0.0);
      endSpinner.setValue(0.5);
    } else {
      const isAnion =
        selectedMedia === "deae_cellulose" ||
        selectedMedia === "q_sepharose";
      if (isAnion) {
        startSpinner.setValue(ph);
        endSpinner.setValue(4.0);
      } else {
        startSpinner.setValue(ph);
        endSpinner.setValue(10.0);
      }
    }
  };

  saltRadio.addEventListener("change", updateSpinnerRanges);
  phRadio.addEventListener("change", updateSpinnerRanges);

  step3.content.appendChild(startSpinner.element);
  step3.content.appendChild(endSpinner.element);

  const ok3 = await step3.promise;
  if (!ok3) return null;

  const gradientType = step3.content.querySelector<HTMLInputElement>(
    'input[name="ix-grad-type"]:checked',
  )?.value as "salt" | "ph";

  return {
    media: selectedMedia,
    ph,
    gradientType,
    startGrad: startSpinner.getValue(),
    endGrad: endSpinner.getValue(),
  };
}
