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
        'fade-in': 'fadeIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        'slide-down': 'slideDown 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideDown: {
          '0%': { opacity: '0', transform: 'translateY(-10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
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
  transition-duration: 200ms;
}

/* Professional Multinational Enterprise Background */
body {
  background-color: #080c14;
  background-image: 
    radial-gradient(circle at 15% 10%, rgba(37, 99, 235, 0.09) 0%, transparent 45%),
    radial-gradient(circle at 85% 15%, rgba(6, 182, 212, 0.07) 0%, transparent 45%),
    radial-gradient(circle at 50% 85%, rgba(15, 23, 42, 0.8) 0%, transparent 100%),
    linear-gradient(180deg, #080c14 0%, #0a0f1d 50%, #070a12 100%);
  background-attachment: fixed;
  color: #f8fafc;
  font-family: 'Montserrat', 'Segoe UI', system-ui, -apple-system, sans-serif;
  margin: 0;
  -webkit-font-smoothing: antialiased;
}

main {
  animation: fadeIn 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards;
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
  transition: all 0.28s cubic-bezier(0.16, 1, 0.3, 1);
}

.card:hover {
  background: rgba(22, 33, 62, 0.78);
  border-color: rgba(37, 99, 235, 0.35);
  transform: translateY(-2px);
  box-shadow: 0 16px 36px -8px rgba(0, 0, 0, 0.6), 0 0 25px rgba(37, 99, 235, 0.12), inset 0 1px 0 0 rgba(255, 255, 255, 0.12);
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
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
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

/* HTMX Transition Classes */
.htmx-swapping {
  opacity: 0;
  transition: opacity 180ms ease-out;
}
.htmx-settling {
  opacity: 1;
  transition: opacity 180ms ease-in;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes slideDown {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}
''')

HEAD_EXTRA = [
    Meta(name="theme-color", content="#080c14"),
    Link(rel="icon", href="/favicon.ico"),
    Link(rel="apple-touch-icon", href="/favicon-192.png")
]

hdrs = [STYLE, *HEAD_EXTRA, TAILWIND_CDN, TAILWIND_CONFIG, GOOGLE_FONTS, GOOGLE_FONTS2, GOOGLE_FONTS_LINK, MATERIAL_ICONS]
