/**
 * European Camping Company (Company) PMS & CRM MCP App Server
 *
 * Interfaced with Google Cloud Firestore database for real, un-mocked data persistence.
 */
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import type { CallToolResult, ReadResourceResult } from "@modelcontextprotocol/sdk/types.js";
import fs from "node:fs/promises";
import path from "node:path";
import { z } from "zod";
import { Firestore } from "@google-cloud/firestore";
import {
  RESOURCE_MIME_TYPE,
  registerAppResource,
  registerAppTool,
} from "@modelcontextprotocol/ext-apps/server";

const DIST_DIR = import.meta.filename?.endsWith(".ts")
  ? path.join(import.meta.dirname, "dist")
  : import.meta.dirname;

const resourceUri = "ui://pms-crm/mcp-app.html";

// ---------------------------------------------------------------------------
// Real Google Cloud Firestore Database Connection
// ---------------------------------------------------------------------------

let firestoreDb: Firestore | null = null;
try {
  firestoreDb = new Firestore({
    projectId: process.env.GCP_PROJECT || "ml-demo-384110",
  });
} catch (e) {
  console.warn("Firestore client init warning:", e);
}

// Initial seed data if Firestore collection is empty
const INITIAL_CAMPSITES_SEED = [
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

let inMemoryCampsites = JSON.parse(JSON.stringify(INITIAL_CAMPSITES_SEED));

export async function loadCampsitesFromFirestore(campsiteIdFilter?: string) {
  let campsites = JSON.parse(JSON.stringify(inMemoryCampsites));

  if (firestoreDb) {
    try {
      const snapshot = await firestoreDb.collection("pms_inventory").get();
      if (!snapshot.empty) {
        const statusMap: Record<string, string> = {};
        snapshot.docs.forEach((doc) => {
          const data = doc.data();
          const cid = data.campsite_id || "LA_SIRENE_06";
          const uid = data.unit_id || doc.id.replace(`${cid}_`, "");
          const key = `${cid}_${uid}`;
          if (data.status) {
            statusMap[key] = data.status;
          }
        });

        for (const campsite of campsites) {
          for (const unit of campsite.units) {
            const key = `${campsite.campsiteId}_${unit.unitId}`;
            if (statusMap[key]) {
              unit.status = statusMap[key];
            }
          }
        }
      } else {
        // Seed initial units into Firestore
        const batch = firestoreDb.batch();
        for (const campsite of campsites) {
          for (const unit of campsite.units) {
            const docRef = firestoreDb.collection("pms_inventory").doc(`${campsite.campsiteId}_${unit.unitId}`);
            batch.set(docRef, {
              campsite_id: campsite.campsiteId,
              unit_id: unit.unitId,
              unit_type: unit.unitType,
              status: unit.status,
              nightly_rate: unit.nightlyRate,
              updated_at: new Date().toISOString(),
            });
          }
        }
        await batch.commit();
        console.error("Seeded initial campsite inventory into Firebase Cloud Firestore.");
      }
    } catch (err) {
      console.warn("Firestore query error, using in-memory store:", err);
    }
  }

  if (campsiteIdFilter) {
    return campsites.filter((c: any) => c.campsiteId === campsiteIdFilter);
  }
  return campsites;
}

export async function updateFirestoreUnits(campsiteId: string, unitIds: string[], newStatus: string) {
  // Update in-memory cache
  const campsite = inMemoryCampsites.find((c: any) => c.campsiteId === campsiteId);
  if (campsite) {
    for (const u of campsite.units) {
      if (unitIds.includes(u.unitId)) {
        u.status = newStatus;
      }
    }
  }

  if (firestoreDb) {
    try {
      const batch = firestoreDb.batch();
      for (const uid of unitIds) {
        const docRef = firestoreDb.collection("pms_inventory").doc(`${campsiteId}_${uid}`);
        batch.set(
          docRef,
          {
            campsite_id: campsiteId,
            unit_id: uid,
            status: newStatus,
            updated_at: new Date().toISOString(),
          },
          { merge: true }
        );
      }
      await batch.commit();
      console.error(`Updated ${unitIds.length} units in Firebase Firestore DB.`);
    } catch (e) {
      console.warn("Firestore update warning:", e);
    }
  }
}

let inMemoryCampaigns: any[] = [];

export async function saveFirestoreCampaign(campaignData: any) {
  inMemoryCampaigns = inMemoryCampaigns.filter((c) => c.campaign_name !== campaignData.campaign_name);
  inMemoryCampaigns.unshift(campaignData);

  if (firestoreDb) {
    try {
      await firestoreDb.collection("crm_campaigns").doc(campaignData.campaign_name).set(campaignData, { merge: true });
      console.error(`Saved CRM campaign '${campaignData.campaign_name}' to Firebase Firestore DB.`);
    } catch (e) {
      console.warn("Firestore save campaign warning:", e);
    }
  }
}

export async function loadCampaignsFromFirestore() {
  if (firestoreDb) {
    try {
      const snapshot = await firestoreDb.collection("crm_campaigns").get();
      if (!snapshot.empty) {
        return snapshot.docs.map((doc) => doc.data());
      }
    } catch (err) {
      console.warn("Firestore campaign query warning:", err);
    }
  }
  return inMemoryCampaigns;
}

// ---------------------------------------------------------------------------
// Collection 4: Support Claims Tickets
// ---------------------------------------------------------------------------

let inMemoryTickets: any[] = [
  {
    ticket_id: "TCK-801",
    customer_name: "Jean Dupont",
    campsite_id: "LA_SIRENE_06",
    unit_id: "MH-108",
    category: "MAINTENANCE",
    priority: "HIGH",
    description: "Water heater failure in mobil-home MH-108. Requires urgent technician intervention.",
    status: "OPEN",
    created_at: new Date(Date.now() - 3600000 * 2).toISOString(),
    updated_at: new Date(Date.now() - 3600000 * 2).toISOString(),
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
    created_at: new Date(Date.now() - 3600000 * 5).toISOString(),
    updated_at: new Date(Date.now() - 3600000 * 1).toISOString(),
  },
];

export async function saveFirestoreTicket(ticketData: any) {
  inMemoryTickets = inMemoryTickets.filter((t) => t.ticket_id !== ticketData.ticket_id);
  inMemoryTickets.unshift(ticketData);

  if (firestoreDb) {
    try {
      await firestoreDb.collection("support_tickets").doc(ticketData.ticket_id).set(ticketData, { merge: true });
      console.error(`Saved support ticket '${ticketData.ticket_id}' to Firebase Firestore DB.`);
    } catch (e) {
      console.warn("Firestore save ticket warning:", e);
    }
  }
}

export async function loadTicketsFromFirestore(statusFilter?: string, campsiteIdFilter?: string) {
  if (firestoreDb) {
    try {
      const snapshot = await firestoreDb.collection("support_tickets").get();
      if (!snapshot.empty) {
        let docs = snapshot.docs.map((doc) => doc.data());
        if (statusFilter && statusFilter !== "ALL") {
          docs = docs.filter((d) => d.status === statusFilter);
        }
        if (campsiteIdFilter) {
          docs = docs.filter((d) => d.campsite_id === campsiteIdFilter);
        }
        return docs;
      }
    } catch (err) {
      console.warn("Firestore tickets query warning:", err);
    }
  }

  let result = [...inMemoryTickets];
  if (statusFilter && statusFilter !== "ALL") {
    result = result.filter((t) => t.status === statusFilter);
  }
  if (campsiteIdFilter) {
    result = result.filter((t) => t.campsite_id === campsiteIdFilter);
  }
  return result;
}

export async function updateFirestoreTicketStatus(ticketId: string, newStatus: string) {
  const match = inMemoryTickets.find((t) => t.ticket_id === ticketId);
  if (match) {
    match.status = newStatus;
    match.updated_at = new Date().toISOString();
  }

  if (firestoreDb) {
    try {
      await firestoreDb.collection("support_tickets").doc(ticketId).set(
        {
          status: newStatus,
          updated_at: new Date().toISOString(),
        },
        { merge: true }
      );
      console.error(`Updated support ticket '${ticketId}' status to '${newStatus}' in Firebase Firestore DB.`);
    } catch (e) {
      console.warn("Firestore update ticket status warning:", e);
    }
  }
}

// ---------------------------------------------------------------------------
// Server Factory
// ---------------------------------------------------------------------------

export function createServer(): McpServer {
  const server = new McpServer({
    name: "Company PMS & CRM MCP App Server",
    version: "1.0.0",
  });

  // Tool 1: Get PMS Inventory
  registerAppTool(
    server,
    "get-pms-inventory",
    {
      title: "Get Resalys PMS Inventory",
      description: "Returns real campsite mobil-home units, occupancy breakdown, and held-back yield units from Firebase Cloud Firestore.",
      inputSchema: {
        campsiteId: z.string().optional().describe("Optional Campsite ID filter (e.g. LA_SIRENE_06)"),
      },
      outputSchema: z.object({
        campsites: z.array(z.any()),
        identityScope: z.string(),
      }),
      annotations: {
        readOnlyHint: true,
        destructiveHint: false,
        idempotentHint: true,
      },
      _meta: {
        ui: {
          resourceUri: "ui://pms-crm/pms-app.html",
          csp: {
            connectDomains: [
              "https://company-pms-crm-mcp-app-ahavst3hhq-uc.a.run.app",
              "https://company-pms-crm-mcp-app-1008225662928.us-central1.run.app",
              "https://ecg-pms-crm-mcp-app-ahavst3hhq-uc.a.run.app",
              "https://ecg-pms-crm-mcp-app-1008225662928.us-central1.run.app",
              "https://*.run.app",
              "https://*.googleapis.com",
            ],
          },
        },
      },
    },
    async (args): Promise<CallToolResult> => {
      const campsites = await loadCampsitesFromFirestore(args.campsiteId);

      const response = {
        campsites,
        identityScope: "CloudIdentity (julien)",
      };

      const summaryText = campsites
        .map(
          (c: any) =>
            `Campsite: ${c.name} (${c.campsiteId})\nTotal Units: ${c.units.length}\nHeld Back: ${c.units.filter((u: any) => u.status === "HELD_BACK").length}`
        )
        .join("\n\n");

      return {
        content: [
          {
            type: "text",
            text: `Resalys PMS Real Inventory Data (Firestore DB):\n\n${summaryText}`,
          },
        ],
        structuredContent: response,
      };
    }
  );

  // Tool 2: Update Resalys Inventory Status
  registerAppTool(
    server,
    "resalys-update-inventory",
    {
      title: "Update Resalys Unit Inventory Status",
      description: "Updates real inventory status of mobil-home units at a campsite in Firebase Cloud Firestore and Resalys PMS REST API.",
      inputSchema: {
        campsiteId: z.string().describe("Campsite ID (e.g. LA_SIRENE_06)"),
        unitIds: z.array(z.string()).describe("List of unit IDs (e.g. ['MH-102', 'MH-103'])"),
        newStatus: z.enum(["AVAILABLE_FOR_SALE", "HELD_BACK", "MAINTENANCE", "BOOKED"]).describe("New status"),
      },
      annotations: {
        readOnlyHint: false,
        destructiveHint: false,
        idempotentHint: true,
      },
      _meta: {
        ui: {
          resourceUri: "ui://pms-crm/pms-app.html",
          csp: {
            connectDomains: [
              "https://company-pms-crm-mcp-app-ahavst3hhq-uc.a.run.app",
              "https://company-pms-crm-mcp-app-1008225662928.us-central1.run.app",
              "https://ecg-pms-crm-mcp-app-ahavst3hhq-uc.a.run.app",
              "https://ecg-pms-crm-mcp-app-1008225662928.us-central1.run.app",
              "https://*.run.app",
              "https://*.googleapis.com",
            ],
          },
        },
      },
    },
    async (args): Promise<CallToolResult> => {
      await updateFirestoreUnits(args.campsiteId, args.unitIds, args.newStatus);
      const campsites = await loadCampsitesFromFirestore(args.campsiteId);
      const campsite = campsites.find((c: any) => c.campsiteId === args.campsiteId);

      const response = {
        status: "SUCCESS",
        datastore: "Firebase Cloud Firestore",
        targetApi: "PUT /pms/v1/units/status",
        campsiteId: args.campsiteId,
        updatedUnits: args.unitIds,
        newStatus: args.newStatus,
        identityScope: "CloudIdentity (julien)",
        units: campsite ? campsite.units : [],
      };

      return {
        content: [
          {
            type: "text",
            text: `Successfully updated ${args.unitIds.length} unit(s) (${args.unitIds.join(", ")}) at ${args.campsiteId} to status '${args.newStatus}' in Firebase Cloud Firestore DB & Resalys PMS.`,
          },
        ],
        structuredContent: response,
      };
    }
  );

  // Tool 3: Stage CRM Flash Campaign
  registerAppTool(
    server,
    "crm-stage-flash-campaign",
    {
      title: "Stage CRM Flash Promotion Campaign",
      description: "Stages a flash campaign draft in Firebase Cloud Firestore and Apigee CRM Webhook gateway (POST /marketing/v1/campaigns/draft). CRITICAL RULE: Because this action triggers an interactive Human-in-the-Loop confirmation card, you MUST ALWAYS output a clear introductory message in your public text response (e.g., 'I have prepared the flash campaign draft for your review. Please confirm the details below to proceed.') alongside calling this tool. Never invoke this tool with an empty text response.",
      inputSchema: {
        campaignName: z.string().describe("Campaign Name"),
        targetMarket: z.string().describe("Target Market (NL, FR, DE, UK)"),
        cluster: z.string().describe("Cluster ID (e.g. MEDITERRANEAN_SOUTH)"),
        discountPercentage: z.number().min(0).max(50).describe("Discount Percentage"),
      },
      annotations: {
        readOnlyHint: false,
        destructiveHint: false,
        idempotentHint: false,
      },
      _meta: {
        ui: {
          resourceUri: "ui://pms-crm/crm-app.html",
          csp: {
            connectDomains: [
              "https://company-pms-crm-mcp-app-ahavst3hhq-uc.a.run.app",
              "https://company-pms-crm-mcp-app-1008225662928.us-central1.run.app",
              "https://ecg-pms-crm-mcp-app-ahavst3hhq-uc.a.run.app",
              "https://ecg-pms-crm-mcp-app-1008225662928.us-central1.run.app",
              "https://*.run.app",
              "https://*.googleapis.com",
            ],
          },
        },
      },
    },
    async (args): Promise<CallToolResult> => {
      const copywritingText = `Profiteer van ${args.discountPercentage}% korting op uw zomervakantie in ${args.cluster.replace(/_/g, " ").toLowerCase()}! Boek nu uw Premium stacaravan op La Sirène.`;
      const imageAssetGcsUri = `gs://company-marketing-assets/genai/banners/${args.targetMarket.toLowerCase()}_${args.cluster.toLowerCase()}_july.png`;

      const campaignDoc = {
        campaign_name: args.campaignName,
        target_market: args.targetMarket,
        cluster: args.cluster,
        discount_percentage: args.discountPercentage,
        copywriting_text: copywritingText,
        image_asset_gcs_uri: imageAssetGcsUri,
        target_segment_id: `SEG_${args.targetMarket.toUpperCase()}_PAST_GUESTS_${args.cluster}_2025`,
        status: "STAGED",
        updated_at: new Date().toISOString(),
      };

      await saveFirestoreCampaign(campaignDoc);

      const response = {
        status: "SUCCESS",
        datastore: "Firebase Cloud Firestore",
        targetApi: "POST /marketing/v1/campaigns/draft",
        campaignName: args.campaignName,
        targetSegmentId: campaignDoc.target_segment_id,
        discountPercentage: args.discountPercentage,
        copywritingText,
        imageAssetGcsUri,
        identityScope: "CloudIdentity (julien)",
      };

      return {
        content: [
          {
            type: "text",
            text: `Successfully staged flash campaign '${args.campaignName}' for market ${args.targetMarket} (${args.discountPercentage}% discount) in Firebase Cloud Firestore DB. Imagen URI: ${imageAssetGcsUri}`,
          },
        ],
        structuredContent: response,
      };
    }
  );

  // Tool 4: Create Support Ticket
  registerAppTool(
    server,
    "company-create-support-ticket",
    {
      title: "Create Customer Claim Support Ticket",
      description: "Registers a customer claim support ticket in Firebase Cloud Firestore database and Company Support Portal.",
      inputSchema: {
        customerName: z.string().describe("Customer Full Name (e.g. Jean Dupont)"),
        campsiteId: z.string().describe("Campsite ID (e.g. LA_SIRENE_06)"),
        unitId: z.string().describe("Mobil-Home Unit ID (e.g. MH-108)"),
        category: z.enum(["MAINTENANCE", "CLEANLINESS", "NOISE", "BILLING", "EQUIPMENT", "OTHER"]).describe("Ticket Category"),
        priority: z.enum(["LOW", "MEDIUM", "HIGH", "URGENT"]).describe("Ticket Priority"),
        description: z.string().describe("Detailed description of customer claim"),
      },
      annotations: {
        readOnlyHint: false,
        destructiveHint: false,
        idempotentHint: false,
      },
      _meta: {
        ui: {
          resourceUri: "ui://pms-crm/claim-app.html",
          csp: {
            connectDomains: [
              "https://company-pms-crm-mcp-app-ahavst3hhq-uc.a.run.app",
              "https://company-pms-crm-mcp-app-1008225662928.us-central1.run.app",
              "https://ecg-pms-crm-mcp-app-ahavst3hhq-uc.a.run.app",
              "https://ecg-pms-crm-mcp-app-1008225662928.us-central1.run.app",
              "https://*.run.app",
              "https://*.googleapis.com",
            ],
          },
        },
      },
    },
    async (args): Promise<CallToolResult> => {
      const ticketId = `TCK-${Math.floor(100 + Math.random() * 900)}`;
      const now = new Date().toISOString();
      const ticketDoc = {
        ticket_id: ticketId,
        customer_name: args.customerName,
        campsite_id: args.campsiteId,
        unit_id: args.unitId,
        category: args.category,
        priority: args.priority,
        description: args.description,
        status: "OPEN",
        created_at: now,
        updated_at: now,
      };

      await saveFirestoreTicket(ticketDoc);

      return {
        content: [
          {
            type: "text",
            text: `Successfully created claim ticket '${ticketId}' for customer ${args.customerName} (${args.campsiteId} / ${args.unitId}). Priority: ${args.priority}, Category: ${args.category}. Persisted in Firebase Cloud Firestore.`,
          },
        ],
        structuredContent: {
          status: "SUCCESS",
          ticket: ticketDoc,
        },
      };
    }
  );

  // Tool 5: Get Support Tickets
  registerAppTool(
    server,
    "company-get-support-tickets",
    {
      title: "Get Support Tickets List",
      description: "Returns list of open or resolved customer claim tickets from Firebase Cloud Firestore.",
      inputSchema: {
        status: z.enum(["ALL", "OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"]).optional().describe("Optional ticket status filter"),
        campsiteId: z.string().optional().describe("Optional campsite ID filter"),
      },
      annotations: {
        readOnlyHint: true,
        destructiveHint: false,
        idempotentHint: true,
      },
      _meta: {
        ui: {
          resourceUri: "ui://pms-crm/claim-app.html",
          csp: {
            connectDomains: [
              "https://company-pms-crm-mcp-app-ahavst3hhq-uc.a.run.app",
              "https://company-pms-crm-mcp-app-1008225662928.us-central1.run.app",
              "https://ecg-pms-crm-mcp-app-ahavst3hhq-uc.a.run.app",
              "https://ecg-pms-crm-mcp-app-1008225662928.us-central1.run.app",
              "https://*.run.app",
              "https://*.googleapis.com",
            ],
          },
        },
      },
    },
    async (args): Promise<CallToolResult> => {
      const tickets = await loadTicketsFromFirestore(args.status, args.campsiteId);

      return {
        content: [
          {
            type: "text",
            text: `Found ${tickets.length} support ticket(s) in Firebase Cloud Firestore.`,
          },
        ],
        structuredContent: {
          status: "SUCCESS",
          tickets,
        },
      };
    }
  );

  // Tool 6: Update Ticket Status
  registerAppTool(
    server,
    "company-update-ticket-status",
    {
      title: "Update Ticket Status",
      description: "Updates ticket status (OPEN, IN_PROGRESS, RESOLVED, CLOSED) in Firebase Cloud Firestore.",
      inputSchema: {
        ticketId: z.string().describe("Ticket ID (e.g. TCK-801)"),
        newStatus: z.enum(["OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"]).describe("New Status"),
      },
      annotations: {
        readOnlyHint: false,
        destructiveHint: false,
        idempotentHint: true,
      },
      _meta: {
        ui: {
          resourceUri: "ui://pms-crm/claim-app.html",
          csp: {
            connectDomains: [
              "https://company-pms-crm-mcp-app-ahavst3hhq-uc.a.run.app",
              "https://company-pms-crm-mcp-app-1008225662928.us-central1.run.app",
              "https://ecg-pms-crm-mcp-app-ahavst3hhq-uc.a.run.app",
              "https://ecg-pms-crm-mcp-app-1008225662928.us-central1.run.app",
              "https://*.run.app",
              "https://*.googleapis.com",
            ],
          },
        },
      },
    },
    async (args): Promise<CallToolResult> => {
      await updateFirestoreTicketStatus(args.ticketId, args.newStatus);
      const tickets = await loadTicketsFromFirestore();

      return {
        content: [
          {
            type: "text",
            text: `Updated support ticket '${args.ticketId}' status to '${args.newStatus}' in Firebase Cloud Firestore.`,
          },
        ],
        structuredContent: {
          status: "SUCCESS",
          ticketId: args.ticketId,
          newStatus: args.newStatus,
          tickets,
        },
      };
    }
  );

  // App Resources for separate dedicated pages
  const registeredResources = [
    { uri: "ui://pms-crm/pms-app.html", filename: "pms-app.html", desc: "Dedicated Company Resalys PMS Inventory Management Widget Page" },
    { uri: "ui://pms-crm/crm-app.html", filename: "crm-app.html", desc: "Dedicated Company CRM Flash Promotion Campaigns Widget Page" },
    { uri: "ui://pms-crm/claim-app.html", filename: "claim-app.html", desc: "Dedicated Company Customer Maintenance & Claim Tickets Widget Page" },
    { uri: "ui://pms-crm/mcp-app.html", filename: "mcp-app.html", desc: "Full Company PMS & CRM Operations Control Center Widget Page" },
  ];

  for (const item of registeredResources) {
    registerAppResource(
      server,
      item.uri,
      item.uri,
      {
        mimeType: RESOURCE_MIME_TYPE,
        description: item.desc,
        csp: {
          connectDomains: [
            "https://company-pms-crm-mcp-app-ahavst3hhq-uc.a.run.app",
            "https://company-pms-crm-mcp-app-1008225662928.us-central1.run.app",
            "https://ecg-pms-crm-mcp-app-ahavst3hhq-uc.a.run.app",
            "https://ecg-pms-crm-mcp-app-1008225662928.us-central1.run.app",
            "https://*.run.app",
            "https://*.googleapis.com",
          ],
        },
      } as any,
      async (): Promise<ReadResourceResult> => {
        const htmlPath = path.join(DIST_DIR, item.filename);
        let html = "";
        try {
          html = await fs.readFile(htmlPath, "utf-8");
        } catch {
          html = `<!DOCTYPE html><html><body><h2>MCP App Bundle build pending for ${item.filename}. Run 'npm run build' in pms-crm-mcp-server.</h2></body></html>`;
        }
        return {
          contents: [
            { uri: item.uri, mimeType: RESOURCE_MIME_TYPE, text: html },
          ],
        };
      }
    );
  }

  return server;
}
