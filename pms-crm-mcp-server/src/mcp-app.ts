import { App, type McpUiHostContext } from "@modelcontextprotocol/ext-apps";
import { Chart, registerables } from "chart.js";
import { z } from "zod";
import { getApiBaseUrl, shouldPerformDirectHttpFetch } from "./config.js";
import "./global.css";
import "./mcp-app.css";

Chart.register(...registerables);

// ---------------------------------------------------------------------------
// Types & Data Structures
// ---------------------------------------------------------------------------

export type UnitStatus = "AVAILABLE_FOR_SALE" | "HELD_BACK" | "MAINTENANCE" | "BOOKED";

export interface MobilHomeUnit {
  unitId: string;
  unitType: string;
  status: UnitStatus;
  nightlyRate: number;
}

export interface CampsiteInfo {
  campsiteId: string;
  name: string;
  cluster: string;
  units: MobilHomeUnit[];
}

export interface PendingPmsAction {
  campsiteId: string;
  unitIds: string[];
  newStatus: UnitStatus;
  description: string;
}

interface AppState {
  campsites: CampsiteInfo[];
  selectedCampsiteId: string;
  targetMarket: string;
  targetCluster: string;
  discountPercentage: number;
  campaignName: string;
  customCopywriting: string | null;
  hitlActionPending: "PMS" | "CRM" | null;
  pendingPmsAction: PendingPmsAction | null;
  pmsChart: Chart<"doughnut"> | null;
}

// Initial Fallback Data
const INITIAL_CAMPSITES: CampsiteInfo[] = [
  {
    campsiteId: "LA_SIRENE_06",
    name: "La Sirène (French Riviera)",
    cluster: "MEDITERRANEAN_SOUTH",
    units: [
      { unitId: "MH-102", unitType: "Premium 3BR", status: "HELD_BACK", nightlyRate: 145 },
      { unitId: "MH-103", unitType: "Premium 3BR", status: "HELD_BACK", nightlyRate: 145 },
      { unitId: "MH-104", unitType: "Comfort 2BR", status: "HELD_BACK", nightlyRate: 110 },
      { unitId: "MH-105", unitType: "Comfort 2BR", status: "HELD_BACK", nightlyRate: 110 },
      { unitId: "MH-106", unitType: "Luxury Villa", status: "AVAILABLE_FOR_SALE", nightlyRate: 220 },
      { unitId: "MH-107", unitType: "Luxury Villa", status: "BOOKED", nightlyRate: 220 },
      { unitId: "MH-108", unitType: "Comfort 2BR", status: "MAINTENANCE", nightlyRate: 110 },
      { unitId: "MH-109", unitType: "Premium 3BR", status: "AVAILABLE_FOR_SALE", nightlyRate: 145 },
    ],
  },
  {
    campsiteId: "HIPOCAMP_07",
    name: "L'Hippocampe (Roussillon)",
    cluster: "MEDITERRANEAN_SOUTH",
    units: [
      { unitId: "HIP-201", unitType: "Cosy 2BR", status: "AVAILABLE_FOR_SALE", nightlyRate: 95 },
      { unitId: "HIP-202", unitType: "Cosy 2BR", status: "HELD_BACK", nightlyRate: 95 },
    ],
  },
];

const state: AppState = {
  campsites: INITIAL_CAMPSITES,
  selectedCampsiteId: "LA_SIRENE_06",
  targetMarket: "NL",
  targetCluster: "MEDITERRANEAN_SOUTH",
  discountPercentage: 15,
  campaignName: "Flash_Promo_NL_MEDITERRANEAN_SOUTH_July",
  customCopywriting: null,
  hitlActionPending: null,
  pendingPmsAction: null,
  pmsChart: null,
};

// ---------------------------------------------------------------------------
// Backend API Sync
// ---------------------------------------------------------------------------

