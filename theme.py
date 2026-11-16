from fasthtml.common import *

TAILWIND_CDN = Script(src="https://cdn.tailwindcss.com")

TAILWIND_CONFIG = Script("""
tailwind.config = {
  theme: {
    extend: {
      colors: {
        dark: '#080c14',
        card: '#0f172a',
        surface: '#1e293b',
        primary: '#2563eb',
        'primary-hover': '#1d4ed8',
        cyan: '#06b6d4',
        amber: '#f59e0b',
        border: 'rgba(255, 255, 255, 0.08)',
        text: '#f8fafc',
        secondary: '#94a3b8',
        muted: '#64748b',
      },
      fontFamily: {
        sans: ['Montserrat', 'Segoe UI', 'system-ui', '-apple-system', 'sans-serif'],
        heading: ['Montserrat', 'Segoe UI', 'sans-serif'],
        display: ['Impact', 'Montserrat', 'Segoe UI', 'sans-serif'],
        mono: ['JetBrains Mono', 'Consolas', 'monospace'],
      },
      borderRadius: {
        card: '16px',
        sheet: '24px',
        modal: '24px',
      },
      animation: {
        'fade-in': 'fadeIn 0.25s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        'slide-down': 'slideDown 0.25s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        'pulse-subtle': 'pulseSubtle 2s infinite ease-in-out',
        'spin-fast': 'spin 0.65s linear infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(6px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideDown: {
          '0%': { opacity: '0', transform: 'translateY(-8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        pulseSubtle: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.6' },
        }
      }
    }
  }
}
""")

GOOGLE_FONTS = Link(rel="preconnect", href="https://fonts.googleapis.com")
GOOGLE_FONTS2 = Link(rel="preconnect", href="https://fonts.gstatic.com", crossorigin="")
GOOGLE_FONTS_LINK = Link(
    href="https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,400&family=JetBrains+Mono:wght@400;500;700&display=swap",
    rel="stylesheet"
)

MATERIAL_ICONS = Link(
    href="https://fonts.googleapis.com/icon?family=Material+Symbols+Outlined",
    rel="stylesheet"
)

