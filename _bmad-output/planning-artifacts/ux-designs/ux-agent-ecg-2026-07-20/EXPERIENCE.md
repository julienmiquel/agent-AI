---
name: 'ECG Multi-Agent User Experience Specification'
type: experience-spine
status: 'final'
created: '2026-07-20'
updated: '2026-07-20'
design_reference: 'DESIGN.md'
---

# User Experience Specification: ECG Multi-Agent Interface

## 1. Foundation

The ECG Multi-Agent Interface operates **natively inside the Gemini Enterprise Application** (Discovery Engine / Agent Builder chat interface). The core chat container, navigation shell, theme defaults, and input bar are hosted by Gemini Enterprise.

Our custom UX footprint focuses on **Agent Extension Cards**, **Rich Tool Output Widgets** (Yield reports), and **Human-in-the-Loop (HITL) Action Confirmation Cards** rendered inline within the Gemini Enterprise conversational stream.

Visual tokens and extension component styling are anchored in `{design_reference}` (`DESIGN.md`).

---

## 2. Information Architecture (Gemini Enterprise Host Environment)

```
+-------------------------------------------------------------------------------+
| Gemini Enterprise App Host Shell (Google Workspace SSO & Identity)           |
+-------------------------------------------------------------------------------+
| Gemini Agent Workspace Thread                                                 |
| +---------------------------------------------------------------------------+ |
| | Conversation Stream                                                       | |
| | - User Prompts                                                            | |
| | - Gemini Agent Markdown Responses                                         | |
| | - Inline Yield Analytics Cards (Rich Structured Output)                   | |
| | - Inline Interactive HITL Approval Cards (Action Manifest & Approval Buttons)| |
| +---------------------------------------------------------------------------+ |
| | Gemini Enterprise Input Field (Text + File/Voice Attachments)             | |
+-------------------------------------------------------------------------------+
```

---

## 3. Voice and Tone (Microcopy)

- **Tone:** Executive, precise, actionable, transparent.
- **Agent Microcopy Principles:**
  - **Directness:** Lead with key metrics or transaction status before technical explanations.
  - **Transparency:** State exact parameters when asking for HITL approvals (e.g., *"Requesting approval to update 4 mobil-homes to AVAILABLE_FOR_SALE at La Sirène"*).
  - **Error Messages:** Explicit, non-blaming explanations with actionable resolution options.

---

## 4. Component Patterns & Behaviors

### 4.1 Chat Thread & Message Bubbles
- Messages append dynamically with smooth auto-scroll.
- Agent thinking states display a animated pulse indicator (`"Yield Analytics Agent is querying BigQuery..."`).
- Code snippets (SQL, JSON payloads) render inside copyable block containers.

### 4.2 HITL Approval Card Pattern
- **Trigger:** Intercepts any HTTP `PUT`, `POST`, `PATCH`, or `DELETE` request before tool execution.
- **Card Structure:**
  - Header: Warning badge (`{colors.accent-amber}`) with action title (e.g., *"Action Required: Update PMS Inventory"*).
  - Manifest Table: Target API endpoint, Campsite ID, Unit IDs, Target Status, Identity Scope.
  - Action Footer: Primary button **Approve** (`{components.button-primary}`), Secondary button **Reject** (`{components.button-danger}`).
- **Behavior:** Clicking `Approve` changes card status to `"Approved — Executing..."` with a progress spinner, then resolves into a green success confirmation toast.

---

## 5. State Patterns

| State | Visual & Behavioral Manifestation |
| --- | --- |
| **Idle / Ready** | Input field focused, recent session history loaded. |
| **Agent Thinking** | Thinking pulse animation under last user message; input field disabled. |
| **HITL Pending** | Chat thread auto-scrolls to HITL Approval Card; interactive buttons active; keyboard focus on `Approve`. |
| **Executing Mutation** | HITL card buttons disable; loading spinner active; card header updates to `"Executing..."`. |
| **Mutation Confirmed** | Card background transitions to subtle green tint (`{colors.accent-emerald}`); confirmation timestamp added. |
| **Mutation Rejected** | Card background transitions to subtle red tint (`{colors.accent-rose}`); cancellation note logged in thread. |

---

## 6. Accessibility Floor (a11y)

- **Keyboard Navigation:** Full tab-stop support across prompt input, HITL cards, and action buttons. Pressing `Enter` on an active HITL card defaults to `Approve`.
- **Screen Reader ARIA:** HITL cards use `role="dialog"` and `aria-live="assertive"` to announce approval prompts immediately.
- **Color Contrast:** All body text meets WCAG AA standards (minimum 4.5:1 contrast against `{colors.bg-dark}` and `{colors.surface-card}`).

---

## 7. Key User Flows

### Flow 1: Yield Anomaly Analysis to PMS Inventory Unlock (Marc)
- **Protagonist:** Marc, Regional Yield Manager for Mediterranean campsite clusters.
- **Context:** Monday morning yield review showing low July occupancy.
- **Beats:**
  1. Marc opens the web console and types: *"Analyze July occupancy for Mediterranean South cluster"*.
  2. Agent processes NL-to-SQL and displays the Yield Analytics Report Widget (72% Occupancy, 15% Dutch lag, 4 held-back units at *La Sirène*).
  3. Marc types: *"Release mobil-homes MH-102 to MH-105 at La Sirène to sale"*.
  4. Agent pauses and presents the HITL Approval Card showing Resalys `PUT` payload details.
  5. Marc inspects the manifest and clicks **Approve** (or presses `Enter`).
  6. The card updates to **Confirmed**, and Resalys inventory is live for sale within 2 seconds.
- **Climax:** Marc sees the immediate status transition from held-back to `AVAILABLE_FOR_SALE` with full audit trace confirmation.
