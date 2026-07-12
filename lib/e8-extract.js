// The canonical E8 capture: evaluate this in any browser driver (Playwright/CDP),
// save the result as JSON, feed two captures to lib/e8-dom.py. Shipping ONE script
// is the point — a diff must never come from asking the two pages different
// questions. Lane docs: docs/10 §10. Widen PROPS when a real loop needs more.
() => {
  const PROPS = [
    "color", "background-color", "border-color", "border-radius", "border-width",
    "font-size", "font-weight", "font-family", "line-height", "letter-spacing",
    "padding", "margin", "gap", "opacity", "box-shadow", "text-align",
  ];
  const els = [...document.querySelectorAll("[id], [data-e8]")];
  return {
    url: location.href,
    viewport: [window.innerWidth, window.innerHeight],
    // coverage honesty: only MARKED elements are captured, so the diff tool can
    // report what it never looked at instead of appearing complete
    dom_elements: document.body.querySelectorAll("*").length,
    elements: els.map((el) => {
      const cs = getComputedStyle(el);
      const styles = {};
      for (const p of PROPS) styles[p] = cs.getPropertyValue(p);
      const r = el.getBoundingClientRect();
      return {
        selector: el.id ? `#${el.id}` : `[data-e8="${el.dataset.e8}"]`,
        box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        styles,
      };
    }),
  };
};
