const DEFAULTS = { on:true, home:true, side:true, end:true, shorts:true, comments:true, nav:true, chrome:true };
const KEYS = Object.keys(DEFAULTS);
chrome.storage.sync.get(DEFAULTS, v => {
  for (const k of KEYS) document.getElementById(k).checked = !!v[k];
  paint(v.on);
});
for (const k of KEYS) {
  document.getElementById(k).addEventListener("change", e => {
    chrome.storage.sync.set({ [k]: e.target.checked });
    if (k === "on") paint(e.target.checked);
  });
}
function paint(on) {
  document.querySelectorAll(".sub").forEach(el => el.classList.toggle("off", !on));
}
