const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

const DEFAULT_TIMEOUT_MS = 75000;

class ApiError extends Error {
  constructor(message, status = null, code = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

async function fetchWithTimeout(url, options = {}, timeoutMs = DEFAULT_TIMEOUT_MS) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  const customSignal = options.signal;
  if (customSignal) {
    customSignal.addEventListener("abort", () => controller.abort());
  }

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    return response;
  } catch (err) {
    clearTimeout(timeoutId);
    if (err.name === "AbortError") {
      throw new ApiError("Request timed out after 75 seconds", 408, "TIMEOUT");
    }
    throw new ApiError(err.message || "Network error", 0, "NETWORK_ERROR");
  }
}

export async function checkHealth() {
  try {
    const resp = await fetchWithTimeout(`${API_BASE_URL}/api/health`, { method: "GET" }, 5000);
    return resp.ok;
  } catch (_err) {
    return false;
  }
}

export async function getMeta(signal) {
  const resp = await fetchWithTimeout(
    `${API_BASE_URL}/api/meta`,
    {
      method: "GET",
      headers: { Accept: "application/json" },
      signal,
    },
    10000
  );
  if (!resp.ok) {
    throw new ApiError("Failed to fetch metadata", resp.status);
  }
  return resp.json();
}

export async function getSources(signal) {
  const resp = await fetchWithTimeout(
    `${API_BASE_URL}/api/sources`,
    {
      method: "GET",
      headers: { Accept: "application/json" },
      signal,
    },
    10000
  );
  if (!resp.ok) {
    throw new ApiError("Failed to fetch sources", resp.status);
  }
  return resp.json();
}

export async function triageSymptoms(payload, signal) {
  let bodyObj;
  if (typeof payload === "string") {
    bodyObj = { message: payload.trim() };
  } else {
    bodyObj = {
      message: (payload.message || "").trim(),
      ...(payload.skip_intake ? { skip_intake: true } : {}),
      ...(payload.intake ? { intake: payload.intake } : {}),
    };
  }

  const resp = await fetchWithTimeout(
    `${API_BASE_URL}/api/triage`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(bodyObj),
      signal,
    },
    DEFAULT_TIMEOUT_MS
  );

  if (!resp.ok) {
    let errorDetail = "Server error occurred";
    try {
      const errJson = await resp.json();
      if (errJson.detail) {
        errorDetail = typeof errJson.detail === "string" ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch (_e) {
      // Use fallback
    }
    throw new ApiError(errorDetail, resp.status);
  }

  return resp.json();
}
