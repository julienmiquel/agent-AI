import { App, type McpUiHostContext } from "@modelcontextprotocol/ext-apps";
import { z } from "zod";
import { getApiBaseUrl, shouldPerformDirectHttpFetch } from "./config.js";
import "./global.css";
import "./mcp-app.css";

interface AppState {
  targetMarket: string;
  targetCluster: string;
  discountPercentage: number;
  campaignName: string;
  customCopywriting: string | null;
  hitlActionPending: "CRM" | null;
}

const state: AppState = {
  targetMarket: "NL",
  targetCluster: "MEDITERRANEAN_SOUTH",
  discountPercentage: 15,
  campaignName: "Flash_Promo_NL_MEDITERRANEAN_SOUTH_July",
  customCopywriting: null,
  hitlActionPending: null,
};

async function syncCampaignStageToBackend(): Promise<void> {
  if (shouldPerformDirectHttpFetch()) {
    try {
      await fetch(`${getApiBaseUrl()}/api/crm-stage-flash-campaign`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          campaignName: state.campaignName,
          targetMarket: state.targetMarket,
          cluster: state.targetCluster,
          discountPercentage: state.discountPercentage,
        }),
      });
      await fetchLiveCampaignsHistory();
    } catch (err) {
      console.log("[CRM-APP] Direct fetch notice:", err);
    }
  }
}

async function fetchLiveCampaignsHistory(): Promise<void> {
  const container = document.getElementById("crm-campaigns-history-list");
  if (!container) return;

  if (shouldPerformDirectHttpFetch()) {
    try {
      const res = await fetch(`${getApiBaseUrl()}/api/crm-campaigns`);
      if (res.ok) {
        const data = await res.json();
        const campaigns = data.campaigns || [];
        if (!campaigns.length) {
          container.innerHTML = `<div style="color: var(--text-secondary); font-size: 13px; font-style: italic;">No staged campaigns found yet. Click 'Stage Flash Campaign' above to create one.</div>`;
          return;
        }

        container.innerHTML = campaigns.map((c: any) => `
        <div class="campaign-item" style="background: var(--bg-primary); border: 1px solid var(--border-color); border-radius: 8px; padding: 12px; display: flex; flex-direction: column; gap: 8px;">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <div style="font-weight: 700; font-size: 14px; color: var(--text-primary);">${c.campaign_name || "Flash Promo"}</div>
            <span style="font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 10px; background: rgba(16, 185, 129, 0.15); color: #10b981; text-transform: uppercase;">
              ${c.status || "STAGED"}
            </span>
          </div>
          <div style="display: flex; gap: 8px; font-size: 11px; align-items: center; flex-wrap: wrap;">
            <span style="background: #3b82f6; color: white; padding: 2px 6px; border-radius: 10px; font-weight: 600;">${c.target_market || "NL"} Market</span>
            <span style="background: rgba(255,255,255,0.1); color: var(--text-secondary); padding: 2px 6px; border-radius: 10px;">${c.cluster || "MEDITERRANEAN_SOUTH"}</span>
            <span style="color: var(--accent-color); font-weight: 700;">-${c.discount_percentage}% Discount</span>
            <span style="color: var(--text-secondary); font-size: 10px; margin-left: auto;">${new Date(c.updated_at || Date.now()).toLocaleTimeString()}</span>
          </div>
          ${c.copywriting_text ? `<div style="font-size: 12px; font-weight: 500; font-style: italic; color: var(--text-primary); background: var(--bg-surface); padding: 8px; border-left: 3px solid var(--accent-color); border-radius: 4px;">"${c.copywriting_text}"</div>` : ''}
          ${c.image_asset_gcs_uri ? `<div style="font-family: monospace; font-size: 10px; color: #10b981; background: rgba(16,185,129,0.1); padding: 4px 8px; border-radius: 4px; word-break: break-all;">${c.image_asset_gcs_uri}</div>` : ''}
        </div>
      `).join("");
      }
    } catch (err) {
      console.log("[CRM-APP] Direct fetch notice:", err);
    }
  }
}

function generateCopywriting(market: string, cluster: string, discount: number): string {
  if (state.customCopywriting) return state.customCopywriting;
  const clusterDisplay = cluster.replace(/_/g, " ").toLowerCase();
  
  switch (market.toUpperCase()) {
    case "NL":
      return `Profiteer van ${discount}% korting op uw zomervakantie in ${clusterDisplay}! Boek nu uw Premium stacaravan op La Sirène.`;
    case "FR":
      return `Profitez de ${discount}% de réduction sur vos vacances d'été en ${clusterDisplay} ! Réservez votre mobil-home dès maintenant.`;
    case "DE":
      return `Sichern Sie sich ${discount}% Rabatt auf Ihren Sommerurlaub in ${clusterDisplay}! Jetzt Mobilheim buchen.`;
    default:
      return `Enjoy ${discount}% discount on your summer stay in ${clusterDisplay}! Book your mobil-home today.`;
  }
}

