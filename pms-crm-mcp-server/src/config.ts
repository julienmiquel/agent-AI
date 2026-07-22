/**
 * Configuration and Helper for ECG PMS & CRM MCP App
 */

const FALLBACK_API_DOMAIN = "https://ecg-pms-crm-mcp-app-ahavst3hhq-uc.a.run.app";

export function isEmbeddedInHost(): boolean {
  try {
    return (
      window.self !== window.top ||
      window.location.origin.includes("gstatic.com") ||
      window.location.origin.includes("google.com") ||
      window.location.origin === "null" ||
      window.location.protocol === "about:"
    );
  } catch {
    return true;
  }
}

export function shouldPerformDirectHttpFetch(): boolean {
  return !isEmbeddedInHost();
}

export function getApiBaseUrl(): string {
  if (shouldPerformDirectHttpFetch()) {
    try {
      const origin = window.location.origin;
      if (origin && origin.startsWith("http")) {
        return origin;
      }
    } catch (e) {
      console.warn("Could not determine window.location.origin:", e);
    }
  }
  return FALLBACK_API_DOMAIN;
}