async function fetchLiveInventory(): Promise<void> {
  if (shouldPerformDirectHttpFetch()) {
    try {
      const res = await fetch(`${getApiBaseUrl()}/api/pms-inventory`);
      if (res.ok) {
        const data = await res.json();
        if (data.campsites && data.campsites.length) {
          state.campsites = data.campsites;
        }
      }
    } catch (err) {
      console.log("[MCP-APP] Direct fetch notice:", err);
    }
  }
  updateUI();
}

async function syncInventoryUpdateToBackend(campsiteId: string, unitIds: string[], newStatus: string): Promise<void> {
  if (shouldPerformDirectHttpFetch()) {
    try {
      const res = await fetch(`${getApiBaseUrl()}/api/resalys-update-inventory`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ campsiteId, unitIds, newStatus }),
      });
      if (res.ok) {
        const data = await res.json();
        if (data.campsites && data.campsites.length) {
          state.campsites = data.campsites;
        }
      }
    } catch (err) {
      console.log("[MCP-APP] Post update notice:", err);
    }
  }
  updateUI();
}

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
      console.log("[MCP-APP] Direct stage notice:", err);
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
      console.log("[MCP-APP] Direct fetch notice:", err);
    }
  }
}

// ---------------------------------------------------------------------------
// Support Claims Tickets Sync
// ---------------------------------------------------------------------------

async function fetchLiveTickets(): Promise<void> {
  const container = document.getElementById("support-tickets-list");
  if (!container) return;

  const filterSelect = document.getElementById("filter-ticket-status") as HTMLSelectElement | null;
  const statusFilter = filterSelect ? filterSelect.value : "ALL";

  if (shouldPerformDirectHttpFetch()) {
    try {
      const res = await fetch(`${getApiBaseUrl()}/api/support-tickets?status=${encodeURIComponent(statusFilter)}`);
      if (res.ok) {
        const data = await res.json();
        const tickets = data.tickets || [];

        // Update metrics
        let openCount = 0, urgentCount = 0, inProgressCount = 0, resolvedCount = 0;
        tickets.forEach((t: any) => {
          if (t.status === "OPEN") openCount++;
          if (t.priority === "URGENT" || t.priority === "HIGH") urgentCount++;
          if (t.status === "IN_PROGRESS") inProgressCount++;
          if (t.status === "RESOLVED" || t.status === "CLOSED") resolvedCount++;
        });

        (document.getElementById("ticket-metric-open") as HTMLElement).textContent = String(openCount);
        (document.getElementById("ticket-metric-urgent") as HTMLElement).textContent = String(urgentCount);
        (document.getElementById("ticket-metric-progress") as HTMLElement).textContent = String(inProgressCount);
        (document.getElementById("ticket-metric-resolved") as HTMLElement).textContent = String(resolvedCount);

        if (!tickets.length) {
          container.innerHTML = `<div style="color: var(--text-secondary); font-size: 13px; font-style: italic;">No claim tickets found for status '${statusFilter}'. Submit a new ticket on the left.</div>`;
          return;
        }

        container.innerHTML = tickets.map((t: any) => {
          const priorityColor = t.priority === "URGENT" ? "#ef4444" : t.priority === "HIGH" ? "#f59e0b" : t.priority === "MEDIUM" ? "#3b82f6" : "#10b981";
          const categoryIcon = t.category === "MAINTENANCE" ? "🔧" : t.category === "CLEANLINESS" ? "🧹" : t.category === "NOISE" ? "🔊" : t.category === "BILLING" ? "💳" : t.category === "EQUIPMENT" ? "🛋️" : "❓";

          return `
            <div class="ticket-item" style="background: var(--bg-primary); border: 1px solid var(--border-color); border-radius: 8px; padding: 12px; display: flex; flex-direction: column; gap: 8px;">
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 8px;">
                  <span style="font-weight: 800; font-size: 14px; color: #60a5fa;">${t.ticket_id}</span>
                  <span style="font-weight: 700; font-size: 13px; color: var(--text-primary);">${t.customer_name}</span>
                </div>
                <select class="ticket-status-select" data-ticket-id="${t.ticket_id}" style="font-size: 11px; padding: 2px 6px; border-radius: 4px; background: var(--bg-surface); color: var(--text-primary); border: 1px solid var(--border-color);">
                  <option value="OPEN" ${t.status === "OPEN" ? "selected" : ""}>OPEN</option>
                  <option value="IN_PROGRESS" ${t.status === "IN_PROGRESS" ? "selected" : ""}>IN PROGRESS</option>
                  <option value="RESOLVED" ${t.status === "RESOLVED" ? "selected" : ""}>RESOLVED</option>
                  <option value="CLOSED" ${t.status === "CLOSED" ? "selected" : ""}>CLOSED</option>
                </select>
              </div>
              <div style="display: flex; gap: 8px; font-size: 11px; align-items: center; flex-wrap: wrap;">
                <span style="background: rgba(255,255,255,0.08); color: var(--text-primary); padding: 2px 6px; border-radius: 4px; font-weight: 600;">${categoryIcon} ${t.category}</span>
                <span style="background: rgba(255,255,255,0.08); color: var(--text-secondary); padding: 2px 6px; border-radius: 4px;">${t.campsite_id} / ${t.unit_id}</span>
                <span style="color: ${priorityColor}; font-weight: 700;">● ${t.priority}</span>
                <span style="color: var(--text-secondary); font-size: 10px; margin-left: auto;">${new Date(t.updated_at || Date.now()).toLocaleTimeString()}</span>
              </div>
              <div style="font-size: 12px; color: var(--text-primary); background: var(--bg-surface); padding: 8px; border-radius: 4px;">
                ${t.description}
              </div>
            </div>
          `;
        }).join("");

        // Bind status select listeners
        container.querySelectorAll<HTMLSelectElement>(".ticket-status-select").forEach((sel) => {
          sel.addEventListener("change", async () => {
            const tid = sel.dataset.ticketId!;
            const st = sel.value;
            await updateTicketStatusInBackend(tid, st);
          });
        });
      }
    } catch (err) {
      console.log("[MCP-APP] Direct fetch notice:", err);
    }
  }
}

