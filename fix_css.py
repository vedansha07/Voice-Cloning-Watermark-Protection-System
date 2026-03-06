import re

with open('app.py', 'r') as f:
    content = f.read()

new_css = """def inject_css():
    st.markdown('''
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Syne:wght@600;700;800&display=swap');
    
    :root {
        --bg: #ebebeb;
        --card: transparent;
        --accent: #ff9a9e;
        --low: #a8e6cf;
        --med: #ffd3b6;
        --high: #ff8b94;
        --text: #000000;
        --muted: #4f4f4f;
        --border: #000000;
        --box-bg: #ffffff;
        --syne: 'Syne', sans-serif;
        --sg: 'Space Grotesk', sans-serif;
    }
    
    @media (prefers-color-scheme: dark) {
        :root {
            --bg: #121212;
            --text: #ffffff;
            --border: #ffffff;
            --muted: #a0a0a0;
            --box-bg: #1e1e1e;
        }
    }
    
    .stApp {
        background-color: var(--bg);
        color: var(--text);
        font-family: var(--sg);
        background-image: radial-gradient(var(--muted) 1px, transparent 1px);
        background-size: 20px 20px;
    }
    
    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="stSidebarCollapseButton"] {
        display: none !important;
    }

    [data-testid="stElementToolbar"] {
        display: flex !important;
        align-items: center !important;
        justify-content: flex-end !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    [data-testid="stElementToolbar"] > div,
    [data-testid="StyledFullScreenButton"] {
        background-color: var(--border) !important;
        border: 2px solid var(--border) !important;
        border-radius: 0px !important;
        box-shadow: 2px 2px 0px 0px var(--border) !important;
        opacity: 1 !important;
    }
    
    [data-testid="stElementToolbar"] button,
    [data-testid="StyledFullScreenButton"] {
        color: var(--bg) !important;
    }
    
    [data-testid="stElementToolbar"] svg,
    [data-testid="StyledFullScreenButton"] svg {
        color: var(--bg) !important;
        fill: var(--bg) !important;
    }
    
    [data-testid="stSidebar"] {
        background-color: var(--bg);
        border-right: 2px solid var(--border);
    }
    
    h1, h2, h3, h4, h5, h6, p, span, div {
        color: var(--text);
        font-family: var(--sg);
    }

    div[data-baseweb="select"] *, div[role="listbox"] * {
        color: inherit !important;
    }

    button[kind="primary"], button[kind="secondary"] {
        background-color: var(--box-bg) !important;
        color: var(--text) !important;
        border: 2px solid var(--border) !important;
        border-radius: 0px !important;
        padding: 0.5rem 1rem !important;
        font-family: var(--sg) !important;
        font-weight: 700 !important;
        box-shadow: 4px 4px 0px 0px var(--border) !important;
        text-transform: lowercase !important;
        transition: all 0.1s !important;
    }
    button[kind="primary"] {
        background-color: var(--accent) !important;
        color: #000 !important;
    }
    button[kind="primary"]:active, button[kind="secondary"]:active {
        transform: translate(4px, 4px) !important;
        box-shadow: 0px 0px 0px 0px var(--border) !important;
    }
    
    .hero-container {
        text-align: center;
        padding: 60px 20px;
        background: linear-gradient(135deg, #fecfef 0%, #ff9a9e 100%);
        border: 2px solid var(--border);
        box-shadow: 6px 6px 0px 0px var(--border);
        margin-bottom: 32px;
    }
    .hero-title {
        font-family: var(--syne) !important;
        font-size: 4rem;
        font-weight: 800;
        color: #000;
        margin-bottom: 16px;
        letter-spacing: -0.05em;
    }
    .hero-subtitle {
        font-size: 1.125rem;
        font-weight: 600;
        max-width: 650px;
        margin: 0 auto;
        line-height: 1.6;
        font-family: var(--sg) !important;
        color: #000;
    }
    
    .card {
        background-color: var(--bg);
        border: 2px solid var(--border);
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 4px 4px 0px 0px var(--border);
    }
    
    .metric-card {
        background-color: var(--box-bg);
        border: 2px solid var(--border);
        padding: 24px;
        text-align: center;
        margin-bottom: 24px;
        box-shadow: 4px 4px 0px 0px var(--border);
        transition: all 0.1s;
    }
    .metric-card:hover {
        transform: translate(-2px, -2px);
        box-shadow: 6px 6px 0px 0px var(--border);
    }
    .metric-value {
        font-family: var(--syne) !important;
        font-size: 3rem;
        font-weight: 800;
        margin: 12px 0;
        color: var(--text) !important;
    }
    .metric-label {
        font-family: var(--sg) !important;
        font-size: 1rem;
        font-weight: 700;
        text-transform: lowercase;
        border-bottom: 2px solid var(--border);
        display: inline-block;
        padding-bottom: 4px;
    }
    
    .verdict-card {
        background-color: var(--box-bg);
        border: 2px solid var(--border);
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 4px 4px 0px 0px var(--border);
    }
    .verdict-card.high { background-color: var(--high); color: #000 !important; }
    .verdict-card.medium { background-color: var(--med); color: #000 !important; }
    .verdict-card.low { background-color: var(--low); color: #000 !important; }
    
    .v-title {
        font-family: var(--syne) !important;
        font-size: 2rem;
        font-weight: 800;
        text-transform: lowercase;
    }
    
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border: 2px solid var(--border);
        font-family: var(--sg) !important;
        font-weight: 800;
        text-transform: lowercase;
        background: var(--box-bg);
        box-shadow: 2px 2px 0px 0px var(--border);
    }
    .badge.high { background: var(--high); color: #000; border-color: #000; box-shadow: 2px 2px 0px 0px #000; }
    .badge.medium { background: var(--med); color: #000; border-color: #000; box-shadow: 2px 2px 0px 0px #000; }
    .badge.low { background: var(--low); color: #000; border-color: #000; box-shadow: 2px 2px 0px 0px #000; }
    
    .section-header {
        font-family: var(--syne) !important;
        font-size: 2rem;
        font-weight: 800;
        color: var(--text);
        margin-bottom: 16px;
        text-transform: lowercase;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 2px solid var(--border);
        padding-bottom: 8px;
    }
    
    div[data-testid="stFileUploader"] {
        background-color: var(--box-bg);
        border: 2px dashed var(--border);
        border-radius: 0px !important;
        padding: 24px;
        box-shadow: 4px 4px 0px 0px var(--border);
    }
    
    .stCheckbox > label {
        color: var(--text) !important;
        font-weight: 600;
        font-family: var(--sg) !important;
    }
    
    [data-testid="stDataFrame"] {
        background-color: var(--box-bg);
        border: 2px solid var(--border);
        box-shadow: 4px 4px 0px 0px var(--border);
    }
    
    .stProgress > div > div > div > div {
        background-color: var(--text) !important;
        border-radius: 0px !important;
    }
    .stProgress > div > div > div {
        background-color: var(--box-bg) !important;
        border-radius: 0px !important;
        border: 2px solid var(--border) !important;
    }
    
    .stMarkdown { color: var(--text) !important; }
    </style>
    ''', unsafe_allow_html=True)"""

