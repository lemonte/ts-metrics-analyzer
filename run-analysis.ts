import simpleGit from "simple-git";
import { execSync } from "child_process";
import { readFileSync, rmSync, cpSync } from "fs";
import path from "path";

const config = JSON.parse(readFileSync("config.json", "utf-8")) as {
  token: string;
  repoUrl: string;
};

const { token, repoUrl } = config;
const repoName = path.basename(repoUrl, ".git");
const cloneUrl = repoUrl.replace("https://", `https://${token}@`);

async function run() {
  const git = simpleGit();

  if (rmSync && typeof rmSync === "function" && repoName && repoName.length) {
    console.log("🧹 Removendo repositório anterior (se existir)...");
    rmSync(repoName, { recursive: true, force: true });
  }

  console.log("📦 Clonando repositório...");
  await git.clone(cloneUrl);

  // Copia o script para o repositório clonado
  cpSync("analyze-metrics.ts", `${repoName}/analyze-metrics.ts`);
  cpSync("index.html", `${repoName}/index.html`);

  console.log("🔍 Rodando análise de métricas...");
  execSync("npx ts-node analyze-metrics.ts", {
    cwd: repoName,
    stdio: "inherit"
  });

  console.log("✅ Análise concluída!");
}

run().catch(console.error);
