import os
import tempfile
import sqlite3
from datetime import datetime
import streamlit as st
import matplotlib.pyplot as plt

# Must be called first
st.set_page_config(page_title="Aawaaz brutalist", layout="wide", initial_sidebar_state="expanded")

from detector import DeepfakeDetector
from watermark import detect_watermark, embed_watermark
from decision import generate_verdict
from database import init_db, save_analysis, fetch_all_history, clear_history

# Initialize Database
init_db()

@st.cache_resource
def load_model() -> DeepfakeDetector:
    return DeepfakeDetector()

try:
    detector_model = load_model()
except Exception as e:
    st.error(f"Initialization failed: {e}")
    st.stop()

# ---------------------------
# GLOBAL CSS INJECTION (BRUTALIST THEME)
# ---------------------------
def inject_css():
    st.markdown("""
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
        --syne: 'Syne', sans-serif;
        --sg: 'Space Grotesk', sans-serif;
    }
    
    .stApp {
        background-color: var(--bg);
        color: var(--text);
        font-family: var(--sg);
        background-image: radial-gradient(#c0c0c0 1px, transparent 1px);
        background-size: 20px 20px;
    }
    
    /* Hide the top Streamlit header (black stripe) */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    
    [data-testid="stSidebar"] {
        background-color: #dcdcdc;
        border-right: 2px solid var(--border);
    }
    
    h1, h2, h3, h4, h5, h6, p, span, div {
        color: var(--text);
        font-family: var(--sg);
    }

    button[kind="primary"], button[kind="secondary"] {
        background-color: #fff !important;
        color: #000 !important;
        border: 2px solid #000 !important;
        border-radius: 0px !important;
        padding: 0.5rem 1rem !important;
        font-family: var(--sg) !important;
        font-weight: 700 !important;
        box-shadow: 4px 4px 0px 0px #000 !important;
        text-transform: lowercase !important;
        transition: all 0.1s !important;
    }
    button[kind="primary"] {
        background-color: var(--accent) !important;
    }
    button[kind="primary"]:active, button[kind="secondary"]:active {
        transform: translate(4px, 4px) !important;
        box-shadow: 0px 0px 0px 0px #000 !important;
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
        color: var(--text);
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
    }
    
    .card {
        background-color: var(--bg);
        border: 2px solid var(--border);
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 4px 4px 0px 0px var(--border);
    }
    
    .metric-card {
        background-color: #fff;
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
        background-color: #fff;
        border: 2px solid var(--border);
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 4px 4px 0px 0px var(--border);
    }
    .verdict-card.high { background-color: var(--high); }
    .verdict-card.medium { background-color: var(--med); }
    .verdict-card.low { background-color: var(--low); }
    
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
        background: #fff;
        box-shadow: 2px 2px 0px 0px var(--border);
    }
    .badge.high { background: var(--high); }
    .badge.medium { background: var(--med); }
    .badge.low { background: var(--low); }
    
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
        background-color: #fff;
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
        background-color: #fff;
        border: 2px solid var(--border);
        box-shadow: 4px 4px 0px 0px var(--border);
    }
    
    /* Modify Streamlit's Progress Bar */
    .stProgress > div > div > div > div {
        background-color: var(--text) !important;
        border-radius: 0px !important;
    }
    .stProgress > div > div > div {
        background-color: #fff !important;
        border-radius: 0px !important;
        border: 2px solid var(--border) !important;
    }
    
    /* Hide Streamlit components background for cards */
    .stMarkdown { color: var(--text) !important; }
    </style>
    """, unsafe_allow_html=True)

# ---------------------------
# PAGE VIEWS
# ---------------------------

