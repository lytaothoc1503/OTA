import * as esbuild from "esbuild";
import { gzipSync } from "node:zlib";
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const outfile = resolve(here, "../../frontend/hero-shader.js");

const banner = `/*!
 * BanlaTravel hero shader island
 *
 * Bundles LiquidFormBackground from @designcodeio/threeui@1.2.0
 * https://github.com/MengTo/threeui (commit 68802d5428071ada5c20db8094b1649e6bb770ed)
 *
 * MIT License
 *
 * Copyright (c) 2026 Meng To
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 * This file also bundles React and ReactDOM 18.3.1
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 * MIT License: https://github.com/facebook/react/blob/main/LICENSE
 */`;

const result = await esbuild.build({
  absWorkingDir: here,
  entryPoints: ["src/mount.jsx"],
  outfile,
  bundle: true,
  format: "iife",
  platform: "browser",
  target: ["es2018"],
  jsx: "automatic",
  minify: true,
  legalComments: "none",
  banner: { js: banner },
  define: {
    "process.env.NODE_ENV": '"production"',
  },
  metafile: true,
  logLevel: "info",
});

const inputs = Object.keys(result.metafile.inputs);
const forbidden = inputs.filter((file) => /(?:^|\/)(three|three128|three165)(\/|$)/.test(file) || file.includes("node_modules/three"));
if (forbidden.length) {
  console.error("Bundle unexpectedly includes three:", forbidden);
  process.exit(1);
}

let js = readFileSync(outfile, "utf8");
// The pinned component hard-codes its DPR cap and exposes no dpr prop.
const defaultDprCap = "Math.min(window.devicePixelRatio||1,1.5)";
if (js.split(defaultDprCap).length - 1 !== 1) {
  console.error("Expected one LiquidFormBackground DPR cap in the bundled renderer");
  process.exit(1);
}
js = js.replace(defaultDprCap, "Math.min(window.devicePixelRatio||1,1.25)");
writeFileSync(outfile, js);
if (!js.includes("Meng To") || !js.includes("MIT License")) {
  console.error("MIT notice missing from bundle");
  process.exit(1);
}
if (!js.includes("u_noise_scale") || !js.includes("BanlaHeroShader")) {
  console.error("LiquidFormBackground shader or mount export missing");
  process.exit(1);
}
const assetUrls = [...js.matchAll(/https?:\/\/[^"'\s)]+/g)]
  .map((match) => match[0])
  .filter((url) => !url.startsWith("https://github.com/") && !url.startsWith("https://reactjs.org/") && !url.startsWith("http://www.w3.org/"));
if (assetUrls.length || /(?:^|[^.\w])\/OTA\//.test(js)) {
  console.error("Bundle contains an unexpected absolute or CDN URL", assetUrls);
  process.exit(1);
}

const bytes = Buffer.byteLength(js);
const gzip = gzipSync(js).length;
console.log(`wrote ${outfile}`);
console.log(`size ${bytes} bytes, gzip ${gzip}`);
console.log(`inputs ${inputs.length}; three bundled: no`);
