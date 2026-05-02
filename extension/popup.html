// ============================================
// ResumePulse — popup.js
// Controls the extension popup UI
// ============================================

const loggedInView   = document.getElementById("logged-in-view");
const loggedOutView  = document.getElementById("logged-out-view");
const userName       = document.getElementById("user-name");
const statResumes    = document.getElementById("stat-resumes");
const statAts        = document.getElementById("stat-ats");
const pageStatus     = document.getElementById("page-status");
const pageStatusText = document.getElementById("page-status-text");
const visaToggle     = document.getElementById("visa-toggle");
const btnTailor      = document.getElementById("btn-tailor");
const btnDashboard   = document.getElementById("btn-dashboard");
const btnSignup      = document.getElementById("btn-signup");
const btnLogin       = document.getElementById("btn-login");
const btnSettings    = document.getElementById("btn-settings");
const btnLogout      = document.getElementById("btn-logout");
const btnHelp        = document.getElementById("btn-help");

// ── GET TOKEN ────────────────────────────────────────────────────
// Checks Chrome storage first, then injects into active tab
// to read localStorage as fallback

async function getToken() {
  // Try Chrome storage first
  return new Promise(resolve => {
    chrome.storage.local.get(["authToken"], async data => {
      if (data.authToken) {
        resolve(data.authToken);
        return;
      }

      // Fallback: read from active tab's localStorage
      try {
        const [tab] = await chrome.tabs.query({
          active: true, currentWindow: true
        });
        if (tab && tab.id) {
          const results = await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            func:   () => localStorage.getItem("authToken")
          });
          const token = results?.[0]?.result;
          if (token) {
            // Sync to Chrome storage for future use
            chrome.storage.local.set({ authToken: token });
          }
          resolve(token || null);
        } else {
          resolve(null);
        }
      } catch {
        resolve(null);
      }
    });
  });
}

// ── CHECK CURRENT TAB ────────────────────────────────────────────
async function checkCurrentTab() {
  try {
    const [tab] = await chrome.tabs.query({
      active: true, currentWindow: true
    });
    if (!tab || !tab.id) return { isJob: false, hasVisa: false };

    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => {
        const text = document.body?.innerText?.toLowerCase() || "";

        const jobKeywords = [
          "responsibilities", "qualifications", "requirements",
          "we are looking for", "about the role", "job description",
          "what you'll do", "years of experience", "apply now",
          "preferred qualifications", "basic qualifications",
          "duties", "essential functions"
        ];

        const visaKeywords = [
          "no sponsorship", "cannot sponsor", "will not sponsor",
          "us citizenship required", "green card required",
          "security clearance required", "no visa sponsorship"
        ];

        const skipUrls = [
          "google.com", "youtube.com", "facebook.com",
          "reddit.com", "wikipedia.org", "gmail.com"
        ];

        if (skipUrls.some(s => location.href.includes(s)))
          return { isJob: false, hasVisa: false };

        const jobMatches  = jobKeywords.filter(k => text.includes(k));
        const visaMatch   = visaKeywords.find(k => text.includes(k));

        return {
          isJob:    jobMatches.length >= 2,
          hasVisa:  !!visaMatch,
          visaWord: visaMatch || null
        };
      }
    });

    return results?.[0]?.result || { isJob: false, hasVisa: false };
  } catch {
    return { isJob: false, hasVisa: false };
  }
}

// ── UPDATE STATUS BADGE ───────────────────────────────────────────
function updatePageStatus(isJob, hasVisa, visaWord) {
  pageStatus.classList.remove("job-found", "visa-found", "no-job");

  if (hasVisa && visaToggle.checked) {
    pageStatus.classList.add("visa-found");
    pageStatusText.textContent = `Visa restriction: "${visaWord}"`;
    btnTailor.disabled         = false;
    btnTailor.textContent      = "Tailor resume anyway";
  } else if (isJob) {
    pageStatus.classList.add("job-found");
    pageStatusText.textContent = "Job posting detected on this page";
    btnTailor.disabled         = false;
    btnTailor.textContent      = "Tailor resume for this job";
  } else {
    pageStatus.classList.add("no-job");
    pageStatusText.textContent = "No job posting detected";
    btnTailor.disabled         = true;
    btnTailor.textContent      = "Tailor resume for this job";
  }
}

// ── VISA TOGGLE ───────────────────────────────────────────────────
visaToggle.addEventListener("change", () => {
  chrome.storage.sync.set({ visaWarningEnabled: visaToggle.checked });
  checkCurrentTab().then(({ isJob, hasVisa, visaWord }) => {
    updatePageStatus(isJob, hasVisa, visaWord);
  });
});

// ── BUTTONS ───────────────────────────────────────────────────────
btnTailor.addEventListener("click", async () => {
  const [tab] = await chrome.tabs.query({
    active: true, currentWindow: true
  });
  chrome.tabs.sendMessage(tab.id, { action: "TAILOR_RESUME" });
  window.close();
});

btnDashboard.addEventListener("click", () => {
  chrome.tabs.create({ url: "http://127.0.0.1:5500/frontend/dashboard.html" });
});

btnSettings.addEventListener("click", () => {
  chrome.tabs.create({ url: "http://127.0.0.1:5500/frontend/settings.html" });
});

btnSignup.addEventListener("click", () => {
  chrome.tabs.create({ url: "http://127.0.0.1:5500/frontend/register.html" });
});

btnLogin.addEventListener("click", () => {
  chrome.tabs.create({ url: "http://127.0.0.1:5500/frontend/register.html#login" });
});

btnLogout.addEventListener("click", () => {
  chrome.storage.local.remove(["user", "authToken"], () => {
    location.reload();
  });
});

btnHelp.addEventListener("click", () => {
  chrome.tabs.create({ url: "https://github.com/YOUR_USERNAME/resumepulse#readme" });
});

// ── INIT ──────────────────────────────────────────────────────────
async function init() {
  const token = await getToken();

  if (!token) {
    loggedInView.style.display  = "none";
    loggedOutView.style.display = "block";
    return;
  }

  loggedInView.style.display  = "block";
  loggedOutView.style.display = "none";

  // Load user from Chrome storage
  chrome.storage.local.get(["user", "resumeCount", "bestAtsScore"], data => {
    const user = data.user || {};
    userName.textContent = user.first_name || "there";

    statResumes.textContent = data.resumeCount || 0;
    const best = data.bestAtsScore;
    if (best) {
      statAts.textContent = `${best}%`;
      statAts.classList.add(best >= 70 ? "green" : "amber");
    }
  });

  // Load visa toggle
  chrome.storage.sync.get({ visaWarningEnabled: true }, ({ visaWarningEnabled }) => {
    visaToggle.checked = visaWarningEnabled;
  });

  // Check current tab
  const { isJob, hasVisa, visaWord } = await checkCurrentTab();
  updatePageStatus(isJob, hasVisa, visaWord);
}

init();

// ── MESSAGE LISTENER ──────────────────────────────────────────────
chrome.runtime.onMessage.addListener(message => {
  if (message.action === "JOB_DETECTED")  updatePageStatus(true,  false, null);
  if (message.action === "VISA_DETECTED") updatePageStatus(true,  true,  message.keyword);
});