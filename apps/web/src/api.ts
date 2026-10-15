let csrf = "";
export function setCSRF(value: string) {
  csrf = value;
}
export async function api<T>(
  path: string,
  data?: unknown,
  method?: string,
): Promise<T> {
  const response = await fetch("/api" + path, {
    method: method ?? (data === undefined ? "GET" : "POST"),
    headers: {
      "Content-Type": data instanceof File ? data.type : "application/json",
      "X-CSRF-Token": csrf,
    },
    body:
      data === undefined
        ? undefined
        : data instanceof File
          ? data
          : JSON.stringify(data),
  });
  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: `Request failed (${response.status})` }));
    throw new Error(
      typeof error.detail === "string"
        ? error.detail
        : "Please check the form values. " + JSON.stringify(error.detail),
    );
  }
  return response.json();
}
export async function download(path: string, body: unknown, name: string) {
  const response = await fetch("/api" + path, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail ?? "Export failed");
  }
  const url = URL.createObjectURL(await response.blob());
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  URL.revokeObjectURL(url);
}
