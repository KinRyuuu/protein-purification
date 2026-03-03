/**
 * Heat treatment parameter dialog.
 * Spec Section 10.2.
 */

import { showDialog } from "../components/dialog-base";
import { createSpinner } from "../components/spinner";

export async function showHeatTreatmentDialog(): Promise<{
  temperature: number;
  duration: number;
} | null> {
  const { content, promise } = showDialog("Heat Treatment");

  const tempSpinner = createSpinner({
    min: 20,
    max: 100,
    step: 1,
    value: 50,
    label: "Temperature (\u00b0C)",
  });
  content.appendChild(tempSpinner.element);

  const durationSpinner = createSpinner({
    min: 1,
    max: 60,
    step: 1,
    value: 10,
    label: "Duration (minutes)",
  });
  content.appendChild(durationSpinner.element);

  const ok = await promise;
  if (!ok) return null;
  return {
    temperature: tempSpinner.getValue(),
    duration: durationSpinner.getValue(),
  };
}
