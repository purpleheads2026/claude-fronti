// Rigenera docs/img/tav-0N-{it,en}.png dalle tavole di docs/index.html.
// Uso: cd tools && npm install && npx playwright install chromium && npm run tavole
import { chromium } from "playwright";
import { fileURLToPath, pathToFileURL } from "node:url";
import { dirname, resolve } from "node:path";

const qui = dirname(fileURLToPath(import.meta.url));
const pagina = pathToFileURL(resolve(qui, "../docs/index.html")).href;
const uscita = resolve(qui, "../docs/img");

const browser = await chromium.launch();
for (const lingua of ["it", "en"]) {
  const contesto = await browser.newContext({
    viewport: { width: 1328, height: 1000 }, deviceScaleFactor: 2, colorScheme: "light", reducedMotion: "reduce",
  });
  const p = await contesto.newPage();
  await p.goto(`${pagina}?lang=${lingua}`, { waitUntil: "networkidle" });
  await p.evaluate(() => document.fonts.ready);
  for (const tavola of await p.locator(".tavola").all()) {
    const id = await tavola.getAttribute("id");
    await tavola.screenshot({ path: `${uscita}/${id}-${lingua}.png`, animations: "disabled" });
    console.log(`${id}-${lingua}.png`);
  }
  await contesto.close();
}
await browser.close();
