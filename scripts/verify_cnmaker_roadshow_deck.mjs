import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const artifactEntry = process.env.ARTIFACT_TOOL_ENTRY ||
  path.join(process.env.USERPROFILE || "", ".cache", "codex-runtimes", "codex-primary-runtime", "dependencies", "node", "node_modules", "@oai", "artifact-tool", "dist", "artifact_tool.mjs");
const { FileBlob, PresentationFile } = await import(pathToFileURL(artifactEntry).href);

const pptxPath = process.argv[2];
if (!pptxPath) {
  console.error("Usage: node scripts/verify_cnmaker_roadshow_deck.mjs <deck.pptx>");
  process.exit(2);
}
const absolutePptx = path.resolve(pptxPath);
const outDir = path.join(path.dirname(absolutePptx), "roadshow-import-verify");
await fs.mkdir(outDir, { recursive: true });
const presentation = await PresentationFile.importPptx(await FileBlob.load(absolutePptx));
const inspect = await presentation.inspect({ kind: "slide,textbox,image,chart", maxChars: 5000 });
await fs.writeFile(path.join(outDir, "import-inspect.ndjson"), inspect.ndjson);
const firstSlide = presentation.slides.items[0];
const png = await presentation.export({ slide: firstSlide, format: "png", scale: 1 });
await fs.writeFile(path.join(outDir, "slide-01-imported.png"), new Uint8Array(await png.arrayBuffer()));
console.log(JSON.stringify({
  ok: true,
  pptxPath: absolutePptx,
  slideCount: presentation.slides.items.length,
  verifyDir: outDir,
}, null, 2));
process.exit(0);
