// image.js
// Single source of truth for the official MannMitra logo:
// - Pink -> Purple gradient (#FF8FAB -> #9B5DE5)
// - M-monogram formed by two supporting hands
// - Heart in the center symbolizing care & mental wellbeing
// - Scalable SVG output with instance-unique gradient IDs

let gradientCounter = 0;
const passId = () => `mmLogoGrad_${++gradientCounter}`;

/**
 * Build the official MannMitra logo SVG as an HTML string.
 * @param {string} id - unique gradient id for this instance
 * @param {number} [size=40] - viewBox dimension
 */
function mmLogoSvg(id, size = 40) {
  const s = Number(size) || 40;
  return `<svg viewBox="0 0 100 100" width="${s}" height="${s}" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="${id}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FF8FAB"/>
      <stop offset="50%" stop-color="#E07BE0"/>
      <stop offset="100%" stop-color="#9B5DE5"/>
    </linearGradient>
    <filter id="${id}_glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="3" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
  </defs>
  <!-- Background Badge Circle -->
  <circle cx="50" cy="50" r="46" fill="url(#${id})" opacity="0.12" stroke="url(#${id})" stroke-width="2"/>

  <!-- Left Hand / Left stem of M -->
  <path d="M 22 72 C 20 54 26 36 36 28 C 42 23 48 26 48 34 C 48 48 38 60 34 72"
        fill="none" stroke="url(#${id})" stroke-width="6.5" stroke-linecap="round" stroke-linejoin="round"/>

  <!-- Right Hand / Right stem of M -->
  <path d="M 78 72 C 80 54 74 36 64 28 C 58 23 52 26 52 34 C 52 48 62 60 66 72"
        fill="none" stroke="url(#${id})" stroke-width="6.5" stroke-linecap="round" stroke-linejoin="round"/>

  <!-- Center Heart (Support & Empathy) -->
  <path d="M 50 48
           C 50 48 42 38 36 44
           C 30 50 34 58 50 68
           C 66 58 70 50 64 44
           C 58 38 50 48 50 48 Z"
        fill="url(#${id})"/>
</svg>`;
}

/**
 * Reusable avatar wrapper for chat messages and header.
 */
function mmLogoAvatar(size = 40) {
  return `<div class="message-avatar">${mmLogoSvg(passId(), size)}</div>`;
}
