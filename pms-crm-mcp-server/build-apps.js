import { build } from "vite";
import { viteSingleFile } from "vite-plugin-singlefile";

const pages = [
  { name: "mcp", input: "mcp-app.html" },
  { name: "pms", input: "pms-app.html" },
  { name: "crm", input: "crm-app.html" },
  { name: "claim", input: "claim-app.html" },
];

async function buildAll() {
  console.log("Building singlefile HTML bundles for each dedicated page...");
  for (const page of pages) {
    console.log(`Building ${page.input}...`);
    await build({
      configFile: false,
      plugins: [viteSingleFile()],
      build: {
        target: "esnext",
        assetsInlineLimit: 100000000,
        chunkSizeWarningLimit: 100000000,
        cssCodeSplit: false,
        outDir: "dist",
        emptyOutDir: page.name === "mcp", // empty outDir only on first run
        rollupOptions: {
          input: page.input,
        },
      },
    });
    console.log(`✅ ${page.input} successfully bundled!`);
  }
}

buildAll().catch((err) => {
  console.error("Build failed:", err);
  process.exit(1);
});
