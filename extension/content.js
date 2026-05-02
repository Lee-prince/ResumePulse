// ============================================
// ResumePulse — content.js
// COMPLETE FINAL VERSION
// Job detection + warnings + AI resume + side panel
// ============================================


// ── SAFETY GUARD ──────────────────────────────────────────────────
function isChromeContextValid() {
  try { return !!chrome?.runtime?.id; } catch { return false; }
}
if (!isChromeContextValid()) {
  throw new Error("ResumePulse: Extension context gone.");
}


// ── KEYWORD LISTS ─────────────────────────────────────────────────

const JOB_KEYWORDS = [
  "responsibilities", "qualifications", "requirements",
  "we are looking for", "about the role", "job description",
  "what you'll do", "what we're looking for", "years of experience",
  "apply now", "about the position", "who you are",
  "nice to have", "preferred qualifications", "basic qualifications",
  "duties", "essential functions", "job purpose", "job summary",
  "minimum qualifications", "we offer", "what you will do",
  "key responsibilities", "your responsibilities", "your role",
  "about the job", "position summary", "role overview",
  "you will be responsible", "what we expect"
];

const VISA_KEYWORDS = [
  "no sponsorship", "not able to sponsor", "cannot sponsor",
  "will not sponsor", "sponsorship not available",
  "does not sponsor", "unable to sponsor",
  "must be a us citizen", "must be a u.s. citizen",
  "united states citizen only", "us citizenship required",
  "u.s. citizenship required", "green card required",
  "permanent resident only", "must hold a green card",
  "security clearance required", "secret clearance",
  "top secret", "ts/sci", "active clearance required",
  "no visa sponsorship", "visa sponsorship is not available",
  "not eligible for sponsorship", "only considering us citizens",
];

const EXPERIENCE_PATTERNS = [
  /(\d+)\+?\s*years?\s*of\s*experience/gi,
  /(\d+)\+?\s*years?\s*experience/gi,
  /minimum\s*(?:of\s*)?(\d+)\s*years?/gi,
  /at\s*least\s*(\d+)\s*years?/gi,
  /(\d+)\s*to\s*\d+\s*years?\s*of\s*experience/gi,
  /experience\s*of\s*(\d+)\+?\s*years?/gi,
  /(\d+)\+\s*years?\s*(?:of\s*)?(?:relevant|related|professional)/gi
];


// ── HELPERS ───────────────────────────────────────────────────────

function getPageText() {
  return document.body.innerText.toLowerCase();
}

function isJobPage(pageText) {
  const skipUrls = [
    "google.com/search", "youtube.com", "facebook.com",
    "twitter.com", "instagram.com", "reddit.com",
    "wikipedia.org", "amazon.com", "netflix.com",
    "gmail.com", "outlook.com"
  ];
  if (skipUrls.some(s => location.href.toLowerCase().includes(s))) return false;
  const matches = JOB_KEYWORDS.filter(k => pageText.includes(k));
  return matches.length >= 2;
}

function getVisaMatch(pageText) {
  return VISA_KEYWORDS.find(k => pageText.includes(k));
}

function extractRequiredExperience(pageText) {
  for (const pattern of EXPERIENCE_PATTERNS) {
    const match = pageText.match(pattern);
    if (match) {
      const numMatch = match[0].match(/(\d+)/);
      if (numMatch) return parseInt(numMatch[1]);
    }
  }
  return null;
}

function getUserSettings() {
  return new Promise(resolve => {
    const defaults = {
      visaWarningEnabled:       true,
      experienceWarningEnabled: true,
      yearsOfExperience:        0
    };
    if (!isChromeContextValid()) { resolve(defaults); return; }
    chrome.storage.sync.get(defaults, resolve);
  });
}

async function getAuthToken() {
  try {
    return new Promise(resolve => {
      chrome.storage.local.get(["authToken"], d => resolve(d.authToken || null));
    });
  } catch {
    return localStorage.getItem("authToken");
  }
}


// ── HIGHLIGHTING ──────────────────────────────────────────────────