async function updateTicketStatusInBackend(ticketId: string, newStatus: string): Promise<void> {
  if (shouldPerformDirectHttpFetch()) {
    try {
      await fetch(`${getApiBaseUrl()}/api/support-tickets/update-status`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticketId, newStatus }),
      });
      await fetchLiveTickets();
    } catch (err) {
      console.log("[MCP-APP] Direct update notice:", err);
    }
  }
}

async function createSupportTicketFromForm(): Promise<void> {
  const customerName = (document.getElementById("ticket-customer-name") as HTMLInputElement).value || "Anonymous Guest";
  const campsiteId = (document.getElementById("ticket-campsite-select") as HTMLSelectElement).value || "LA_SIRENE_06";
  const unitId = (document.getElementById("ticket-unit-id") as HTMLInputElement).value || "MH-102";
  const category = (document.getElementById("ticket-category") as HTMLSelectElement).value || "MAINTENANCE";
  const priority = (document.getElementById("ticket-priority") as HTMLSelectElement).value || "HIGH";
  const description = (document.getElementById("ticket-description") as HTMLTextAreaElement).value || "Claim issue details.";

  if (shouldPerformDirectHttpFetch()) {
    try {
      const res = await fetch(`${getApiBaseUrl()}/api/support-tickets`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          customerName,
          campsiteId,
          unitId,
          category,
          priority,
          description,
        }),
      });
      if (res.ok) {
        await fetchLiveTickets();
      }
    } catch (err) {
      console.log("[MCP-APP] Direct create ticket notice:", err);
    }
  }
}

// ---------------------------------------------------------------------------
// Copywriting & GCS URI Helpers
// ---------------------------------------------------------------------------

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

// ---------------------------------------------------------------------------
// DOM Rendering & Controls
// ---------------------------------------------------------------------------