def render_dashboard():
    st.markdown('''
    <div class="hero-container">
        <div class="hero-title">Aawaaz Dashboard</div>
        <div class="hero-subtitle">dual-layer ai deepfake detection and spectral watermark verification.<br>protecting audio authenticity reliably and effectively.</div>
    </div>
    ''', unsafe_allow_html=True)
    
    history = fetch_all_history()
    total_analyses = len(history)
    high_risk_count = sum(1 for r in history if r['risk_level'] == 'High')
    avg_score = sum(r['risk_score'] for r in history) / total_analyses if total_analyses > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">total analyses</div>
            <div class="metric-value">{total_analyses}</div>
        </div>
        ''', unsafe_allow_html=True)
    with col2:
        st.markdown(f'''
        <div class="metric-card" style="background-color: {'var(--high)' if high_risk_count > 0 else '#fff'};">
            <div class="metric-label">high risk count</div>
            <div class="metric-value">{high_risk_count}</div>
        </div>
        ''', unsafe_allow_html=True)
    with col3:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">average risk score</div>
            <div class="metric-value">{avg_score:.1f}%</div>
        </div>
        ''', unsafe_allow_html=True)
        
    st.markdown('''
    <div class="card">
        <div class="section-header" style="border-bottom: none;"><span>system overview</span> <span>↗</span></div>
        <p style="color: var(--muted); line-height: 1.8; margin-top: 0;">
            <strong>Layer 1: AI Detection (Wav2Vec2)</strong><br>
            Analyzes raw audio to detect synthetic artifacts and AI-generated speech patterns.<br><br>
            <strong>Layer 2: Watermark Verification (FFT)</strong><br>
            Verifies the presence of a hidden spectral watermark to confirm the audio was authorized by this system.<br><br>
            <strong>Risk Scoring</strong><br>
            Combines AI detection and watermark verification into a final 0-100% Risk Score to determine authenticity.
        </p>
    </div>
    ''', unsafe_allow_html=True)