# replace the inject_css function
content = re.sub(r'def inject_css\(\):.*?(?=def render_dashboard\(\):)', new_css + '\n\n', content, flags=re.DOTALL)

# Inline style fixes (convert #fff to var(--box-bg), #000 to var(--border))
# We be careful not to break standard valid strings
content = content.replace("background-color: {('var(--high)' if high_risk_count > 0 else '#fff')};", "background-color: {('var(--high)' if high_risk_count > 0 else 'var(--box-bg)')};")

# Fix inline styles for progress bars and metric cards
content = content.replace('background: #fff; height: 12px; border: 2px solid #000;', 'background: var(--box-bg); height: 12px; border: 2px solid var(--border);')
content = content.replace('background: #000; width:', 'background: var(--text); width:')

content = content.replace('border: 2px solid #000;', 'border: 2px solid var(--border);')
content = content.replace('background: #fff; border: 2px solid #000; box-shadow: 4px 4px 0px 0px #000;', 'background: var(--box-bg); border: 2px solid var(--border); box-shadow: 4px 4px 0px 0px var(--border);')
content = content.replace('border-bottom: 2px solid #000;', 'border-bottom: 2px solid var(--border);')

# Matplotlib styles (use dark grey colors to show up well on both if needed, but #ebebeb and #fff are used for ax)
# Matplotlib does not natively support CSS variables. We will just let matplotlib maintain its light theme design, it's an image.
# We will just change text color for selectbox and app dark mode.

with open('app.py', 'w') as f:
    f.write(content)
