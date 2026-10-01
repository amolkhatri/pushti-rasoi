// Renders an HTML reel to MP4 (1080×1920, 30 fps).
// Usage: cd promo && npm install && node render.mjs
// Options (env): PAGE=reel.html SECONDS=15 MUSIC=assets/music.wav OUT=pushti-rasoi-reel.mp4
import { chromium } from "playwright-core";
import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, rmSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const dir = path.dirname(fileURLToPath(import.meta.url));
const FPS = 30, W = 1080, H = 1920;
const PAGE = process.env.PAGE || "reel.html";
const SECONDS = Number(process.env.SECONDS || 15);
const OUT = path.resolve(dir, process.env.OUT || "pushti-rasoi-reel.mp4");
const frames = path.join(dir, "frames");
rmSync(frames, { recursive: true, force: true });
mkdirSync(frames);

const browser = await chromium.launch({
  executablePath: process.env.CHROME || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
});
const page = await browser.newPage({ viewport: { width: W, height: H } });
await page.goto("file://" + path.join(dir, PAGE));
await page.evaluate(async () => {
  await document.fonts.ready;
  await Promise.all([...document.images].map(i => i.decode().catch(() => {})));
});

// PREVIEW="2,5.5,9" saves stills at those seconds instead of rendering the video.
if (process.env.PREVIEW) {
  for (const s of process.env.PREVIEW.split(",").map(Number)) {
    await page.evaluate(ms => document.getAnimations().forEach(a => { a.pause(); a.currentTime = ms; }), s * 1000);
    await page.screenshot({ path: path.join(frames, `preview-${s}s.jpg`), type: "jpeg", quality: 80 });
  }
  await browser.close();
  console.log("previews in", frames);
  process.exit(0);
}

for (let f = 0; f < FPS * SECONDS; f++) {
  // Seek every CSS animation to this frame's time so output is deterministic.
  await page.evaluate(ms => document.getAnimations().forEach(a => { a.pause(); a.currentTime = ms; }), (f * 1000) / FPS);
  await page.screenshot({ path: path.join(frames, String(f).padStart(4, "0") + ".jpg"), type: "jpeg", quality: 95 });
}
await browser.close();

// Background music (generate with one of the music_*.py scripts).
const music = path.resolve(dir, process.env.MUSIC || "assets/music.wav");
execFileSync("ffmpeg", ["-y", "-loglevel", "error", "-framerate", String(FPS), "-i", path.join(frames, "%04d.jpg"),
  ...(existsSync(music) ? ["-i", music, "-af", "loudnorm=I=-14:TP=-1.5:LRA=7", "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-shortest"] : []),
  "-c:v", "libx264", "-profile:v", "high", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
  OUT], { stdio: "inherit" });
rmSync(frames, { recursive: true, force: true });
console.log("wrote", OUT);
