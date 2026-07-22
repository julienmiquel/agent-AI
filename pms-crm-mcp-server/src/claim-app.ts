import { App, type McpUiHostContext } from "@modelcontextprotocol/ext-apps";
import { z } from "zod";
import { getApiBaseUrl, shouldPerformDirectHttpFetch } from "./config.js";
import "./global.css";
import "./mcp-app.css";

let stateTickets: any[] = [
  {
    ticket_id: "TCK-801",
    customer_name: "Jean Dupont",
    campsite_id: "LA_SIRENE_06",
    unit_id: "MH-108",
    category: "MAINTENANCE",
    priority: "HIGH",
    description: "Water heater failure in mobil-home MH-108. Requires urgent technician intervention.",
    status: "OPEN",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    ticket_id: "TCK-802",
    customer_name: "Sophie Martin",
    campsite_id: "HIPOCAMP_07",
    unit_id: "HIP-202",
    category: "CLEANLINESS",
    priority: "MEDIUM",
    description: "Additional towels and bed sheets requested upon arrival.",
    status: "IN_PROGRESS",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

function renderTicketsFromData(tickets: any[]): void {
  const container = document.getElementById("support-tickets-list");
  if (!container) return;

  const filterSelect = document.getElementById("filter-ticket-status") as HTMLSelectElement | null;
  const statusFilter = filterSelect ? filterSelect.value : "ALL";

  let filtered = tickets;
  if (statusFilter && statusFilter !== "ALL") {
    filtered = tickets.filter((t: any) => t.status === statusFilter);
  }

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

  if (!filtered.length) {
    container.innerHTML = `<div style="color: var(--text-secondary); font-size: 13px; font-style: italic;">No claim tickets found for status '${statusFilter}'. Submit a new ticket on the left.</div>`;
    return;
  }

  container.innerHTML = filtered.map((t: any) => {
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

  container.querySelectorAll<HTMLSelectElement>(".ticket-status-select").forEach((sel) => {
    sel.addEventListener("change", async () => {
      const tid = sel.dataset.ticketId!;
      const st = sel.value;
      await updateTicketStatusInBackend(tid, st);
    });
  });
}

async function fetchLiveTickets(): Promise<void> {
  const filterSelect = document.getElementById("filter-ticket-status") as HTMLSelectElement | null;
  const statusFilter = filterSelect ? filterSelect.value : "ALL";

  if (shouldPerformDirectHttpFetch()) {
    try {
      const res = await fetch(`${getApiBaseUrl()}/api/support-tickets?status=${encodeURIComponent(statusFilter)}`);
      if (res.ok) {
        const data = await res.json();
        if (data.tickets) {
          stateTickets = data.tickets;
        }
      }
    } catch (err) {
      console.log("[CLAIM-APP] Direct fetch notice:", err);
    }
  }

  renderTicketsFromData(stateTickets);
}

async function updateTicketStatusInBackend(ticketId: string, newStatus: string): Promise<void> {
  const match = stateTickets.find((t) => t.ticket_id === ticketId);
  if (match) {
    match.status = newStatus;
    match.updated_at = new Date().toISOString();
    renderTicketsFromData(stateTickets);
  }

  if (shouldPerformDirectHttpFetch()) {
    try {
      await fetch(`${getApiBaseUrl()}/api/support-tickets/update-status`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticketId, newStatus }),
      });
    } catch (err) {
      console.log("[CLAIM-APP] Post update notice:", err);
    }
  }
}

async function createSupportTicketFromForm(): Promise<void> {
  const customerName = (document.getElementById("ticket-customer-name") as HTMLInputElement).value || "Anonymous Guest";
  const campsiteId = (document.getElementById("ticket-campsite-select") as HTMLSelectElement).value || "LA_SIRENE_06";
  const unitId = (document.getElementById("ticket-unit-id") as HTMLInputElement).value || "MH-108";
  const category = (document.getElementById("ticket-category") as HTMLSelectElement).value || "MAINTENANCE";
  const priority = (document.getElementById("ticket-priority") as HTMLSelectElement).value || "HIGH";
  const description = (document.getElementById("ticket-description") as HTMLTextAreaElement).value || "Claim issue details.";

  const newTicket = {
    ticket_id: `TCK-${Math.floor(100 + Math.random() * 900)}`,
    customer_name: customerName,
    campsite_id: campsiteId,
    unit_id: unitId,
    category,
    priority,
    description,
    status: "OPEN",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  stateTickets.unshift(newTicket);
  renderTicketsFromData(stateTickets);

  if (shouldPerformDirectHttpFetch()) {
    try {
      await fetch(`${getApiBaseUrl()}/api/support-tickets`, {
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
    } catch (err) {
      console.log("[CLAIM-APP] Post ticket create notice:", err);
    }
  }
}

function setupSelectors(): void {
  document.getElementById("btn-create-ticket")?.addEventListener("click", async () => {
    await createSupportTicketFromForm();
  });

  document.getElementById("filter-ticket-status")?.addEventListener("change", () => {
    renderTicketsFromData(stateTickets);
  });

  document.getElementById("btn-refresh-tickets")?.addEventListener("click", () => {
    fetchLiveTickets();
  });
}

const app = new App({ name: "ECG Customer Maintenance & Claim Tickets", version: "1.0.0" });

app.ontoolresult = (result) => {
  console.log("[CLAIM-APP] Tool result received via postMessage:", result);
  const data = result.structuredContent as any;
  if (data?.tickets && Array.isArray(data.tickets)) {
    stateTickets = data.tickets;
    renderTicketsFromData(stateTickets);
  } else if (data?.ticket) {
    stateTickets.unshift(data.ticket);
    renderTicketsFromData(stateTickets);
  } else {
    renderTicketsFromData(stateTickets);
  }
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
    const newTicket = {
      ticket_id: `TCK-${Math.floor(100 + Math.random() * 900)}`,
      customer_name: args.customerName,
      campsite_id: args.campsiteId,
      unit_id: args.unitId,
      category: args.category,
      priority: args.priority,
      description: args.description,
      status: "OPEN",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    stateTickets.unshift(newTicket);
    renderTicketsFromData(stateTickets);

    if (shouldPerformDirectHttpFetch()) {
      try {
        const res = await fetch(`${getApiBaseUrl()}/api/support-tickets`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(args),
        });
        const data = await res.json();
        if (data?.tickets) stateTickets = data.tickets;
      } catch (e) {
        console.log("[CLAIM-APP] Post ticket tool notice:", e);
      }
    }

    return {
      content: [{ type: "text" as const, text: `Created support ticket for customer ${args.customerName}` }],
      structuredContent: { tickets: stateTickets },
    };
  }
);

document.addEventListener("DOMContentLoaded", () => {
  setupSelectors();
  renderTicketsFromData(stateTickets);
  fetchLiveTickets();

  app.connect().then(() => {
    console.log("[CLAIM-APP] Connected to MCP App Host.");
  }).catch((err) => {
    console.warn("[CLAIM-APP] Host connection notice:", err);
  });
});