def render_verify():
    st.markdown('<div class="section-header"><span>upload audio</span> <span>↗</span></div>', unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Upload Audio File (WAV/MP3)", type=["wav", "mp3"], label_visibility="collapsed")
    
    if uploaded_file is not None:
        suffix = os.path.splitext(uploaded_file.name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_filepath = tmp_file.name
        
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.audio(uploaded_file, format=f"audio/{suffix.strip('.')}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="section-header"><span>analysis controls</span> <span>↗</span></div>', unsafe_allow_html=True)
        st.markdown('<div class="card">', unsafe_allow_html=True)
        embed_wm = st.checkbox("Embed watermark before analysis", key="embed_chk")
        st.markdown('<br>', unsafe_allow_html=True)
        analyze_clicked = st.button("analyze audio", type="primary", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        if analyze_clicked:
            analysis_filepath = tmp_filepath
            watermarked_tmp = None
            
            if embed_wm:
                with st.spinner("Embedding spectral watermark..."):
                     with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as wt_file:
                         watermarked_tmp = wt_file.name
                     try:
                         embed_watermark(tmp_filepath, watermarked_tmp)
                         analysis_filepath = watermarked_tmp
                     except Exception as e:
                         st.error(f"Watermark embedding failed: {e}")
            
            with st.spinner("Processing deepfake classification and watermark..."):
                try:
                    with open(analysis_filepath, "rb") as af:
                        analysis_bytes = af.read()
                        analysis_suffix = os.path.splitext(analysis_filepath)[1]
                        
                    deepfake_label, deepfake_confidence = detector_model.detect(analysis_bytes, suffix=analysis_suffix)
                    watermark_confidence = detect_watermark(analysis_filepath)
                    verdict_results = generate_verdict(deepfake_label, deepfake_confidence, watermark_confidence)
                    
                    save_analysis(
                        filename=uploaded_file.name,
                        deepfake_label=deepfake_label,
                        deepfake_confidence=deepfake_confidence,
                        watermark_confidence=watermark_confidence,
                        risk_score=verdict_results.get("risk_score", 0),
                        final_verdict=verdict_results.get("final_verdict", "Unknown"),
                        risk_level=verdict_results.get("risk_level", "Unknown")
                    )
                except Exception as e:
                    st.error(f"Analysis failed: {e}")
                    st.stop()
                    
            st.markdown('<div class="section-header" style="margin-top: 32px;"><span>analysis results</span> <span>↗</span></div>', unsafe_allow_html=True)
            
            ai_val = verdict_results.get("ai_risk_component", 0.0)
            wm_val = verdict_results.get("watermark_risk_component", 0.0)
            risk_score = verdict_results.get("risk_score", 0.0)
            risk_level = verdict_results.get("risk_level", "Unknown")
            final_verdict = verdict_results.get("final_verdict", "Unknown")
            explanation = verdict_results.get("explanation", "")
            
            c1, c2, c3 = st.columns(3)
            
            badge_class = risk_level.lower()
            
            with c1:
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-label">deepfake detection</div>
                    <div class="metric-value">{deepfake_label.upper()}</div>
                    <div style="font-size: 0.875rem; font-weight: 600; margin-bottom: 12px;">Confidence: {deepfake_confidence*100:.1f}%</div>
                    <div style="background: #fff; height: 12px; border: 2px solid #000; width: 100%;">
                        <div style="background: #000; width: {deepfake_confidence*100}%; height: 100%;"></div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            with c2:
                wm_label = "DETECTED" if watermark_confidence >= 0.7 else "NOT DETECTED"
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-label">watermark verification</div>
                    <div class="metric-value">{wm_label}</div>
                    <div style="font-size: 0.875rem; font-weight: 600; margin-bottom: 12px;">Confidence: {watermark_confidence*100:.1f}%</div>
                    <div style="background: #fff; height: 12px; border: 2px solid #000; width: 100%;">
                        <div style="background: #000; width: {watermark_confidence*100}%; height: 100%;"></div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            with c3:
                st.markdown(f'''
                <div class="metric-card" style="background-color: var(--{badge_class});">
                    <div class="metric-label">aggregated risk score</div>
                    <div class="metric-value">{risk_score}%</div>
                    <div style="font-size: 0.875rem; font-weight: 600; margin-bottom: 12px;">Rating: {risk_level.upper()}</div>
                    <div style="background: rgba(255,255,255,0.5); height: 12px; border: 2px solid #000; width: 100%;">
                        <div style="background: #000; width: {risk_score}%; height: 100%;"></div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
                
            st.markdown(f'''
            <div class="verdict-card {badge_class}">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                    <div class="v-title">{final_verdict}</div>
                    <div class="badge {badge_class}">{risk_level.upper()} RISK</div>
                </div>
                <div style="font-weight: 600; line-height: 1.6;">{explanation}</div>
            </div>
            ''', unsafe_allow_html=True)
            
            consistency_msg = "No definitive conflict detected."
            if ai_val > 60 and watermark_confidence >= 0.7:
                consistency_msg = "Warning: Watermark is present but AI model indicates synthetic characteristics. Possible watermark injection attack."
            elif ai_val < 40 and watermark_confidence < 0.3:
                consistency_msg = "Warning: AI model suggests authenticity, but watermark verification failed. Possible unauthorized recording."
            elif ai_val > 60 and watermark_confidence < 0.3:
                consistency_msg = "Both AI and watermark layers agree: audio is highly suspicious."
            elif ai_val < 40 and watermark_confidence >= 0.7:
                consistency_msg = "Both AI and watermark layers are consistent and indicate authenticity."
                
            st.markdown(f'''
            <div class="card">
                <div style="font-family: var(--syne); font-size: 1.25rem; font-weight: 800; color: var(--text); margin-bottom: 12px; text-transform: lowercase;">cross-layer consistency analysis ↗</div>
                <div style="padding: 16px; background: #fff; border: 2px solid #000; box-shadow: 4px 4px 0px 0px #000; font-weight: 600;">
                    {consistency_msg}
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            # Temporary File Cleanup
            if os.path.exists(tmp_filepath):
                try: os.remove(tmp_filepath)
                except: pass
            if watermarked_tmp and os.path.exists(watermarked_tmp):
                try: os.remove(watermarked_tmp)
                except: pass

def render_embed():
    st.markdown('<div class="section-header"><span>watermark studio</span> <span>↗</span></div>', unsafe_allow_html=True)
    st.markdown('<p style="font-weight: 600; margin-bottom: 24px; font-size: 1.1rem;">Upload an audio file to embed a secure spectral watermark. This process does not perform deepfake analysis.</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="card" style="height: 100%;">', unsafe_allow_html=True)
        st.markdown('<div style="font-family: var(--syne); font-size: 1.5rem; font-weight: 800; margin-bottom: 12px; text-transform: lowercase;">original audio</div>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Upload Audio", type=["wav", "mp3"], key="wm_uploader", label_visibility="collapsed")
        gen_clicked = None
        if uploaded_file:
            st.markdown('<br>', unsafe_allow_html=True)
            gen_clicked = st.button("generate watermarked audio", type="primary", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        st.markdown('<div class="card" style="height: 100%;">', unsafe_allow_html=True)
        st.markdown('<div style="font-family: var(--syne); font-size: 1.5rem; font-weight: 800; margin-bottom: 12px; text-transform: lowercase;">watermarked audio</div>', unsafe_allow_html=True)
        
        if uploaded_file and gen_clicked:
            suffix = os.path.splitext(uploaded_file.name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as t_in:
                t_in.write(uploaded_file.getvalue())
                t_in_path = t_in.name
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as t_out:
                t_out_path = t_out.name
                
            with st.spinner("Embedding spectral watermark..."):
                try:
                    embed_watermark(t_in_path, t_out_path)
                    st.success("Watermark successfully embedded.")
                    st.audio(t_out_path, format="audio/wav")
                    
                    with open(t_out_path, "rb") as f:
                        aud_bytes = f.read()
                    st.download_button(label="download watermarked audio", data=aud_bytes, file_name=f"watermarked_{uploaded_file.name}", mime="audio/wav", type="primary", use_container_width=True)
                except Exception as e:
                    st.error(f"Watermark failed to embed: {e}")
        else:
            st.markdown('<div style="background: #fff; font-weight: 600; border: 2px dashed var(--border); padding: 40px; text-align: center;">no file processed yet.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


def render_history():
    st.markdown('<div class="section-header"><span>history</span> <span>↗</span></div>', unsafe_allow_html=True)
    
    history_records = fetch_all_history()
    
    if not history_records:
        st.info("No historical data available. Run an analysis to generate history.")
        return
        
    df_data = []
    for rec in history_records:
        df_data.append({
            "ID": rec["id"],
            "Time": rec["timestamp"],
            "Filename": rec["filename"],
            "Verdict": rec["final_verdict"],
            "Risk Score": rec["risk_score"],
            "AI Label": rec["deepfake_label"],
            "WM Confidence": round(rec["watermark_confidence"], 3)
        })
        
    st.dataframe(df_data, use_container_width=True, hide_index=True)
    
    st.markdown('<div class="section-header" style="margin-top: 32px;"><span>recent risk score trends</span> <span>↗</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    
    recent = history_records[:20]
    recent.reverse()
    
    if len(recent) > 1:
        plt.style.use("default")
        fig, ax = plt.subplots(figsize=(10, 4))
        times = [r["timestamp"].split(" ")[1] for r in recent]
        scores = [r["risk_score"] for r in recent]
        
        ax.plot(times, scores, color="#000", marker="s", linewidth=2, markersize=8, markeredgecolor='black', markerfacecolor='#ff9a9e')
        fig.patch.set_facecolor('#ebebeb')
        ax.set_facecolor('#fff')
        
        for spine in ax.spines.values():
            spine.set_edgecolor('black')
            spine.set_linewidth(2)
            
        ax.tick_params(colors='#000', width=2)
        ax.set_ylabel("Risk Score", color="#000", fontname='Space Grotesk', fontweight='bold')
        plt.xticks(rotation=45, ha='right', fontsize=8, fontname='Space Grotesk')
        ax.grid(True, linestyle="-", alpha=1, color="#000", linewidth=0.5)
        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.markdown('<div style="text-align: center; font-weight: 600; padding: 20px;">Need at least 2 historical records to plot trends.</div>', unsafe_allow_html=True)
        
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="section-header" style="margin-top: 32px; color: var(--high); border-bottom-color: var(--high);"><span>clear history</span> <span>↗</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="card" style="background: var(--high);">', unsafe_allow_html=True)
    st.markdown('<div style="font-family: var(--syne); font-size: 1.5rem; font-weight: 800; margin-bottom: 8px;">delete data</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-weight: 600; margin-bottom: 16px;">This action will permanently delete all analysis history from the database.</div>', unsafe_allow_html=True)
    
    confirm = st.checkbox("I understand, proceed to clear")
    if confirm:
        if st.button("clear history", type="secondary"):
            clear_history()
            st.success("History successfully cleared.")
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


def render_analytics():
    st.markdown('<div class="section-header"><span>analytics</span> <span>↗</span></div>', unsafe_allow_html=True)
    history = fetch_all_history()
    
    if not history:
        st.info("No logs available to visualize data.")
        return
        
    low_count = sum(1 for r in history if r['risk_level'] == 'Low')
    med_count = sum(1 for r in history if r['risk_level'] == 'Medium')
    high_count = sum(1 for r in history if r['risk_level'] == 'High')
    total = len(history)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="card"><div style="font-family: var(--syne); font-size: 1.5rem; font-weight: 800; text-transform: lowercase; border-bottom: 2px solid #000; padding-bottom: 8px; margin-bottom: 16px;">risk distribution</div>', unsafe_allow_html=True)
        
        plt.style.use("default")
        fig, ax = plt.subplots(figsize=(6, 4))
        labels = ['Low Risk', 'Medium Risk', 'High Risk']
        sizes = [low_count, med_count, high_count]
        colors = ['#a8e6cf', '#ffd3b6', '#ff8b94']
        
        # Filter zeroes
        valid_sizes, valid_lbls, valid_cols = [], [], []
        for i in range(len(sizes)):
            if sizes[i] > 0:
                valid_sizes.append(sizes[i])
                valid_lbls.append(labels[i])
                valid_cols.append(colors[i])
                
        if valid_sizes:
            ax.pie(valid_sizes, labels=valid_lbls, colors=valid_cols, autopct='%1.1f%%', startangle=90, textprops={'color': '#000', 'fontweight': 'bold', 'family': 'Space Grotesk'}, wedgeprops={'edgecolor': 'black', 'linewidth': 2})
            centre_circle = plt.Circle((0,0), 0.70, fc='#ebebeb', ec='black', lw=2)
            fig.gca().add_artist(centre_circle)
            
        fig.patch.set_facecolor('#ebebeb')
        ax.set_facecolor('#ebebeb')
        plt.tight_layout()
        st.pyplot(fig)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div style="font-family: var(--syne); font-size: 1.5rem; font-weight: 800; text-transform: lowercase; border-bottom: 2px solid #000; padding-bottom: 8px; margin-bottom: 16px;">average scores</div>', unsafe_allow_html=True)
        
        avg_wm = sum(r['watermark_confidence'] for r in history) / total
        avg_ai = sum(r['deepfake_confidence'] for r in history) / total
        
        st.markdown(f'''
        <div style="margin-bottom: 24px;">
            <div style="font-weight: 700; font-size: 0.875rem; text-transform: lowercase; border-bottom: 2px solid #000; display: inline-block;">average watermark confidence</div>
            <div style="font-family: var(--syne); font-size: 2.5rem; font-weight: 800;">{avg_wm*100:.1f}%</div>
        </div>
        <div style="margin-bottom: 24px;">
            <div style="font-weight: 700; font-size: 0.875rem; text-transform: lowercase; border-bottom: 2px solid #000; display: inline-block;">average ai detection confidence</div>
            <div style="font-family: var(--syne); font-size: 2.5rem; font-weight: 800;">{avg_ai*100:.1f}%</div>
        </div>
        <div style="margin-bottom: 12px;">
            <div style="font-weight: 700; font-size: 0.875rem; text-transform: lowercase; border-bottom: 2px solid #000; display: inline-block;">total analyses run</div>
            <div style="font-family: var(--syne); font-size: 2.5rem; font-weight: 800;">{total} operations</div>
        </div>
        ''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

def render_architecture():
    st.markdown('<div class="section-header"><span>system architecture</span> <span>↗</span></div>', unsafe_allow_html=True)
    st.markdown('''
    <div class="card">
        <h3 style="margin-top: 0; margin-bottom: 16px; font-family: var(--syne); font-size: 2rem;">processing pipeline</h3>
        <p style="font-weight: 500; line-height: 1.8; margin-bottom: 0;">
            <b>1. Audio Upload</b><br>
            Receives WAV/MP3 files and saves them to temporary storage.
            <br><br>
            <b>2. Resampling & Preprocessing</b><br>
            Normalizes the audio sample rates using `librosa` to prepare the audio for AI analysis.
            <br><br>
            <b>3. AI Detection (Wav2Vec2)</b><br>
            Processes the audio through a transformer network trained for deepfake detection. Outputs an authenticity probability.
            <br><br>
            <b>4. Watermark Verification (FFT)</b><br>
            Analyzes the audio frequency spectrum using Fast Fourier Transform to detect hidden spectral watermarks.
            <br><br>
            <b>5. Risk Engine</b><br>
            Combines AI and watermark results into a final 0-100% Risk Score to determine if the audio is a deepfake or authentic.
            <br><br>
            <b>6. Database Logging</b><br>
            Saves the results into a local SQLite database for historical analytics.
        </p>
    </div>
    ''', unsafe_allow_html=True)


# Execute Routines
inject_css()

# Render Sidebar
st.sidebar.markdown('<h2 style="font-family: var(--syne); text-align: center; margin-bottom: 32px; margin-top: 16px; text-transform: lowercase;">navigation</h2>', unsafe_allow_html=True)
nav_choice = st.sidebar.radio(
    "Navigation Menu",
    options=["Dashboard", "Verify Audio", "Embed Watermark", "History", "Analytics", "Architecture"],
    label_visibility="collapsed"
)

if nav_choice == "Dashboard":
    render_dashboard()
elif nav_choice == "Verify Audio":
    render_verify()
elif nav_choice == "Embed Watermark":
    render_embed()
elif nav_choice == "History":
    render_history()
elif nav_choice == "Analytics":
    render_analytics()
elif nav_choice == "Architecture":
    render_architecture()
