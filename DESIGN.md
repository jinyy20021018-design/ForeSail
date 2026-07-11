# ForeSail DESIGN.md — Freight Studio

Visual system for the ForeSail trade-risk app. Register: **product / command deck**.
A **floating rounded canvas on a soft gray desk**, near-white cards, **999px capsules**
everywhere (buttons, tabs, chips, badges), a **black accent** for the single primary CTA,
misty semantic colors, and one **dark real map** as the deliberate contrast island.
UI language: **English**. Source of truth for pixels: `frontend/prototype/restyle/foresail-overview-demo.html`.

## Color (Freight Studio palette)

```
--canvas: #EBEDF1   /* app-frame canvas */          desk (body): #C7CBD2
--card:   #FAFBFD   /* surfaces */        --card2:  #F0F2F7  /* inset strips */
--ink:    #2C323B   /* text */            --black:  #2E3542  /* primary CTA, active tab/step */
--muted:  #747B88                         --faint:  #A5ACB9
--red:    #C4747C / #F3EBED (soft)   AT_RISK / ACTION_REQUIRED / your-risk
--amber:  #C69D66 / #F3EEE4 (soft)   watch / due-soon
--blue:   #5F7FD0 / #E8EDF8 (soft)   links, selection, counterparty
--green:  #67A08E / #E8F0EC (soft)   clear / complete / ok
```
Status is always **color + label** in a capsule, never color alone. Semantic red/amber/green
are reserved for status; blue is selection/links/counterparty.

## Type
`"Plus Jakarta Sans"` (self-hosted via `@fontsource`, weights 400–800), falling back to
`-apple-system, "Segoe UI", "PingFang SC", "Microsoft YaHei"`. Tabular nums for money/dates/countdowns.

## Shape & elevation
- Radius: **26** hero panels, **20** cards, **16** medium, **10** inputs, **999px** all pills.
- App frame: `max-width 1300`, radius 32, radial-gradient highlights, `0 24px 80px` shadow.
- Elevation is **shadow, not border**: `--shadow: 0 2px 10px rgba(20,20,20,.05)`. Avoid hard borders on cards.

## Components
- **Buttons**: primary = **black pill** (one hero CTA per view); secondary/ghost = **white card pill**.
- **Tabs**: capsule; active = black fill, white text (top `.fsnav` app-mode nav and the 9 `.fs2-tabs` workspace tabs).
- **Badges / chips / status pills / classification**: 999px capsule on a `-soft` tint.
- **Inputs / selects**: radius 10, light border, card fill.
- **Case rows**: individual floating capsule cards on a transparent rail; open button = black circle.

## Signature layout
- **Overview command deck** (`WorkspaceOverview` + scoped `fs2-overview.css`): hazard flight-cards row,
  countdown card, black "Next actions" checklist card, Route Risk Deck, shipment info, exposure flag chips.
- **Route Risk Deck** (`RouteChart` → `RouteLeafletMap`): the **Map** segment is the **real Leaflet map**
  (CARTO dark basemap + route legs, ports, event markers, typhoon cones/track, corridor states, vessel);
  Legs/Weather segments keep the schematic SVG. The dark map is embedded in the light deck via
  `isolation:isolate` (rounded-corner clip) with circular dark-glass zoom controls.

## CSS architecture
Layers load in order (`main.tsx`): fonts → `styles.css` (legacy) → `normalized.css` (structure +
`!important`) → **`styles/theme.css`** (global Freight Studio layer: re-points legacy tokens, reshapes
shared components into capsules) + scoped `styles/fs2-overview.css` (Overview only, untouched).
To restyle globally, edit `theme.css`; structural grids/list rows live in `normalized.css`.

## Bans
No hard-bordered cards. No bright royal blue (use misty `#5F7FD0`). No color-only status.
No fake stylized "map" for the Map segment — the real Leaflet map is primary. UI copy in English.