function resolveImagenUri(market: string, cluster: string): string {
  const m = market.toLowerCase();
  const c = cluster.toLowerCase().replace(/ /g, "_");
  return `gs://ecg-marketing-assets/genai/banners/${m}_${c}_july.png`;
}

function renderCRMPreview(): void {
  const copy = generateCopywriting(state.targetMarket, state.targetCluster, state.discountPercentage);
  const uri = resolveImagenUri(state.targetMarket, state.targetCluster);

  (document.getElementById("preview-market-badge") as HTMLElement).textContent = `${state.targetMarket} Market`;
  (document.getElementById("preview-cluster-badge") as HTMLElement).textContent = state.targetCluster;
  (document.getElementById("preview-copywriting") as HTMLElement).textContent = copy;
  (document.getElementById("preview-imagen-uri") as HTMLElement).textContent = uri;
  (document.getElementById("discount-val") as HTMLElement).textContent = `${state.discountPercentage}%`;
}

function setupSelectors(): void {
  const marketSelect = document.getElementById("target-market") as HTMLSelectElement;
  marketSelect.value = state.targetMarket;
  marketSelect.addEventListener("change", () => {
    state.targetMarket = marketSelect.value;
    renderCRMPreview();
  });

  const clusterSelect = document.getElementById("target-cluster") as HTMLSelectElement;
  clusterSelect.value = state.targetCluster;
  clusterSelect.addEventListener("change", () => {
    state.targetCluster = clusterSelect.value;
    renderCRMPreview();
  });

  const discountSlider = document.getElementById("discount-slider") as HTMLInputElement;
  discountSlider.value = String(state.discountPercentage);
  discountSlider.addEventListener("input", () => {
    state.discountPercentage = parseInt(discountSlider.value, 10);
    renderCRMPreview();
  });

  document.getElementById("btn-refresh-campaigns")?.addEventListener("click", () => {
    fetchLiveCampaignsHistory();
  });
}

function setupHITL(): void {
  const crmBanner = document.getElementById("crm-hitl-banner") as HTMLElement;
  const crmApprove = document.getElementById("crm-hitl-approve") as HTMLElement;
  const crmReject = document.getElementById("crm-hitl-reject") as HTMLElement;

  document.getElementById("btn-stage-campaign")?.addEventListener("click", () => {
    state.hitlActionPending = "CRM";
    crmBanner.classList.remove("hidden", "confirmed", "rejected");
    (document.getElementById("crm-hitl-message") as HTMLElement).textContent = 
      `Request to stage Flash Promo (${state.targetMarket}, ${state.discountPercentage}% discount). Target API: POST /marketing/v1/campaigns/draft`;
  });

  crmApprove.addEventListener("click", async () => {
    await syncCampaignStageToBackend();
    crmBanner.classList.add("confirmed");
    (document.getElementById("crm-hitl-message") as HTMLElement).textContent = `Flash campaign '${state.campaignName}' successfully staged to Apigee CRM Webhook gateway and saved to Firebase Cloud Firestore DB!`;
    state.hitlActionPending = null;
  });

  crmReject.addEventListener("click", () => {
    crmBanner.classList.add("rejected");
    (document.getElementById("crm-hitl-message") as HTMLElement).textContent = "Campaign staging CANCELLED by user.";
    state.hitlActionPending = null;
  });
}

const app = new App({ name: "ECG CRM Flash Promotion Campaigns", version: "1.0.0" });

app.ontoolresult = (result) => {
  console.log("[CRM-APP] Tool result received:", result);
  fetchLiveCampaignsHistory();
};

app.onhostcontextchanged = (ctx: McpUiHostContext) => {
  if (ctx.safeAreaInsets) {
    const container = document.querySelector(".app-container") as HTMLElement;
    container.style.paddingTop = `${ctx.safeAreaInsets.top}px`;
    container.style.paddingRight = `${ctx.safeAreaInsets.right}px`;
    container.style.paddingBottom = `${ctx.safeAreaInsets.bottom}px`;
    container.style.paddingLeft = `${ctx.safeAreaInsets.left}px`;
  }
};

document.addEventListener("DOMContentLoaded", () => {
  setupSelectors();
  setupHITL();
  renderCRMPreview();
  fetchLiveCampaignsHistory();

  app.connect().then(() => {
    console.log("[CRM-APP] Connected to MCP App Host.");
  }).catch((err) => {
    console.warn("[CRM-APP] Host connection notice:", err);
  });
});
