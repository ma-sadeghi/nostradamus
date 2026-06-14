// Predict form UX: per-row autosave with a status indicator, plus the existing
// partial-row nudge. The "Save all" button stays as a no-JS / failure fallback.
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("predict-form");
  if (!form) return;

  const tokenField = form.querySelector("[name=csrfmiddlewaretoken]");
  const csrfToken = tokenField ? tokenField.value : "";
  const statusEl = document.getElementById("save-status");
  const rows = Array.from(form.querySelectorAll("[data-row]"));
  const DEBOUNCE_MS = 700;

  const timers = new WeakMap();
  const lastSaved = new WeakMap(); // row -> "home:away" of the last persisted value
  let inFlight = 0;
  let hadError = false;

  function setStatus(state, html) {
    if (!statusEl) return;
    statusEl.dataset.state = state;
    statusEl.innerHTML = html;
  }

  function scoreFields(row) {
    return Array.from(row.querySelectorAll(".score-input"));
  }

  // Returns true when the row is complete (both scores filled) or empty.
  function markPartial(row) {
    const fields = scoreFields(row);
    if (fields.length !== 2) return true;
    const [home, away] = fields;
    const homeFilled = home.value.trim() !== "";
    const awayFilled = away.value.trim() !== "";
    const partial = homeFilled !== awayFilled;
    home.classList.toggle("needs-pair", partial && !homeFilled);
    away.classList.toggle("needs-pair", partial && !awayFilled);
    return !partial;
  }

  async function saveRow(row) {
    const url = row.dataset.saveUrl;
    if (!url) return; // locked rows have no save URL
    const fields = scoreFields(row);
    if (fields.length !== 2) return;
    const home = fields[0].value.trim();
    const away = fields[1].value.trim();
    const bothEmpty = home === "" && away === "";
    const bothFilled = home !== "" && away !== "";
    // Partial (exactly one filled): wait for the pair before doing anything.
    if (!bothEmpty && !bothFilled) return;
    // bothEmpty means "clear my prediction"; bothFilled means "save it".
    const key = bothEmpty ? "" : `${home}:${away}`;
    if (lastSaved.get(row) === key) return; // nothing changed

    const removing = bothEmpty;
    inFlight += 1;
    setStatus(
      "saving",
      removing
        ? '<i class="fas fa-circle-notch fa-spin"></i> Removing…'
        : '<i class="fas fa-circle-notch fa-spin"></i> Saving…'
    );
    row.classList.add("is-saving");
    try {
      const res = await fetch(url, {
        method: "POST",
        headers: { "X-CSRFToken": csrfToken, "X-Requested-With": "fetch" },
        body: new URLSearchParams({ home_score: home, away_score: away }),
      });
      if (!res.ok) throw new Error(String(res.status));
      lastSaved.set(row, key);
      row.classList.remove("is-saving", "is-error");
      row.classList.add("is-saved");
      setTimeout(() => row.classList.remove("is-saved"), 1500);
    } catch (err) {
      hadError = true;
      row.classList.remove("is-saving");
      row.classList.add("is-error");
      setStatus(
        "error",
        '<i class="fas fa-triangle-exclamation"></i> Couldn\'t save — tap “Save all”.'
      );
    } finally {
      inFlight -= 1;
      if (inFlight === 0 && !hadError) {
        setStatus("saved", '<i class="fas fa-check"></i> All changes saved');
      }
    }
  }

  rows.forEach((row) => {
    const fields = scoreFields(row);
    if (fields.length === 2) {
      const home = fields[0].value.trim();
      const away = fields[1].value.trim();
      // "" marks an unset row, so clearing it again is a no-op while clearing a
      // saved bet ("h:a" -> "") still fires a delete.
      lastSaved.set(row, home !== "" && away !== "" ? `${home}:${away}` : "");
    }
    fields.forEach((input) => {
      input.addEventListener("input", () => {
        markPartial(row);
        clearTimeout(timers.get(row));
        timers.set(row, setTimeout(() => saveRow(row), DEBOUNCE_MS));
      });
      input.addEventListener("blur", () => {
        clearTimeout(timers.get(row));
        saveRow(row);
      });
    });
  });

  // Fallback "Save all": validate partial rows, then let the form POST normally.
  form.addEventListener("submit", (event) => {
    let firstIncomplete = null;
    rows.forEach((row) => {
      if (!markPartial(row) && !firstIncomplete) firstIncomplete = row;
    });
    if (firstIncomplete) {
      event.preventDefault();
      firstIncomplete.scrollIntoView({ behavior: "smooth", block: "center" });
      const empty = firstIncomplete.querySelector(".score-input.needs-pair");
      if (empty) empty.focus({ preventScroll: true });
    }
  });

  // --- Jump to today's matches + floating navigation bubbles -----------------
  function localToday() {
    const d = new Date();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${d.getFullYear()}-${m}-${day}`;
  }

  function todayRound() {
    const rounds = Array.from(document.querySelectorAll(".round[data-date]"));
    if (!rounds.length) return null;
    const today = localToday();
    // Exact match, else the next upcoming day, else the last day played.
    return (
      rounds.find((r) => r.dataset.date === today) ||
      rounds.find((r) => r.dataset.date >= today) ||
      rounds[rounds.length - 1]
    );
  }

  function jumpToToday(smooth) {
    const el = todayRound();
    if (el) el.scrollIntoView({ behavior: smooth ? "smooth" : "auto", block: "start" });
  }

  const fabToday = document.getElementById("fab-today");
  const fabTop = document.getElementById("fab-top");
  if (fabToday) fabToday.addEventListener("click", () => jumpToToday(true));
  if (fabTop) {
    fabTop.addEventListener("click", () =>
      window.scrollTo({ top: 0, behavior: "smooth" })
    );
    const toggleTop = () => fabTop.classList.toggle("fab--hidden", window.scrollY < 400);
    window.addEventListener("scroll", toggleTop, { passive: true });
    toggleTop();
  }

  // Land on today's matches when the page opens — but never yank a user who has
  // already started scrolling (e.g. while fonts were still loading).
  let userScrolled = false;
  ["wheel", "touchmove", "keydown"].forEach((ev) =>
    window.addEventListener(ev, () => { userScrolled = true; }, { passive: true, once: true })
  );
  jumpToToday(false);
  window.addEventListener("load", () => {
    if (!userScrolled) jumpToToday(false);
  });
});
