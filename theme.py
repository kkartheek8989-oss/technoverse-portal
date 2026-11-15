from fasthtml.common import *

TAILWIND_CDN = Script(src="https://cdn.tailwindcss.com")

TAILWIND_CONFIG = Script("""
tailwind.config = {
  theme: {
    extend: {
      colors: {
        dark: '#070d24',
        card: '#0f1a3d',
        primary: '#1769e0',
        amber: '#f5a623',
        border: 'rgba(255,255,255,0.08)',
        text: '#eaf0ff',
        secondary: '#94a3b8',
        muted: '#64748b',
      },
      fontFamily: {
        sans: ['Montserrat', 'Segoe UI', 'system-ui', '-apple-system', 'sans-serif'],
        heading: ['Montserrat', 'Impact', 'Segoe UI', 'sans-serif'],
        display: ['Impact', 'Montserrat', 'Segoe UI', 'sans-serif'],
        mono: ['JetBrains Mono', 'Consolas', 'monospace'],
      },
      borderRadius: {
        card: '14px',
        sheet: '20px',
        modal: '24px',
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
body {
  background: #070d24;
  color: #eaf0ff;
  font-family: 'Montserrat', 'Segoe UI', system-ui, -apple-system, sans-serif;
  margin: 0;
  -webkit-font-smoothing: antialiased;
}
h1, h2, h3, h4, .font-heading {
  font-family: 'Montserrat', 'Segoe UI', sans-serif;
  letter-spacing: -0.015em;
}
.impact-text {
  font-family: 'Impact', 'Montserrat', 'Segoe UI', sans-serif;
  letter-spacing: 0.04em;
}
.card {
  background: #0f1a3d;
  border: 1px solid rgba(255,255,255,.08);
}
.input {
  background: #070d24;
  border: 1px solid rgba(255,255,255,.12);
  border-radius: 8px;
  padding: .6rem .75rem;
  color: #eaf0ff;
  font-family: 'Montserrat', 'Segoe UI', sans-serif;
}
.input:focus {
  outline: 2px solid #1769e0;
}
a {
  color: inherit;
  text-decoration: none;
}
''')

HEAD_EXTRA = [
    Meta(name="theme-color", content="#070d24"),
    Link(rel="icon", href="/favicon.ico"),
    Link(rel="apple-touch-icon", href="/favicon-192.png")
]

hdrs = [STYLE, *HEAD_EXTRA, TAILWIND_CDN, TAILWIND_CONFIG, GOOGLE_FONTS, GOOGLE_FONTS2, GOOGLE_FONTS_LINK, MATERIAL_ICONS]
