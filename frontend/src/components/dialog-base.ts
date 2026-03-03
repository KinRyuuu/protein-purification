/**
 * Base dialog/modal component.
 * Provides overlay, title, OK/Cancel buttons, and content area.
 * Promise-based API: resolves true on OK, null on Cancel.
 */

export interface DialogResult {
  content: HTMLElement;
  promise: Promise<boolean>;
  close: () => void;
}

export function showDialog(
  title: string,
  options?: {
    okLabel?: string;
    cancelLabel?: string;
    showCancel?: boolean;
    wide?: boolean;
  },
): DialogResult {
  const overlay = document.getElementById("dialog-overlay")!;
  overlay.innerHTML = "";
  overlay.classList.remove("hidden");

  const dialog = document.createElement("div");
  dialog.className = "dialog-box" + (options?.wide ? " dialog-wide" : "");

  const titleBar = document.createElement("div");
  titleBar.className = "dialog-title";
  titleBar.textContent = title;
  dialog.appendChild(titleBar);

  const content = document.createElement("div");
  content.className = "dialog-content";
  dialog.appendChild(content);

  const buttonRow = document.createElement("div");
  buttonRow.className = "dialog-buttons";

  let resolvePromise: (value: boolean) => void;
  const promise = new Promise<boolean>((resolve) => {
    resolvePromise = resolve;
  });

  const close = () => {
    overlay.classList.add("hidden");
    overlay.innerHTML = "";
  };

  if (options?.showCancel !== false) {
    const cancelBtn = document.createElement("button");
    cancelBtn.className = "dialog-btn dialog-btn-cancel";
    cancelBtn.textContent = options?.cancelLabel ?? "Cancel";
    cancelBtn.addEventListener("click", () => {
      close();
      resolvePromise(false);
    });
    buttonRow.appendChild(cancelBtn);
  }

  const okBtn = document.createElement("button");
  okBtn.className = "dialog-btn dialog-btn-ok";
  okBtn.textContent = options?.okLabel ?? "OK";
  okBtn.addEventListener("click", () => {
    close();
    resolvePromise(true);
  });
  buttonRow.appendChild(okBtn);

  dialog.appendChild(buttonRow);
  overlay.appendChild(dialog);

  return { content, promise, close };
}

export function showAlert(title: string, message: string): Promise<void> {
  const { content, promise } = showDialog(title, { showCancel: false });
  const p = document.createElement("p");
  p.textContent = message;
  content.appendChild(p);
  return promise.then(() => {});
}

export function showConfirm(title: string, message: string): Promise<boolean> {
  const { content, promise } = showDialog(title);
  const p = document.createElement("p");
  p.textContent = message;
  content.appendChild(p);
  return promise;
}

export function closeDialog(): void {
  const overlay = document.getElementById("dialog-overlay")!;
  overlay.classList.add("hidden");
  overlay.innerHTML = "";
}
