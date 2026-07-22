import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import cors from "cors";
import express from "express";
import type { Request, Response } from "express";
import fs from "node:fs/promises";
import path from "node:path";
import {
  createServer,
  loadCampsitesFromFirestore,
  updateFirestoreUnits,
  saveFirestoreCampaign,
  loadCampaignsFromFirestore,
  loadTicketsFromFirestore,
  saveFirestoreTicket,
  updateFirestoreTicketStatus,
} from "./server.js";

const DIST_DIR = import.meta.filename.endsWith(".ts")
  ? path.join(import.meta.dirname, "dist")
  : import.meta.dirname;

export async function startStreamableHTTPServer(
  createServer: () => McpServer
): Promise<void> {
  const port = parseInt(process.env.PORT ?? "3002", 10);
  const app = express();
  app.use(express.static(DIST_DIR));

  app.use((_req, res, next) => {
    res.setHeader(
      "Content-Security-Policy",
      "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob: https:; connect-src 'self' https://ecg-pms-crm-mcp-app-ahavst3hhq-uc.a.run.app https://ecg-pms-crm-mcp-app-1008225662928.us-central1.run.app https://*.run.app https://*.googleapis.com;"
    );
    next();
  });

  app.get(["/", "/healthz"], (_req: Request, res: Response) => {
    res.json({
      status: "ok",
      server: "ecg-pms-crm-mcp-app-server",
      endpoints: [
        "/mcp",
        "/sse",
        "/pms-app.html",
        "/crm-app.html",
        "/claim-app.html",
        "/mcp-app.html",
        "/widget",
        "/api/pms-inventory",
        "/api/resalys-update-inventory",
        "/api/crm-campaigns",
        "/api/support-tickets",
      ],
    });
  });

  const serveHtml = (filename: string) => async (_req: Request, res: Response) => {
    const htmlPath = path.join(DIST_DIR, filename);
    try {
      const html = await fs.readFile(htmlPath, "utf-8");
      res.setHeader("Content-Type", "text/html");
      res.send(html);
    } catch {
      res.status(404).send(`HTML bundle '${filename}' not found. Please run 'npm run build' first.`);
    }
  };

  app.get(["/pms-app.html", "/pms"], serveHtml("pms-app.html"));
  app.get(["/crm-app.html", "/crm"], serveHtml("crm-app.html"));
  app.get(["/claim-app.html", "/claim", "/tickets"], serveHtml("claim-app.html"));
  app.get(["/mcp-app.html", "/widget"], serveHtml("mcp-app.html"));

  // Apply JSON body parser ONLY to /api routes
  const apiRouter = express.Router();
  apiRouter.use(express.json());

  apiRouter.get("/pms-inventory", async (req: Request, res: Response) => {
    try {
      const campsiteId = (req.query.campsiteId || req.query.campsite_id) as string | undefined;
      const campsites = await loadCampsitesFromFirestore(campsiteId);
      res.json({ status: "SUCCESS", campsites });
    } catch (e: any) {
      console.error("GET /api/pms-inventory error:", e);
      res.status(500).json({ status: "ERROR", error: String(e?.message || e) });
    }
  });

  apiRouter.get("/crm-campaigns", async (_req: Request, res: Response) => {
    try {
      const campaigns = await loadCampaignsFromFirestore();
      res.json({ status: "SUCCESS", campaigns });
    } catch (e: any) {
      console.error("GET /api/crm-campaigns error:", e);
      res.status(500).json({ status: "ERROR", error: String(e?.message || e) });
    }
  });

  apiRouter.get("/support-tickets", async (req: Request, res: Response) => {
    try {
      const status = req.query.status as string | undefined;
      const campsiteId = req.query.campsiteId as string | undefined;
      const tickets = await loadTicketsFromFirestore(status, campsiteId);
      res.json({ status: "SUCCESS", tickets });
    } catch (e: any) {
      console.error("GET /api/support-tickets error:", e);
      res.status(500).json({ status: "ERROR", error: String(e?.message || e) });
    }
  });

  apiRouter.post("/support-tickets", async (req: Request, res: Response) => {
    try {
      const body = req.body || {};
      const ticketId = body.ticketId || body.ticket_id || `TCK-${Math.floor(100 + Math.random() * 900)}`;
      const now = new Date().toISOString();
      const ticketDoc = {
        ticket_id: ticketId,
        customer_name: body.customerName || body.customer_name || "Anonymous Guest",
        campsite_id: body.campsiteId || body.campsite_id || "LA_SIRENE_06",
        unit_id: body.unitId || body.unit_id || "MH-102",
        category: body.category || "MAINTENANCE",
        priority: body.priority || "MEDIUM",
        description: body.description || "No details provided.",
        status: "OPEN",
        created_at: now,
        updated_at: now,
      };

      await saveFirestoreTicket(ticketDoc);
      const tickets = await loadTicketsFromFirestore();
      res.json({ status: "SUCCESS", ticket: ticketDoc, tickets });
    } catch (e: any) {
      console.error("POST /api/support-tickets error:", e);
      res.status(500).json({ status: "ERROR", error: String(e?.message || e) });
    }
  });

  apiRouter.post("/support-tickets/update-status", async (req: Request, res: Response) => {
    try {
      const { ticketId, ticket_id, newStatus, new_status } = req.body || {};
      const tid = ticketId || ticket_id;
      const st = newStatus || new_status;
      if (!tid || !st) {
        res.status(400).json({ status: "VALIDATION_ERROR", error: "Missing required ticketId or newStatus" });
        return;
      }
      await updateFirestoreTicketStatus(tid, st);
      const tickets = await loadTicketsFromFirestore();
      res.json({ status: "SUCCESS", ticketId: tid, newStatus: st, tickets });
    } catch (e: any) {
      console.error("POST /api/support-tickets/update-status error:", e);
      res.status(500).json({ status: "ERROR", error: String(e?.message || e) });
    }
  });

  apiRouter.post("/resalys-update-inventory", async (req: Request, res: Response) => {
    try {
      const body = req.body || {};
      const campsiteId = body.campsiteId || body.campsite_id || "LA_SIRENE_06";
      let unitIds = body.unitIds || body.unit_ids || [];
      if (typeof unitIds === "string") unitIds = [unitIds];
      const newStatus = body.newStatus || body.new_status || "AVAILABLE_FOR_SALE";

      if (!campsiteId || !unitIds.length) {
        res.status(400).json({ status: "VALIDATION_ERROR", error: "Missing required campsiteId or unitIds" });
        return;
      }

      await updateFirestoreUnits(campsiteId, unitIds, newStatus);
      const campsites = await loadCampsitesFromFirestore(campsiteId);
      res.json({ status: "SUCCESS", campsiteId, updatedUnits: unitIds, newStatus, campsites });
    } catch (e: any) {
      console.error("POST /api/resalys-update-inventory error:", e);
      res.status(500).json({ status: "ERROR", error: String(e?.message || e) });
    }
  });

  apiRouter.post("/crm-stage-flash-campaign", async (req: Request, res: Response) => {
    try {
      const body = req.body || {};
      const campaignName = body.campaignName || body.campaign_name || `Flash_Promo_${Date.now()}`;
      const targetMarket = body.targetMarket || body.target_market || "NL";
      const cluster = body.cluster || "MEDITERRANEAN_SOUTH";
      const discountPercentage = body.discountPercentage ?? body.discount_percentage ?? 15;
      const copywritingText = body.copywritingText || body.copywriting_text ||
        `Profiteer van ${discountPercentage}% korting op uw zomervakantie in ${cluster.replace(/_/g, " ").toLowerCase()}! Boek nu uw Premium stacaravan op La Sirène.`;
      const imageAssetGcsUri = body.imageAssetGcsUri || body.image_asset_gcs_uri ||
        `gs://ecg-marketing-assets/genai/banners/${targetMarket.toLowerCase()}_${cluster.toLowerCase()}_july.png`;

      const campaignDoc = {
        campaign_name: campaignName,
        target_market: targetMarket,
        cluster,
        discount_percentage: discountPercentage,
        copywriting_text: copywritingText,
        image_asset_gcs_uri: imageAssetGcsUri,
        target_segment_id: `SEG_${targetMarket.toUpperCase()}_PAST_GUESTS_${cluster}_2025`,
        status: "STAGED",
        updated_at: new Date().toISOString(),
      };
      await saveFirestoreCampaign(campaignDoc);
      res.json({ status: "SUCCESS", campaignDoc });
    } catch (e: any) {
      console.error("POST /api/crm-stage-flash-campaign error:", e);
      res.status(500).json({ status: "ERROR", error: String(e?.message || e) });
    }
  });

  app.use("/api", apiRouter);

  const mcpHandler = async (req: Request, res: Response) => {
    const server = createServer();
    const transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: undefined,
    });

    res.on("close", () => {
      transport.close().catch(() => {});
      server.close().catch(() => {});
    });

    try {
      await server.connect(transport);
      await transport.handleRequest(req, res, req.body);
    } catch (error) {
      console.error("MCP error:", error);
      if (!res.headersSent) {
        res.status(500).json({
          jsonrpc: "2.0",
          error: { code: -32603, message: "Internal server error" },
          id: null,
        });
      }
    }
  };

  app.all("/mcp", mcpHandler);
  app.all("/sse", mcpHandler);

  const httpServer = app.listen(port, (err?: Error) => {
    if (err) {
      console.error("Failed to start server:", err);
      process.exit(1);
    }
    console.log(`=======================================================`);
    console.log(` ECG PMS & CRM MCP App Server Running`);
    console.log(` HTTP Endpoint : http://localhost:${port}/mcp`);
    console.log(` Web Widget UI : http://localhost:${port}/widget`);
    console.log(`=======================================================`);
  });

  const shutdown = () => {
    console.log("\nShutting down server...");
    httpServer.close(() => process.exit(0));
  };

  process.on("SIGINT", shutdown);
  process.on("SIGTERM", shutdown);
}

export async function startStdioServer(
  createServer: () => McpServer
): Promise<void> {
  await createServer().connect(new StdioServerTransport());
}

async function main() {
  if (process.argv.includes("--stdio")) {
    await startStdioServer(createServer);
  } else {
    await startStreamableHTTPServer(createServer);
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