const HIGHLIGHT_VISA = "acn-highlight-visa";
const HIGHLIGHT_EXP  = "acn-highlight-exp";

function highlightText(keywords, cls) {
  removeHighlights(cls);
  if (!keywords || !keywords.length) return;
  const escaped = keywords.map(k => k.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  const regex   = new RegExp(`(${escaped.join("|")})`, "gi");
  const walker  = document.createTreeWalker(
    document.body, NodeFilter.SHOW_TEXT,
    {
      acceptNode(node) {
        const p   = node.parentElement;
        if (!p) return NodeFilter.FILTER_REJECT;
        const tag = p.tagName?.toLowerCase();
        if (
          tag === "script" || tag === "style" || tag === "noscript" ||
          p.id === "acn-banner" || p.closest?.("#acn-banner") ||
          p.id === "acn-side-panel" || p.closest?.("#acn-side-panel")
        ) return NodeFilter.FILTER_REJECT;
        regex.lastIndex = 0;
        if (regex.test(node.textContent)) { regex.lastIndex = 0; return NodeFilter.FILTER_ACCEPT; }
        regex.lastIndex = 0;
        return NodeFilter.FILTER_SKIP;
      }
    }
  );
  const nodes = [];
  let node;
  while ((node = walker.nextNode())) nodes.push(node);
  nodes.forEach(textNode => {
    const parent = textNode.parentNode;
    if (!parent) return;
    const frag = document.createDocumentFragment();
    let last = 0;
    const text = textNode.textContent;
    regex.lastIndex = 0;
    let m;
    while ((m = regex.exec(text)) !== null) {
      if (m.index > last) frag.appendChild(document.createTextNode(text.slice(last, m.index)));
      const mark = document.createElement("mark");
      mark.className   = `acn-highlight ${cls}`;
      mark.textContent = m[0];
      frag.appendChild(mark);
      last = regex.lastIndex;
    }
    if (last < text.length) frag.appendChild(document.createTextNode(text.slice(last)));
    parent.replaceChild(frag, textNode);
  });
}

function removeHighlights(cls) {
  document.querySelectorAll(`.${cls}`).forEach(el => {
    const p = el.parentNode;
    if (p) { p.replaceChild(document.createTextNode(el.textContent), el); p.normalize(); }
  });
}

function removeAllHighlights() {
  removeHighlights(HIGHLIGHT_VISA);
  removeHighlights(HIGHLIGHT_EXP);
}

function scrollToFirst(cls) {
  const el = document.querySelector(`.${cls}`);
  if (el) setTimeout(() => el.scrollIntoView({ behavior: "smooth", block: "center" }), 600);
}


// ── BANNER REMOVE ─────────────────────────────────────────────────

function removeBanner() {
  const b = document.getElementById("acn-banner");
  if (b) b.remove();
  document.body.classList.remove("acn-active");
}


// ── JOB BANNER ────────────────────────────────────────────────────

function showJobBanner() {
  removeBanner();
  removeAllHighlights();
  const banner     = document.createElement("div");
  banner.id        = "acn-banner";
  banner.className = "job-banner";
  banner.innerHTML = `
    <div id="acn-banner-content">
      <div id="acn-banner-text">
        <div class="acn-icon">✦</div>
        <span><strong>Job detected!</strong> Want an ATS-optimized resume tailored for this role?</span>
      </div>
      <div id="acn-buttons">
        <button class="acn-btn-primary" id="acn-yes">Tailor my resume</button>
        <button class="acn-btn-secondary" id="acn-later">Not now</button>
      </div>
      <button id="acn-close">✕</button>
    </div>`;
  document.body.prepend(banner);
  document.body.classList.add("acn-active");
  document.getElementById("acn-yes").addEventListener("click", handleTailorResume);
  document.getElementById("acn-later").addEventListener("click", removeBanner);
  document.getElementById("acn-close").addEventListener("click", removeBanner);
}


// ── VISA BANNER ───────────────────────────────────────────────────

function showVisaBanner(matchedKeyword) {
  removeBanner();
  highlightText(VISA_KEYWORDS, HIGHLIGHT_VISA);
  scrollToFirst(HIGHLIGHT_VISA);
  const banner     = document.createElement("div");
  banner.id        = "acn-banner";
  banner.className = "visa-banner";
  banner.innerHTML = `
    <div id="acn-banner-content">
      <div id="acn-banner-text">
        <div class="acn-icon">⚠</div>
        <span>
          <strong>Visa restriction detected!</strong>
          Keyword highlighted in red — <em>"${matchedKeyword}"</em> — you may not be eligible.
        </span>
      </div>
      <div id="acn-buttons">
        <button class="acn-btn-primary" id="acn-apply-anyway">Apply anyway</button>
        <button class="acn-btn-secondary" id="acn-skip">Skip this job</button>
      </div>
      <button id="acn-close">✕</button>
    </div>`;
  document.body.prepend(banner);
  document.body.classList.add("acn-active");
  document.getElementById("acn-apply-anyway").addEventListener("click", () => {
    removeHighlights(HIGHLIGHT_VISA); showJobBanner();
  });
  document.getElementById("acn-skip").addEventListener("click", () => {
    removeBanner(); removeAllHighlights();
  });
  document.getElementById("acn-close").addEventListener("click", () => {
    removeBanner(); removeAllHighlights();
  });
}


// ── EXPERIENCE BANNER ─────────────────────────────────────────────

function showExperienceBanner(requiredYears, userYears) {
  removeBanner();
  const pageText  = document.body.innerText;
  const foundExps = [];
  EXPERIENCE_PATTERNS.forEach(p => {
    p.lastIndex = 0;
    const m = pageText.match(p);
    if (m) foundExps.push(...m);
  });
  if (foundExps.length) { highlightText(foundExps, HIGHLIGHT_EXP); scrollToFirst(HIGHLIGHT_EXP); }
  const banner     = document.createElement("div");
  banner.id        = "acn-banner";
  banner.className = "experience-banner";
  banner.innerHTML = `
    <div id="acn-banner-content">
      <div id="acn-banner-text">
        <div class="acn-icon">⚡</div>
        <span>
          <strong>Experience gap!</strong>
          Role requires <strong>${requiredYears} years</strong>,
          your profile shows <strong>${userYears} years</strong>.
          Requirements highlighted in yellow below.
        </span>
      </div>
      <div id="acn-buttons">
        <button class="acn-btn-primary" id="acn-apply-exp">Tailor anyway</button>
        <button class="acn-btn-secondary" id="acn-skip-exp">Skip this job</button>
      </div>
      <button id="acn-close">✕</button>
    </div>`;
  document.body.prepend(banner);
  document.body.classList.add("acn-active");
  document.getElementById("acn-apply-exp").addEventListener("click", () => {
    removeHighlights(HIGHLIGHT_EXP); showJobBanner();
  });
  document.getElementById("acn-skip-exp").addEventListener("click", () => {
    removeBanner(); removeAllHighlights();
  });
  document.getElementById("acn-close").addEventListener("click", () => {
    removeBanner(); removeAllHighlights();
  });
}


// ── LOADING BANNER ────────────────────────────────────────────────

function showLoadingBanner() {
  removeBanner();
  removeSidePanel();
  const banner     = document.createElement("div");
  banner.id        = "acn-banner";
  banner.className = "loading-banner";
  banner.innerHTML = `
    <div id="acn-banner-content">
      <div id="acn-banner-text">
        <div class="acn-loading-dots"><span>.</span><span>.</span><span>.</span></div>
        <span><strong>Generating your ATS resume</strong> — tailoring to this job, about 10 seconds</span>
      </div>
    </div>`;
  document.body.prepend(banner);
  document.body.classList.add("acn-active");
}


// ── SUCCESS BANNER ────────────────────────────────────────────────

function showSuccessBanner(downloadUrl, atsScore, improvements, suggestions) {
  removeBanner();
  removeSidePanel();

  const scoreColor =
    atsScore >= 80 ? "#1D9E75" :
    atsScore >= 60 ? "#EF9F27" : "#E24B4A";

  const scoreLabel =
    atsScore >= 80 ? "Excellent Match ✓" :
    atsScore >= 60 ? "Good Match"        : "Moderate Match";

  const banner     = document.createElement("div");
  banner.id        = "acn-banner";
  banner.className = "success-banner";
  banner.innerHTML = `
    <div id="acn-banner-content">
      <div id="acn-banner-text">
        <div class="acn-icon">✓</div>
        <span>
          <strong>Resume ready!</strong>
          ATS Score: <strong style="color:${scoreColor}">${atsScore}%</strong>
          — <span style="color:${scoreColor}">${scoreLabel}</span>
        </span>
      </div>
      <div id="acn-buttons">
        <button class="acn-btn-primary" id="acn-view-report">📊 View Full Report</button>
        <button class="acn-btn-secondary" id="acn-download-top">⬇ Download PDF</button>
      </div>
      <button id="acn-close">✕</button>
    </div>`;

  document.body.prepend(banner);
  document.body.classList.add("acn-active");

  document.getElementById("acn-close").addEventListener("click", () => {
    removeBanner(); removeSidePanel();
  });
  document.getElementById("acn-download-top").addEventListener("click", () => {
    downloadPDF(downloadUrl);
  });
  document.getElementById("acn-view-report").addEventListener("click", () => {
    showSidePanel(downloadUrl, atsScore, scoreColor, scoreLabel, improvements, suggestions);
  });

  // Auto open side panel
  showSidePanel(downloadUrl, atsScore, scoreColor, scoreLabel, improvements, suggestions);
}


// ── SIDE PANEL ────────────────────────────────────────────────────

function removeSidePanel() {
  const p = document.getElementById("acn-side-panel");
  if (p) p.remove();
}

function showSidePanel(downloadUrl, atsScore, scoreColor, scoreLabel, improvements, suggestions) {
  removeSidePanel();

  const improvHTML = (improvements || []).map(i => `
    <div class="acn-improvement-item">
      <span class="acn-improvement-icon">✓</span>
      <span>${i}</span>
    </div>`).join("");

  const suggHTML = (suggestions || []).map(s => `
    <div class="acn-suggestion-item">💡 ${s}</div>`
  ).join("");

  const panel = document.createElement("div");
  panel.id    = "acn-side-panel";
  panel.innerHTML = `
    <div id="acn-panel-header">
      <h3>📊 ATS Report</h3>
      <button id="acn-panel-close">✕</button>
    </div>
    <div id="acn-panel-body">
      <div class="acn-score-ring">
        <div class="acn-score-circle" style="background:${scoreColor};">
          <span class="score-num">${atsScore}%</span>
          <span class="score-label-sm">ATS Score</span>
        </div>
        <div class="acn-score-label" style="color:${scoreColor};">${scoreLabel}</div>
        <div class="acn-score-sub">Resume optimized for this specific role</div>
      </div>
      ${improvHTML ? `
        <div class="acn-panel-section">
          <div class="acn-panel-section-title">✅ Improvements Made</div>
          ${improvHTML}
        </div>` : ""}
      ${suggHTML ? `
        <div class="acn-panel-section">
          <div class="acn-panel-section-title">💡 Further Suggestions</div>
          ${suggHTML}
        </div>` : ""}
    </div>
    <div id="acn-panel-footer">
      <button class="acn-download-btn" id="acn-panel-download">⬇ Download PDF Resume</button>
      <button class="acn-view-dashboard-btn" id="acn-panel-dashboard">View My Dashboard</button>
    </div>`;

  document.body.appendChild(panel);
  setTimeout(() => panel.classList.add("open"), 10);

  document.getElementById("acn-panel-close").addEventListener("click", removeSidePanel);
  document.getElementById("acn-panel-download").addEventListener("click", () => downloadPDF(downloadUrl));
  document.getElementById("acn-panel-dashboard").addEventListener("click", () => {
    window.open("http://127.0.0.1:5500/frontend/dashboard.html", "_blank");
  });
}


// ── PDF DOWNLOAD (no page redirect) ──────────────────────────────

function downloadPDF(url) {
  const a    = document.createElement("a");
  a.href     = url;
  a.target   = "_blank";
  a.download = "";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}


// ── TAILOR RESUME ─────────────────────────────────────────────────

async function handleTailorResume() {
  showLoadingBanner();

  const jobDescription = document.body.innerText;
  let jobTitle = "";
  let company  = "";
  const jobUrl = window.location.href;

  const titleEl   = document.querySelector(
    ".job-details-jobs-unified-top-card__job-title, h1.t-24, h1"
  );
  const companyEl = document.querySelector(
    ".job-details-jobs-unified-top-card__company-name, .jobs-unified-top-card__company-name"
  );
  if (titleEl)   jobTitle = titleEl.innerText.trim().split('\n')[0];
  if (companyEl) company  = companyEl.innerText.trim().split('\n')[0];

  const token = await getAuthToken();

  if (!token) {
    removeBanner();
    alert("Please log in to ResumePulse first!\nVisit: http://127.0.0.1:5500/frontend/register.html");
    return;
  }

  try {
    const response = await fetch("http://localhost:8000/resume/tailor", {
      method:  "POST",
      headers: {
        "Content-Type":  "application/json",
        "Authorization": `Bearer ${token}`
      },
      body: JSON.stringify({
        job_description: jobDescription,
        job_title:       jobTitle,
        company:         company,
        job_url:         jobUrl,
      })
    });

    const data = await response.json();

    if (response.ok) {
      try {
        chrome.storage.local.get(["resumeCount", "bestAtsScore"], stored => {
          const count = (stored.resumeCount || 0) + 1;
          const best  = Math.max(stored.bestAtsScore || 0, data.ats_score);
          chrome.storage.local.set({ resumeCount: count, bestAtsScore: best });
        });
      } catch { /* ok */ }

      const downloadUrl = `${data.pdf_url}?token=${encodeURIComponent(token)}`;

      showSuccessBanner(
        downloadUrl,
        data.ats_score,
        data.improvements_made || [],
        data.suggestions       || []
      );

    } else {
      removeBanner();
      const msg = data.detail || "Failed to generate resume.";
      if (msg.includes("base resume")) {
        alert("Please upload your resume first!\nVisit: http://127.0.0.1:5500/frontend/settings.html");
      } else {
        alert(`Error: ${msg}`);
      }
    }

  } catch (err) {
    removeBanner();
    alert("Cannot connect to backend. Make sure it is running on localhost:8000");
    console.error("ResumePulse Error:", err);
  }
}


// ── MAIN INIT ─────────────────────────────────────────────────────

async function init() {
  if (!isChromeContextValid()) return;
  await new Promise(resolve => setTimeout(resolve, 800));
  if (!isChromeContextValid()) return;

  const pageText      = getPageText();
  if (!isJobPage(pageText)) return;

  const settings      = await getUserSettings();
  const visaMatch     = getVisaMatch(pageText);
  const requiredYears = extractRequiredExperience(pageText);
  const userYears     = settings.yearsOfExperience || 0;

  if (visaMatch && settings.visaWarningEnabled) {
    showVisaBanner(visaMatch);
  } else if (
    requiredYears !== null &&
    userYears > 0 &&
    requiredYears > userYears &&
    settings.experienceWarningEnabled !== false
  ) {
    showExperienceBanner(requiredYears, userYears);
  } else {
    showJobBanner();
  }
}


// ── URL POLLING ───────────────────────────────────────────────────

let lastUrl     = location.href;
let initRunning = false;

async function runInit() {
  if (initRunning) return;
  if (!isChromeContextValid()) return;
  initRunning = true;
  removeBanner();
  removeSidePanel();
  removeAllHighlights();
  await init();
  initRunning = false;
}

setInterval(() => {
  if (!isChromeContextValid()) return;
  const cur = location.href;
  if (cur !== lastUrl) { lastUrl = cur; runInit(); }
}, 500);

window.addEventListener("load", runInit);


// ── MESSAGE LISTENER ──────────────────────────────────────────────

chrome.runtime.onMessage.addListener(message => {
  if (!isChromeContextValid()) return;
  if (message.action === "TAILOR_RESUME") handleTailorResume();
});