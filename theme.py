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
        sans: ['Inter', 'sans-serif'],
        heading: ['Plus Jakarta Sans', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
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
    href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Plus+Jakarta+Sans:wght@500;600;700&family=JetBrains+Mono:wght@400;500&display=swap",
    rel="stylesheet"
)

MATERIAL_ICONS = Link(
    href="https://fonts.googleapis.com/icon?family=Material+Symbols+Outlined",
    rel="stylesheet"
)

STYLE = Style('''
body{background:#070d24;color:#eaf0ff;font-family:Inter,sans-serif;margin:0}
.card{background:#0f1a3d;border:1px solid rgba(255,255,255,.08)}
.input{background:#070d24;border:1px solid rgba(255,255,255,.12);border-radius:8px;padding:.6rem .75rem;color:#eaf0ff}
.input:focus{outline:2px solid #1769e0}
a{color:inherit;text-decoration:none}
''')
HEAD_EXTRA = [Meta(name="theme-color", content="#070d24"), Link(rel="icon", href="/favicon.ico"),
              Link(rel="apple-touch-icon", href="/favicon-192.png")]

hdrs = [STYLE, *HEAD_EXTRA, TAILWIND_CDN, TAILWIND_CONFIG, GOOGLE_FONTS, GOOGLE_FONTS2, GOOGLE_FONTS_LINK, MATERIAL_ICONS]