function getActiveCampsite(): CampsiteInfo {
  return state.campsites.find((c) => c.campsiteId === state.selectedCampsiteId) || state.campsites[0];
}

function updateMetrics(): void {
  const campsite = getActiveCampsite();
  let available = 0, heldback = 0, maintenance = 0, booked = 0;

  for (const u of campsite.units) {
    if (u.status === "AVAILABLE_FOR_SALE") available++;
    else if (u.status === "HELD_BACK") heldback++;
    else if (u.status === "MAINTENANCE") maintenance++;
    else if (u.status === "BOOKED") booked++;
  }

  (document.getElementById("metric-available") as HTMLElement).textContent = String(available);
  (document.getElementById("metric-heldback") as HTMLElement).textContent = String(heldback);
  (document.getElementById("metric-maintenance") as HTMLElement).textContent = String(maintenance);
  (document.getElementById("metric-booked") as HTMLElement).textContent = String(booked);
}

function stagePmsAction(campsiteId: string, unitIds: string[], newStatus: UnitStatus, description: string): void {
  state.pendingPmsAction = { campsiteId, unitIds, newStatus, description };
  state.hitlActionPending = "PMS";
  const pmsBanner = document.getElementById("pms-hitl-banner") as HTMLElement;
  pmsBanner.classList.remove("hidden", "confirmed", "rejected");
  (document.getElementById("pms-hitl-message") as HTMLElement).textContent = 
    `⚠️ Pending Approval: ${description}. Click 'Approve Action' below to execute & save to Firebase Firestore DB.`;
}

function renderUnitsGrid(): void {
  const container = document.getElementById("units-container") as HTMLElement;
  container.innerHTML = "";
  const campsite = getActiveCampsite();

  for (const unit of campsite.units) {
    const item = document.createElement("div");
    item.className = "unit-item";
    item.innerHTML = `
      <div class="unit-header">
        <span class="unit-id">${unit.unitId}</span>
        <span class="unit-status-pill status-${unit.status}">${unit.status.replace(/_/g, " ")}</span>
      </div>
      <div style="font-size: 11px; color: var(--text-secondary);">${unit.unitType} • €${unit.nightlyRate}/n</div>
      <select class="unit-select" data-unit-id="${unit.unitId}">
        <option value="AVAILABLE_FOR_SALE" ${unit.status === "AVAILABLE_FOR_SALE" ? "selected" : ""}>AVAILABLE FOR SALE</option>
        <option value="HELD_BACK" ${unit.status === "HELD_BACK" ? "selected" : ""}>HELD BACK (YIELD)</option>
        <option value="MAINTENANCE" ${unit.status === "MAINTENANCE" ? "selected" : ""}>MAINTENANCE</option>
        <option value="BOOKED" ${unit.status === "BOOKED" ? "selected" : ""}>BOOKED</option>
      </select>
    `;

    const select = item.querySelector(".unit-select") as HTMLSelectElement;
    select.addEventListener("change", () => {
      const newStatus = select.value as UnitStatus;
      select.value = unit.status;
      stagePmsAction(
        campsite.campsiteId,
        [unit.unitId],
        newStatus,
        `Change status of ${unit.unitId} from ${unit.status} to '${newStatus.replace(/_/g, " ")}'`
      );
    });

    container.appendChild(item);
  }
}

function renderPmsChart(): void {
  const canvas = document.getElementById("pms-chart") as HTMLCanvasElement;
  if (!canvas) return;

  const campsite = getActiveCampsite();
  let available = 0, heldback = 0, maintenance = 0, booked = 0;
  for (const u of campsite.units) {
    if (u.status === "AVAILABLE_FOR_SALE") available++;
    else if (u.status === "HELD_BACK") heldback++;
    else if (u.status === "MAINTENANCE") maintenance++;
    else if (u.status === "BOOKED") booked++;
  }

  if (state.pmsChart) {
    state.pmsChart.data.datasets[0].data = [available, heldback, maintenance, booked];
    state.pmsChart.update();
    return;
  }

  const ctx = canvas.getContext("2d")!;
  state.pmsChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: ["Available", "Held Back", "Maintenance", "Booked"],
      datasets: [
        {
          data: [available, heldback, maintenance, booked],
          backgroundColor: ["#10b981", "#f59e0b", "#ef4444", "#3b82f6"],
          borderWidth: 2,
          borderColor: "#1e293b",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "65%",
      plugins: {
        legend: {
          position: "bottom",
          labels: { color: "#94a3b8", font: { size: 11 } },
        },
      },
    },
  });
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

