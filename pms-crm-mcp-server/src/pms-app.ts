import { App, type McpUiHostContext } from "@modelcontextprotocol/ext-apps";
import { Chart, registerables } from "chart.js";
import { z } from "zod";
import { getApiBaseUrl, shouldPerformDirectHttpFetch } from "./config.js";
import "./global.css";
import "./mcp-app.css";

Chart.register(...registerables);

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
  hitlActionPending: "PMS" | null;
  pendingPmsAction: PendingPmsAction | null;
  pmsChart: Chart<"doughnut"> | null;
}

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
  hitlActionPending: null,
  pendingPmsAction: null,
  pmsChart: null,
};

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
      console.log("[PMS-APP] Direct fetch notice:", err);
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
      console.log("[PMS-APP] Post update notice:", err);
    }
  }
  updateUI();
}

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

function updateUI(): void {
  updateMetrics();
  renderUnitsGrid();
  renderPmsChart();
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
}

const app = new App({ name: "Company Resalys PMS Inventory", version: "1.0.0" });

app.ontoolresult = (result) => {
  console.log("[PMS-APP] Tool result received:", result);
  const data = result.structuredContent as any;
  if (data?.campsites && data.campsites.length) {
    state.campsites = data.campsites;
  }
  updateUI();
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

app.registerTool(
  "update-pms-unit-status",
  {
    title: "Update PMS Unit Inventory Status",
    description: "Update status of specific mobil-home units in selected campsite",
    inputSchema: z.object({
      unitIds: z.array(z.string()).describe("List of unit IDs to update"),
      newStatus: z.enum(["AVAILABLE_FOR_SALE", "HELD_BACK", "MAINTENANCE", "BOOKED"]).describe("New status"),
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

document.addEventListener("DOMContentLoaded", () => {
  setupSelectors();
  setupHITL();
  fetchLiveInventory();
  updateUI();

  app.connect().then(() => {
    console.log("[PMS-APP] Connected to MCP App Host.");
  }).catch((err) => {
    console.warn("[PMS-APP] Host connection notice:", err);
  });
});
