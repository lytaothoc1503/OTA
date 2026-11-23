import { createRoot } from "react-dom/client";
import { LiquidFormBackground } from "@designcodeio/threeui/components/LiquidFormBackground";

/**
 * LiquidFormBackground has no color uniforms. The published component tints the
 * canvas with CSS: sepia(tintAmount) saturate(1 + tintAmount * 5) hue-rotate(tintHue - 35).
 * Sepia's base hue is ~35°, so tintHue is the resulting hue. #329DD2 is hsl(200, 65%, 51%).
 * Highlights in the metal shader stay near white (#F8FAFC) after that tint.
 * mouseAmount is 0 because the host is pointer-events: none (the search dock must stay clickable).
 */
const SKY_LIQUID = {
  speed: 0.55,
  morph: 0.72,
  noiseScale: 0.8,
  mouseAmount: 0,
  metal: 0.62,
  camera: 6.4,
  tintHue: 200,
  tintAmount: 0.88,
};

let root = null;

function mount(el) {
  if (!el) return;
  unmount();
  root = createRoot(el);
  root.render(<LiquidFormBackground {...SKY_LIQUID} />);
}

function unmount() {
  if (!root) return;
  root.unmount();
  root = null;
}

window.BanlaHeroShader = { mount, unmount };
