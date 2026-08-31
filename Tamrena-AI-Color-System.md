# Tamrena-AI — Color System

This is the official color system for Tamrena-AI. Use these tokens consistently across every screen (landing page, auth, dashboard, workout plan, nutrition plan, live CV tracking, monthly reports). Do not introduce new colors outside this palette without updating this doc first.

**Design direction:** dark navy base, one primary accent (emerald) reserved for the single highest-priority action per screen, and a small set of category colors used consistently to represent specific feature types across the whole app (not randomly assigned per screen).

---

## 1. CSS Variables (drop-in)

```css
:root {
  /* ===== Backgrounds ===== */
  --bg-page: #0B0F1A;        /* page/app background */
  --bg-card: #131A2B;        /* cards, panels, modals, sign-in box */
  --bg-card-hover: #172038;  /* card hover state */
  --bg-input: #0F1524;       /* input fields */

  /* ===== Borders ===== */
  --border: #1E293B;         /* default card/input border */
  --border-strong: #2A3B52;  /* hover / focus border */

  /* ===== Primary accent (use sparingly — 1 primary action per screen) ===== */
  --accent-primary: #10B981;       /* emerald — primary buttons, active states, logo */
  --accent-primary-hover: #0EA371; /* emerald hover */
  --accent-primary-muted: #103A2E; /* emerald tint for subtle backgrounds/badges */

  /* ===== Category colors (fixed meaning — do not reassign) ===== */
  --category-nutrition: #10B981;   /* green — nutrition/meal features */
  --category-data: #38BDF8;        /* blue — InBody scanning, data/analytics */
  --category-motion: #F59E0B;      /* amber — live CV tracking, real-time/motion features */
  --category-ai: #A78BFA;          /* purple — AI reasoning, multi-agent, plan generation */

  /* ===== Text ===== */
  --text-heading: #F1F5F9;   /* headings, primary labels */
  --text-body: #94A3B8;      /* body copy, descriptions */
  --text-muted: #64748B;     /* captions, placeholders, disabled text */
  --text-on-accent: #062A1E; /* dark text placed on emerald/amber fills */

  /* ===== Status colors (standard semantic use only) ===== */
  --status-success: #10B981;
  --status-warning: #F59E0B;
  --status-error: #EF4444;
  --status-info: #38BDF8;
}
```

---

## 2. Color Reference Table

| Token | Hex | Role |
|---|---|---|
| `--bg-page` | `#0B0F1A` | Page background |
| `--bg-card` | `#131A2B` | Cards, panels, sign-in box |
| `--bg-card-hover` | `#172038` | Card hover |
| `--bg-input` | `#0F1524` | Input field backgrounds |
| `--border` | `#1E293B` | Default borders |
| `--border-strong` | `#2A3B52` | Hover/focus borders |
| `--accent-primary` | `#10B981` | Primary CTA, logo, active nav item |
| `--accent-primary-hover` | `#0EA371` | Primary CTA hover |
| `--accent-primary-muted` | `#103A2E` | Subtle emerald backgrounds (badges, highlights) |
| `--category-nutrition` | `#10B981` | Nutrition plan feature icons/badges |
| `--category-data` | `#38BDF8` | InBody scan / data & analytics feature icons |
| `--category-motion` | `#F59E0B` | Live CV tracking / real-time feature icons |
| `--category-ai` | `#A78BFA` | AI plan generation / multi-agent feature icons |
| `--text-heading` | `#F1F5F9` | Headings |
| `--text-body` | `#94A3B8` | Body text |
| `--text-muted` | `#64748B` | Captions, placeholders, disabled |
| `--status-success` | `#10B981` | Success states |
| `--status-warning` | `#F59E0B` | Warning states |
| `--status-error` | `#EF4444` | Error states |
| `--status-info` | `#38BDF8` | Info states |

---

## 3. Usage Rules

### Primary accent (emerald)
- Exactly **one** primary emerald element per screen: the main CTA button, or the active state of a key nav item — never both competing at once.
- Use `--accent-primary-muted` for soft backgrounds behind emerald icons/badges (e.g. a highlighted stat), not the full-saturation emerald as a fill for large areas.
- Text placed on a solid emerald fill must use `--text-on-accent` (dark), never white — for contrast.

