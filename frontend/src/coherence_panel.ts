/**
 * Phase 4f: Collapsible coherence panel.
 *
 * The panel is rendered closed by default in ``index_v1.html`` so the
 * v0.1 visual baseline is byte-identical (modulo a small toggle
 * button in the top-right corner). On first expand we GET
 * ``/coherence``, render a per-topic table, and cache the result so
 * subsequent toggles are instantaneous.
 *
 * Kept dependency-free (vanilla DOM) so it doesn't bloat the bundle.
 */

interface TveWindow extends Window {
  TVE?: {
    coherenceK?: number;
    coherenceTopicLabel0Based?: (i: number) => string;
    invalidateCoherenceCache?: () => void;
  };
}

interface CoherenceResponse {
  npmi: (number | null)[];
  c_v: (number | null)[];
  segregation: (number | null)[];
  coverage: (number | null)[];
  labels?: string[];
  mean_npmi?: number | null;
  mean_c_v?: number | null;
}

let cached: CoherenceResponse | null = null;
let inflight = false;

const w = window as TveWindow;
w.TVE = w.TVE || {};
w.TVE.invalidateCoherenceCache = () => {
  cached = null;
};

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function coherenceResponseStale(rep: CoherenceResponse | null): boolean {
  if (!rep) return true;
  const k = w.TVE?.coherenceK;
  if (typeof k !== "number" || k < 0) return false;
  const n = rep.npmi?.length ?? 0;
  return n !== k;
}

function topicLabelForRow(i: number, rep: CoherenceResponse): string {
  const tveFn = w.TVE?.coherenceTopicLabel0Based;
  const fromTve = typeof tveFn === "function" ? String(tveFn(i) ?? "").trim() : "";
  const fromApi = rep.labels?.[i] != null ? String(rep.labels[i] ?? "").trim() : "";
  return (fromTve || fromApi || `Topic ${i + 1}`).trim();
}

function fmt(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return v.toFixed(3);
}

async function fetchCoherence(): Promise<CoherenceResponse | null> {
  try {
    const res = await fetch("/coherence", {
      method: "GET",
      credentials: "same-origin",
      headers: { Accept: "application/json" },
    });
    if (!res.ok) {
      console.error("[TopicVisExplorer] /coherence failed:", res.status, await res.text());
      return null;
    }
    return (await res.json()) as CoherenceResponse;
  } catch (err) {
    console.error("[TopicVisExplorer] /coherence threw:", err);
    return null;
  }
}

function renderTable(rep: CoherenceResponse, root: HTMLElement, status: HTMLElement): void {
  const table = root.querySelector<HTMLTableElement>("#TveCoherenceTable");
  const tbody = table?.querySelector("tbody");
  if (!table || !tbody) return;

  // Number of topics is the longest of any of the four columns
  // (in practice all have the same length; defensive).
  const n = Math.max(
    rep.npmi?.length ?? 0,
    rep.c_v?.length ?? 0,
    rep.segregation?.length ?? 0,
    rep.coverage?.length ?? 0,
  );
  if (n === 0) {
    status.textContent = "No topics in this scenario.";
    return;
  }

  const rows: string[] = [];
  for (let i = 0; i < n; i++) {
    const label = topicLabelForRow(i, rep);
    const titleAttr = ` title="${escapeHtml(label)}"`;
    const labelCell = `<td class="tve-coherence-topic-col"${titleAttr}>${escapeHtml(label)}</td>`;
    rows.push(
      `<tr>${labelCell}` +
        `<td>${fmt(rep.npmi?.[i])}</td>` +
        `<td>${fmt(rep.c_v?.[i])}</td>` +
        `<td>${fmt(rep.segregation?.[i])}</td>` +
        `<td>${fmt(rep.coverage?.[i])}</td></tr>`,
    );
  }
  tbody.innerHTML = rows.join("");

  status.hidden = true;
  table.hidden = false;
}

async function ensureLoaded(root: HTMLElement, status: HTMLElement): Promise<void> {
  if (cached && coherenceResponseStale(cached)) {
    cached = null;
  }
  if (cached) {
    renderTable(cached, root, status);
    return;
  }
  if (inflight) return;
  inflight = true;
  status.textContent = "Computing coherence…";
  status.hidden = false;
  try {
    const rep = await fetchCoherence();
    if (rep) {
      cached = rep;
      renderTable(rep, root, status);
    } else {
      status.textContent = "Coherence unavailable for this scenario.";
    }
  } finally {
    inflight = false;
  }
}

function setupCoherencePanel(): void {
  const wrapper = document.getElementById("TveCoherencePanelWrapper");
  const toggle = document.getElementById("TveCoherencePanelToggle");
  const body = document.getElementById("TveCoherencePanelBody");
  const status = document.getElementById("TveCoherencePanelStatus");

  // Multi-corpus mode renders no panel at all (see ``type_vis == 1``
  // guard in index_v1.html). All early-return paths are safe.
  if (!wrapper || !toggle || !body || !status) return;

  toggle.addEventListener("click", () => {
    const isOpen = wrapper.dataset.state === "expanded";
    if (isOpen) {
      wrapper.dataset.state = "collapsed";
      body.hidden = true;
      toggle.setAttribute("aria-expanded", "false");
    } else {
      wrapper.dataset.state = "expanded";
      body.hidden = false;
      toggle.setAttribute("aria-expanded", "true");
      // Lazy-load on first expand.
      void ensureLoaded(wrapper, status);
    }
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", setupCoherencePanel);
} else {
  setupCoherencePanel();
}

export {};