STYLE = Style('''
*, ::before, ::after {
  transition-property: color, background-color, border-color, opacity, box-shadow, transform;
  transition-timing-function: cubic-bezier(0.16, 1, 0.3, 1);
  transition-duration: 180ms;
}

/* Professional Multinational Enterprise Ambient Canvas */
body {
  background-color: #080c14;
  background-image: 
    radial-gradient(circle at 12% 8%, rgba(37, 99, 235, 0.08) 0%, transparent 45%),
    radial-gradient(circle at 88% 12%, rgba(6, 182, 212, 0.06) 0%, transparent 45%),
    radial-gradient(circle at 50% 90%, rgba(15, 23, 42, 0.85) 0%, transparent 100%),
    linear-gradient(180deg, #080c14 0%, #0a0f1d 50%, #070a12 100%);
  background-attachment: fixed;
  color: #f8fafc;
  font-family: 'Montserrat', 'Segoe UI', system-ui, -apple-system, sans-serif;
  margin: 0;
  -webkit-font-smoothing: antialiased;
}

/* Page Mount Animation */
main {
  animation: pageEnter 0.28s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

@keyframes pageEnter {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}

h1, h2, h3, h4, .font-heading {
  font-family: 'Montserrat', 'Segoe UI', sans-serif;
  letter-spacing: -0.015em;
  color: #f8fafc;
}

.impact-text {
  font-family: 'Impact', 'Montserrat', 'Segoe UI', sans-serif;
  letter-spacing: 0.04em;
}

/* Glassmorphism MNC Enterprise Cards */
.card {
  background: rgba(15, 23, 42, 0.72);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.07);
  box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.4), inset 0 1px 0 0 rgba(255, 255, 255, 0.06);
  border-radius: 16px;
  transition: transform 0.22s cubic-bezier(0.16, 1, 0.3, 1),
              box-shadow 0.22s cubic-bezier(0.16, 1, 0.3, 1),
              border-color 0.22s cubic-bezier(0.16, 1, 0.3, 1),
              background-color 0.22s cubic-bezier(0.16, 1, 0.3, 1);
}

.card:hover {
  background: rgba(20, 30, 56, 0.8);
  border-color: rgba(37, 99, 235, 0.35);
  transform: translateY(-2px);
  box-shadow: 0 14px 34px -8px rgba(0, 0, 0, 0.6), 0 0 22px rgba(37, 99, 235, 0.12), inset 0 1px 0 0 rgba(255, 255, 255, 0.12);
}

/* Executive Form Inputs */
.input {
  background: #0b1120;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  padding: .65rem .85rem;
  color: #f8fafc;
  font-family: 'Montserrat', 'Segoe UI', sans-serif;
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.3);
  transition: all 0.18s cubic-bezier(0.16, 1, 0.3, 1);
}

.input:focus {
  outline: none;
  background: #0e1629;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.25), inset 0 1px 2px rgba(0, 0, 0, 0.3);
  transform: translateY(-1px);
}

a {
  color: inherit;
  text-decoration: none;
}

/* Button Active Press Micro-Interaction */
button:active:not(:disabled), .btn:active:not(:disabled) {
  transform: scale(0.985);
}

/* Modals and sticky cards stay stable on hover */
.sticky.card:hover, [id*="-modal"] .card:hover, .no-lift:hover {
  transform: none !important;
}

/* Global Top Progress Loading Bar (Linear/Stripe style) */
#global-progress-bar {
  position: fixed;
  top: 0;
  left: 0;
  height: 2.5px;
  width: 0%;
  background: linear-gradient(90deg, #2563eb, #06b6d4, #6366f1);
  box-shadow: 0 0 10px rgba(37, 99, 235, 0.8), 0 0 5px rgba(6, 182, 212, 0.6);
  z-index: 99999;
  transition: width 0.28s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.2s ease;
  opacity: 0;
  pointer-events: none;
}

/* Loading Spinner Utility */
.spinner-ring {
  display: inline-block;
  width: 1rem;
  height: 1rem;
  border: 2px solid rgba(255, 255, 255, 0.25);
  border-top-color: #ffffff;
  border-radius: 9999px;
  animation: spin 0.65s linear infinite;
  vertical-align: middle;
  flex-shrink: 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Form Submit Loading Indicator State */
.btn-submitting {
  opacity: 0.85 !important;
  pointer-events: none !important;
  cursor: wait !important;
}

/* HTMX Smooth Transition Classes */
.htmx-swapping {
  opacity: 0;
  transform: translateY(4px);
  transition: opacity 160ms cubic-bezier(0.16, 1, 0.3, 1), transform 160ms cubic-bezier(0.16, 1, 0.3, 1);
}

.htmx-settling {
  opacity: 1;
  transform: translateY(0);
  transition: opacity 160ms cubic-bezier(0.16, 1, 0.3, 1), transform 160ms cubic-bezier(0.16, 1, 0.3, 1);
}

.htmx-indicator {
  display: inline-block;
  opacity: 0;
  transition: opacity 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  pointer-events: none;
}

.htmx-request .htmx-indicator,
.htmx-request.htmx-indicator {
  opacity: 1;
  pointer-events: auto;
}
''')