### Category colors — fixed meaning, reuse everywhere
These four colors are **feature-type identifiers**, not decorative. Once assigned, keep them consistent across the entire app so users build a visual association:

| Feature area | Color | Example screens |
|---|---|---|
| Nutrition plans, meal cards, macros | `--category-nutrition` (green) | Nutrition plan generator, meal swap UI |
| InBody scan, data extraction, analytics, progress charts | `--category-data` (blue) | InBody upload, monthly comparison report |
| Live CV tracking, rep counting, real-time feedback | `--category-motion` (amber) | Live workout tracker, rep quality feedback |
| AI plan generation, multi-agent reasoning, "why this plan" explanations | `--category-ai` (purple) | Workout plan generation screen, AI rationale tooltips |

Do not use these four colors for anything outside their assigned category (e.g. don't use amber for a random warning badge — use `--status-warning`, which happens to share the same hex but is semantically separate).

### Text hierarchy
- `--text-heading` for all headings and primary labels.
- `--text-body` for descriptions, paragraph copy, secondary labels.
- `--text-muted` for placeholders, timestamps, disabled states, fine print.
- Never use pure white (`#FFFFFF`) or pure gray hex values directly in components — always reference the token.

### Borders & surfaces
- Default card/input border: `--border`.
- On hover/focus: transition to `--border-strong`, paired with `--bg-card-hover` for cards.
- Don't stack more than 2 elevation levels (`--bg-page` → `--bg-card`) in a single view; avoid a third floating layer unless it's a modal/dialog.

### Status colors
- Reserve `--status-success/warning/error/info` strictly for system feedback (toasts, form validation, alerts) — not for general UI decoration, even though some values overlap with category colors.

---

## 4. Component Quick Reference

**Primary button**
```css
background: var(--accent-primary);
color: var(--text-on-accent);
border: none;
border-radius: 8px;
```
Hover: `background: var(--accent-primary-hover);`

**Secondary button**
```css
background: transparent;
color: var(--text-heading);
border: 1px solid var(--border-strong);
border-radius: 8px;
```

**Feature card**
```css
background: var(--bg-card);
border: 1px solid var(--border);
border-radius: 12px;
```
Icon color = matching `--category-*` token for that feature.

**Input field**
```css
background: var(--bg-input);
border: 1px solid var(--border);
color: var(--text-heading);
```
Focus: `border-color: var(--border-strong);`

**Badge (category tag)**
```css
background: var(--accent-primary-muted); /* or category-specific muted variant */
color: var(--category-nutrition); /* matching category color */
border-radius: 999px;
padding: 4px 10px;
font-size: 12px;
```

---

## 5. Accessibility Notes

- `--text-body` (`#94A3B8`) on `--bg-page` (`#0B0F1A`) passes WCAG AA for normal text — do not lighten `--bg-page` without re-checking contrast.
- `--text-on-accent` (`#062A1E`) on `--accent-primary` (`#10B981`) is the required pairing for buttons — do not substitute white text on emerald.
- Never rely on category color alone to convey meaning (e.g. "this is a nutrition card") — always pair with an icon or label text, for colorblind accessibility.

---

## 6. Tailwind Config (optional, if using Tailwind)

```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        page: '#0B0F1A',
        card: '#131A2B',
        cardHover: '#172038',
        input: '#0F1524',
        border: '#1E293B',
        borderStrong: '#2A3B52',
        primary: {
          DEFAULT: '#10B981',
          hover: '#0EA371',
          muted: '#103A2E',
        },
        category: {
          nutrition: '#10B981',
          data: '#38BDF8',
          motion: '#F59E0B',
          ai: '#A78BFA',
        },
        text: {
          heading: '#F1F5F9',
          body: '#94A3B8',
          muted: '#64748B',
          onAccent: '#062A1E',
        },
        status: {
          success: '#10B981',
          warning: '#F59E0B',
          error: '#EF4444',
          info: '#38BDF8',
        },
      },
    },
  },
};
```

---

*Any new screen or component should reference these tokens directly rather than hardcoding hex values. If a new color need arises, add it to this document first so the whole team/agent stays in sync.*
