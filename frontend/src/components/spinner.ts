/**
 * Numeric spinner input component.
 * Used for parameter entry (saturation %, temperature, pH, etc.)
 */

export interface SpinnerOptions {
  min: number;
  max: number;
  step: number;
  value: number;
  label: string;
  decimals?: number;
}

export interface Spinner {
  element: HTMLElement;
  getValue(): number;
  setValue(v: number): void;
}

export function createSpinner(options: SpinnerOptions): Spinner {
  const decimals = options.decimals ?? (options.step < 1 ? 1 : 0);
  let value = options.value;

  const wrapper = document.createElement("div");
  wrapper.className = "spinner-wrapper";

  const label = document.createElement("label");
  label.className = "spinner-label";
  label.textContent = options.label;
  wrapper.appendChild(label);

  const controls = document.createElement("div");
  controls.className = "spinner-controls";

  const minusBtn = document.createElement("button");
  minusBtn.className = "spinner-btn";
  minusBtn.textContent = "\u2212";
  minusBtn.type = "button";

  const input = document.createElement("input");
  input.className = "spinner-input";
  input.type = "number";
  input.min = String(options.min);
  input.max = String(options.max);
  input.step = String(options.step);
  input.value = value.toFixed(decimals);

  const plusBtn = document.createElement("button");
  plusBtn.className = "spinner-btn";
  plusBtn.textContent = "+";
  plusBtn.type = "button";

  const clamp = (v: number) =>
    Math.min(options.max, Math.max(options.min, v));
  const round = (v: number) =>
    Math.round(v / options.step) * options.step;

  const update = (newVal: number) => {
    value = clamp(round(newVal));
    input.value = value.toFixed(decimals);
    minusBtn.disabled = value <= options.min;
    plusBtn.disabled = value >= options.max;
  };

  minusBtn.addEventListener("click", () => update(value - options.step));
  plusBtn.addEventListener("click", () => update(value + options.step));
  input.addEventListener("change", () => update(parseFloat(input.value) || options.min));

  controls.appendChild(minusBtn);
  controls.appendChild(input);
  controls.appendChild(plusBtn);
  wrapper.appendChild(controls);

  update(value);

  return {
    element: wrapper,
    getValue: () => value,
    setValue: (v: number) => update(v),
  };
}