# Client-Side Top Progress Bar, Section Loader, and Button Loading Script
GLOBAL_SCRIPT = Script('''
document.addEventListener("DOMContentLoaded", function() {
  // Ensure progress bar exists in DOM
  var bar = document.getElementById("global-progress-bar");
  if (!bar) {
    bar = document.createElement("div");
    bar.id = "global-progress-bar";
    document.body.prepend(bar);
  }

  function startProgress() {
    bar.style.opacity = "1";
    bar.style.width = "35%";
    setTimeout(function() {
      if (bar.style.opacity === "1") bar.style.width = "80%";
    }, 120);
  }

  function finishProgress() {
    bar.style.width = "100%";
    setTimeout(function() {
      bar.style.opacity = "0";
      setTimeout(function() { bar.style.width = "0%"; }, 220);
    }, 180);
    hideSectionLoader();
  }

  function hideSectionLoader() {
    var overlay = document.getElementById("section-loading-overlay");
    if (overlay) {
      overlay.classList.remove("opacity-100");
      overlay.classList.add("opacity-0", "pointer-events-none");
    }
    document.querySelectorAll(".nav-spinner").forEach(function(s) {
      s.classList.add("hidden");
    });
  }

  // Clear loaders on initial DOM mount
  hideSectionLoader();

  // Instant prefetch on link hover
  var prefetchedUrls = new Set();
  document.addEventListener("mouseover", function(e) {
    var a = e.target.closest("a");
    if (!a || !a.href || a.origin !== window.location.origin) return;
    var url = a.href;
    if (prefetchedUrls.has(url)) return;
    if (url.includes("/logout") || url.includes("delete") || url.includes("/reset")) return;
    prefetchedUrls.add(url);
    var prefetchLink = document.createElement("link");
    prefetchLink.rel = "prefetch";
    prefetchLink.href = url;
    document.head.appendChild(prefetchLink);
  });

  // HTMX Lifecycle Events
  document.body.addEventListener("htmx:configRequest", function() {
    startProgress();
  });
  document.body.addEventListener("htmx:afterOnLoad", function() {
    finishProgress();
  });
  document.body.addEventListener("htmx:responseError", function() {
    finishProgress();
  });

  // Link Clicks (Native page navigation)
  document.addEventListener("click", function(e) {
    var a = e.target.closest("a");
    if (a && a.href && !a.href.startsWith("javascript:") && !a.hasAttribute("download") && a.target !== "_blank" && a.origin === window.location.origin) {
      var hrefAttr = a.getAttribute("href");
      if (hrefAttr && hrefAttr.startsWith("#")) return;
      startProgress();

      // Show section loading overlay
      var navLabel = a.getAttribute("data-nav") || a.innerText.trim();
      var overlay = document.getElementById("section-loading-overlay");
      var loaderText = document.getElementById("section-loading-text");
      if (overlay && loaderText) {
        if (navLabel && navLabel.length < 30) {
          loaderText.textContent = "Loading " + navLabel + "...";
        } else {
          loaderText.textContent = "Loading Section...";
        }
        overlay.classList.remove("opacity-0", "pointer-events-none");
        overlay.classList.add("opacity-100");
      }

      // Show spinner on the clicked nav link
      var spinner = a.querySelector(".nav-spinner");
      if (spinner) {
        spinner.classList.remove("hidden");
      }
    }
  });

  // Before unload: show progress on navigation
  window.addEventListener("beforeunload", function() {
    startProgress();
  });

  // Pageshow (Reset on browser back/forward cache navigation)
  window.addEventListener("pageshow", function(e) {
    finishProgress();
    hideSectionLoader();
    document.querySelectorAll(".btn-submitting").forEach(function(b) {
      b.classList.remove("btn-submitting");
      var sp = b.querySelector(".spinner-ring");
      if (sp) sp.remove();
    });
  });

  // Form Submissions: Attach Loading State & Button Spinner
  document.addEventListener("submit", function(e) {
    var form = e.target;
    // If browser HTML5 validation fails, abort loading state
    if (form.checkValidity && !form.checkValidity()) {
      return;
    }
    var btn = form.querySelector('button[type="submit"], input[type="submit"]');
    if (btn && !btn.hasAttribute("data-no-loading") && !btn.classList.contains("btn-submitting")) {
      startProgress();
      btn.classList.add("btn-submitting");
      
      // Check if button already has a spinner
      if (!btn.querySelector(".spinner-ring")) {
        var sp = document.createElement("span");
        sp.className = "spinner-ring mr-2";
        btn.prepend(sp);
      }
      
      // Update loading text if data-loading is provided
      var loadingText = btn.getAttribute("data-loading");
      if (loadingText) {
        var labelSpan = btn.querySelector(".btn-label");
        if (labelSpan) {
          labelSpan.textContent = loadingText;
        } else {
          // If no specific span, keep spinner and update text
          btn.childNodes.forEach(function(node) {
            if (node.nodeType === Node.TEXT_NODE && node.textContent.trim()) {
              node.textContent = " " + loadingText;
            }
          });
        }
      }
    }
  });
});
''')

HEAD_EXTRA = [
    Meta(name="theme-color", content="#080c14"),
    Link(rel="icon", href="/favicon.ico"),
    Link(rel="apple-touch-icon", href="/favicon-192.png")
]

hdrs = [
    STYLE,
    GLOBAL_SCRIPT,
    *HEAD_EXTRA,
    TAILWIND_CDN,
    TAILWIND_CONFIG,
    GOOGLE_FONTS,
    GOOGLE_FONTS2,
    GOOGLE_FONTS_LINK,
    MATERIAL_ICONS
]
