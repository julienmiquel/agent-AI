---
name: 'ECG Multi-Agent System Design System'
description: 'Design system for the ECG Yield & Operations Multi-Agent Web Interface.'
status: 'final'
created: '2026-07-20'
updated: '2026-07-20'
colors:
  bg-dark: '#090d16'
  surface-card: 'rgba(22, 30, 46, 0.75)'
  surface-card-border: 'rgba(56, 189, 248, 0.15)'
  text-primary: '#f3f4f6'
  text-secondary: '#9ca3af'
  accent-cyan: '#38bdf8'
  accent-indigo: '#6366f1'
  accent-emerald: '#10b981'
  accent-amber: '#f59e0b'
  accent-rose: '#f43f5e'
typography:
  fontFamily: "'Inter', sans-serif"
  fontFamilyCode: "'JetBrains Mono', monospace"
  heading1: { fontSize: '28px', fontWeight: '700', lineHeight: '1.2' }
  heading2: { fontSize: '20px', fontWeight: '600', lineHeight: '1.3' }
  heading3: { fontSize: '16px', fontWeight: '600', lineHeight: '1.4' }
  body: { fontSize: '14px', fontWeight: '400', lineHeight: '1.6' }
  code: { fontSize: '13px', fontWeight: '400', lineHeight: '1.5' }
rounded:
  sm: '4px'
  md: '8px'
  lg: '14px'
  full: '9999px'
spacing:
  '1': '4px'
  '2': '8px'
  '3': '12px'
  '4': '16px'
  '6': '24px'
  '8': '32px'
components:
  card-glass:
    background: '{colors.surface-card}'
    border: '1px solid {colors.surface-card-border}'
    borderRadius: '{rounded.lg}'
    backdropFilter: 'blur(16px)'
  hitl-card:
    background: 'rgba(30, 41, 59, 0.9)'
    border: '1px solid {colors.accent-amber}'
    borderRadius: '{rounded.lg}'
  button-primary:
    background: 'linear-gradient(135deg, {colors.accent-cyan}, {colors.accent-indigo})'
    color: '#ffffff'
    borderRadius: '{rounded.md}'
  button-danger:
    background: '{colors.accent-rose}'
    color: '#ffffff'
    borderRadius: '{rounded.md}'
---

# Design System: ECG Multi-Agent Interface

## Brand & Style
The visual identity operates within the **Gemini Enterprise Application** host environment (Discovery Engine / Agent Builder). The outer container, navigation header, and text input bar inherit from Gemini Enterprise's native UI shell. Our custom visual identity governs the **inline extension cards**, **data widgets**, and **Human-in-the-Loop (HITL) approval components** embedded within the conversational stream.

The card aesthetic projects high-tech precision and operational trust, utilizing dark glassmorphic surfaces (`{colors.surface-card}`), clear status badges, and prominent action buttons for HITL sign-offs.

## Colors
- **Canvas Base (`{colors.bg-dark}`):** Deep obsidian dark background ensuring maximum visual comfort during extended operational sessions.
- **Card Surfaces (`{colors.surface-card}`):** Semi-transparent slate blue glass with subtle backdrop blur.
- **Primary Brand Accent (`{colors.accent-cyan}`):** Vibrant cyan used for active states, highlights, and primary data callouts.
- **Secondary Accent (`{colors.accent-indigo}`):** Deep indigo used in gradients and container borders.
- **Status Indicators:**
  - **Success / Positive (`{colors.accent-emerald}`):** Inventory release confirmations, target occupancy met.
  - **Warning / Action Required (`{colors.accent-amber}`):** Human-in-the-Loop (HITL) approval cards requiring decision.
  - **Critical / Reject (`{colors.accent-rose}`):** Destructive actions, system alerts, rejected transactions.

## Typography
Uses **Inter** for clean readability across text, charts, and table summaries. **JetBrains Mono** is utilized for code fragments, SQL queries, API endpoints, and payload JSON manifests.

## Layout & Spacing
Built on an 8-point spatial grid (`4px`, `8px`, `16px`, `24px`, `32px`). Margins and padding scale predictably across chat threads, card widgets, and detail overlays.

## Elevation & Depth
Depth is created using subtle border highlights (`rgba(56, 189, 248, 0.15)`) and multi-layered backdrop blur filters (`blur(16px)`), eliminating heavy drop shadows while maintaining clear spatial separation.

## Shapes
Card containers feature smooth `14px` (`{rounded.lg}`) corner radii. Action buttons and input fields utilize `8px` (`{rounded.md}`) radii. Badges and status indicators use fully rounded pills (`{rounded.full}`).

## Components

### 1. Conversational Chat Thread
Message bubbles distinguish user turns from agent responses. User prompts are right-aligned with an indigo accent gradient background; agent messages are left-aligned inside glassmorphic containers.

### 2. HITL Interactive Approval Card
Prominently framed with an amber accent border (`{colors.accent-amber}`). Displays a structured action manifest (Target Service, Endpoint, Payload Parameters) with two side-by-side action buttons: **Approve** (Cyan/Indigo primary gradient) and **Reject** (Rose outline).

### 3. Yield Analytics Widget
Displays a circular gauge for Occupancy Rate, paired with key metric cards for AVPN and RevPAR. Includes warning callouts for lagging customer market segments.

## Do's and Don'ts

- **DO:** Keep HITL approval manifests readable with clean key-value parameter pairs.
- **DO:** Use `{colors.accent-amber}` exclusively for items requiring explicit human authorization.
- **DON'T:** Use bright un-tinted red or green backgrounds; rely on curated HSL/HEX status badges.
- **DON'T:** Overcrowd the chat thread; use collapsable cards for lengthy SQL or JSON raw responses.