function updateUI(): void {
  updateMetrics();
  renderUnitsGrid();
  renderPmsChart();
  renderCRMPreview();
}

// ---------------------------------------------------------------------------
// Event Listeners Setup
// ---------------------------------------------------------------------------

export function switchTab(targetTab: string): void {
  const raw = (targetTab || "").toLowerCase().trim();
  let actualTab = raw;
  if (["claim", "claims", "ticket", "tickets", "maintenance", "support"].includes(raw)) {
    actualTab = "tickets";
  } else if (["crm", "campaign", "campaigns", "promo", "marketing"].includes(raw)) {
    actualTab = "crm";
  } else if (["pms", "inventory", "units", "resalys"].includes(raw)) {
    actualTab = "pms";
  }

  const tabBtns = document.querySelectorAll<HTMLButtonElement>(".tab-btn");
  const tabContents = document.querySelectorAll<HTMLElement>(".tab-content");

  tabBtns.forEach((btn) => {
    if (btn.dataset.tab === actualTab) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }
  });

  tabContents.forEach((c) => {
    if (c.id === `${actualTab}-tab`) {
      c.classList.add("active");
    } else {
      c.classList.remove("active");
    }
  });

  if (actualTab === "tickets") {
    fetchLiveTickets();
  } else if (actualTab === "crm") {
    fetchLiveCampaignsHistory();
  }
}

function checkTabFromUrl(): void {
  const urlParams = new URLSearchParams(window.location.search);
  const tabParam = urlParams.get("tab") || window.location.hash.replace("#", "");
  if (tabParam) {
    switchTab(tabParam);
  }
}

function setupTabs(): void {
  const tabBtns = document.querySelectorAll<HTMLButtonElement>(".tab-btn");

  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const target = btn.dataset.tab;
      if (target) {
        switchTab(target);
      }
    });
  });
}

function setupSelectors(): void {
  const campsiteSelect = document.getElementById("campsite-selector") as HTMLSelectElement;
  campsiteSelect.innerHTML = "";
  for (const c of state.campsites) {
    const opt = document.createElement("option");
    opt.value = c.campsiteId;
    opt.textContent = c.name;
    opt.selected = c.campsiteId === state.selectedCampsiteId;
    campsiteSelect.appendChild(opt);
  }

  campsiteSelect.addEventListener("change", () => {
    state.selectedCampsiteId = campsiteSelect.value;
    updateUI();
  });

  const marketSelect = document.getElementById("target-market") as HTMLSelectElement;
  marketSelect.value = state.targetMarket;
  marketSelect.addEventListener("change", () => {
    state.targetMarket = marketSelect.value;
    updateUI();
  });

  const clusterSelect = document.getElementById("target-cluster") as HTMLSelectElement;
  clusterSelect.value = state.targetCluster;
  clusterSelect.addEventListener("change", () => {
    state.targetCluster = clusterSelect.value;
    updateUI();
  });

  const discountSlider = document.getElementById("discount-slider") as HTMLInputElement;
  discountSlider.value = String(state.discountPercentage);
  discountSlider.addEventListener("input", () => {
    state.discountPercentage = parseInt(discountSlider.value, 10);
    updateUI();
  });

  document.getElementById("btn-refresh-campaigns")?.addEventListener("click", () => {
    fetchLiveCampaignsHistory();
  });

  document.getElementById("btn-create-ticket")?.addEventListener("click", async () => {
    await createSupportTicketFromForm();
  });

  document.getElementById("filter-ticket-status")?.addEventListener("change", () => {
    fetchLiveTickets();
  });

  document.getElementById("btn-refresh-tickets")?.addEventListener("click", () => {
    fetchLiveTickets();
  });
}

