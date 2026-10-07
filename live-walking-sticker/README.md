# Live Walking Sticker

Mobile-friendly web app that turns a PNG/JPG photo into a transparent walking sticker.

## What it does

1. **Upload** a PNG or JPG of a person or character  
2. **Remove the background** in-browser (original face/identity pixels are preserved)  
3. **Animate** the cutout walking left ↔ right with a subtle bob  
4. **Preview** on a checkerboard with Play/Pause, speed, size, and distance controls  
5. **Export** as transparent GIF, WebM, APNG, or a Telegram-oriented 512×512 WebM sticker  

Identity rule: the app never redraws, beautifies, or regenerates faces — only background removal + translation.

## Stack

- React 19 + TypeScript + Vite  
- `@imgly/background-removal` (ONNX, client-side)  
- HTML5 Canvas for preview & frame rendering  
- `gifenc` (GIF), `upng-js` (APNG), `MediaRecorder` (WebM)

## Develop

```bash
cd live-walking-sticker
npm install
npm run dev
```

Open the printed local URL (COOP/COEP headers are set for `SharedArrayBuffer`).

## Build

```bash
npm run build
npm run preview
```

## Project layout

```
src/
  components/     Upload, preview, controls, export UI
  lib/
    animation.ts          Walk pose + canvas draw
    backgroundRemoval.ts  Identity-safe cutout
    export/               GIF / WebM / APNG / Telegram
```

## Telegram note

The Telegram export targets a **512×512 VP9 WebM ≤ ~3s, no audio**. Upload via [@Stickers](https://t.me/stickers) or the Bot API. Exact sticker-set limits can change; re-encode if Telegram rejects the file.