function setupHITL(): void {
  const pmsBanner = document.getElementById("pms-hitl-banner") as HTMLElement;
  const pmsApprove = document.getElementById("pms-hitl-approve") as HTMLElement;
  const pmsReject = document.getElementById("pms-hitl-reject") as HTMLElement;

  document.getElementById("btn-holdback-units")?.addEventListener("click", () => {
    const campsite = getActiveCampsite();
    const unitsToHold = ["MH-102", "MH-103", "MH-104", "MH-105"];
    stagePmsAction(
      campsite.campsiteId,
      unitsToHold,
      "HELD_BACK",
      `Hold back 4 units (MH-102..MH-105) at ${campsite.campsiteId} for Yield Management`
    );
  });

  document.getElementById("btn-release-heldback")?.addEventListener("click", () => {
    const campsite = getActiveCampsite();
    const heldBackUnits = campsite.units.filter((u) => u.status === "HELD_BACK");
    const unitsToUpdate = heldBackUnits.length 
      ? heldBackUnits.map((u) => u.unitId)
      : ["MH-102", "MH-103", "MH-104", "MH-105"];

    stagePmsAction(
      campsite.campsiteId,
      unitsToUpdate,
      "AVAILABLE_FOR_SALE",
      `Release ${unitsToUpdate.length} held-back unit(s) (${unitsToUpdate.join(", ")}) at ${campsite.campsiteId} to AVAILABLE_FOR_SALE`
    );
  });

  pmsApprove.addEventListener("click", async () => {
    if (!state.pendingPmsAction) {
      const campsite = getActiveCampsite();
      state.pendingPmsAction = {
        campsiteId: campsite.campsiteId,
        unitIds: ["MH-102", "MH-103", "MH-104", "MH-105"],
        newStatus: "AVAILABLE_FOR_SALE",
        description: "Release held-back units",
      };
    }

    const pending = state.pendingPmsAction;
    const campsite = state.campsites.find((c) => c.campsiteId === pending.campsiteId) || getActiveCampsite();

    for (const u of campsite.units) {
      if (pending.unitIds.includes(u.unitId)) {
        u.status = pending.newStatus;
      }
    }

    await syncInventoryUpdateToBackend(pending.campsiteId, pending.unitIds, pending.newStatus);

    pmsBanner.classList.add("confirmed");
    (document.getElementById("pms-hitl-message") as HTMLElement).textContent = 
      `✅ Action CONFIRMED & executed via Resalys PMS REST API! Updated ${pending.unitIds.length} unit(s) (${pending.unitIds.join(", ")}) to '${pending.newStatus}' in Firebase Cloud Firestore DB.`;
    
    state.pendingPmsAction = null;
    updateUI();
  });

  pmsReject.addEventListener("click", () => {
    pmsBanner.classList.add("rejected");
    (document.getElementById("pms-hitl-message") as HTMLElement).textContent = "❌ Action REJECTED by user. Zero backend side-effects.";
    state.pendingPmsAction = null;
    fetchLiveInventory();
  });

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

// ---------------------------------------------------------------------------
// MCP App SDK Connection & Client Tools
// ---------------------------------------------------------------------------

const app = new App({ name: "ECG PMS & CRM Control Center", version: "1.0.0" });

app.ontoolresult = (result) => {
  console.log("[MCP-APP] Tool result received:", result);
  const data = result.structuredContent as any;
  if (data?.campsites && data.campsites.length) {
    state.campsites = data.campsites;
  }

  const toolName = (result.toolInfo?.tool?.name || "").toLowerCase();
  if (
    toolName.includes("ticket") ||
    toolName.includes("support") ||
    toolName.includes("claim") ||
    data?.tickets ||
    data?.ticket ||
    data?.tab === "tickets" ||
    data?.widget_type === "SUPPORT_TICKETS"
  ) {
    switchTab("tickets");
  } else if (toolName.includes("crm") || toolName.includes("campaign") || data?.campaignName || data?.tab === "crm" || data?.widget_type === "MARKETING_CAMPAIGN_DRAFT") {
    switchTab("crm");
  } else if (toolName.includes("pms") || toolName.includes("inventory") || data?.tab === "pms") {
    switchTab("pms");
  }

  updateUI();
  fetchLiveTickets();
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

// Register Client Tools
app.registerTool(
  "get-pms-crm-state",
  {
    title: "Get PMS & CRM State",
    description: "Returns current state of PMS unit inventory, campsite selection, CRM campaign draft, and support claim tickets.",
  },
  async () => {
    const campsite = getActiveCampsite();
    const data = {
      campsiteId: campsite.campsiteId,
      campsiteName: campsite.name,
      units: campsite.units,
      crmConfig: {
        targetMarket: state.targetMarket,
        targetCluster: state.targetCluster,
        discountPercentage: state.discountPercentage,
        copywritingText: generateCopywriting(state.targetMarket, state.targetCluster, state.discountPercentage),
        imageAssetGcsUri: resolveImagenUri(state.targetMarket, state.targetCluster),
      },
    };

    return {
      content: [{ type: "text" as const, text: JSON.stringify(data, null, 2) }],
      structuredContent: data,
    };
  }
);

app.registerTool(
  "update-pms-unit-status",
  {
    title: "Update PMS Unit Inventory Status",
    description: "Update status of specific mobil-home units in selected campsite",
    inputSchema: z.object({
      unitIds: z.array(z.string()).describe("List of unit IDs to update (e.g. ['MH-102', 'MH-103'])"),
      newStatus: z.enum(["AVAILABLE_FOR_SALE", "HELD_BACK", "MAINTENANCE", "BOOKED"]).describe("New inventory status"),
    }),
  },
  async ({ unitIds, newStatus }) => {
    const campsite = getActiveCampsite();
    let updatedCount = 0;

    for (const u of campsite.units) {
      if (unitIds.includes(u.unitId)) {
        u.status = newStatus as UnitStatus;
        updatedCount++;
      }
    }

    await syncInventoryUpdateToBackend(campsite.campsiteId, unitIds, newStatus);
    updateUI();

    return {
      content: [{ type: "text" as const, text: `Successfully updated ${updatedCount} unit(s) to status '${newStatus}' at ${campsite.campsiteId}` }],
    };
  }
);

app.registerTool(
  "create-support-ticket",
  {
    title: "Create Customer Claim Support Ticket",
    description: "Registers customer claim ticket in Firebase Cloud Firestore",
    inputSchema: z.object({
      customerName: z.string().describe("Customer Full Name"),
      campsiteId: z.string().describe("Campsite ID"),
      unitId: z.string().describe("Unit ID"),
      category: z.string().describe("Category"),
      priority: z.string().describe("Priority"),
      description: z.string().describe("Claim Details"),
    }),
  },
  async (args) => {
    const res = await fetch(`${getApiBaseUrl()}/api/support-tickets`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(args),
    });
    const data = await res.json();
    await fetchLiveTickets();
    switchTab("tickets");
    return {
      content: [{ type: "text" as const, text: `Created support ticket '${data.ticket?.ticket_id}' for customer ${args.customerName}` }],
      structuredContent: data,
    };
  }
);

// App Init
document.addEventListener("DOMContentLoaded", () => {
  setupTabs();
  setupSelectors();
  setupHITL();
  fetchLiveInventory();
  fetchLiveCampaignsHistory();
  fetchLiveTickets();
  updateUI();
  checkTabFromUrl();

  app.connect().then(() => {
    console.log("[MCP-APP] Connected to MCP App Host.");
  }).catch((err) => {
    console.warn("[MCP-APP] Host connection notice:", err);
  });
});
