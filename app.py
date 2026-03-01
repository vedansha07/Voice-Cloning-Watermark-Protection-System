import os
import tempfile
import sqlite3
from datetime import datetime
import streamlit as st
import matplotlib.pyplot as plt

# Must be called first
st.set_page_config(page_title="Aawaaz Dashboard", layout="wide", initial_sidebar_state="expanded")

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
# GLOBAL CSS INJECTION
# ---------------------------
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    :root {
        --bg: #0f172a;
        --card: #1e293b;
        --accent: #3b82f6;
        --low: #10b981;
        --med: #f59e0b;
        --high: #ef4444;
        --text: #f8fafc;
        --muted: #94a3b8;
        --border: #334155;
    }
    
    .stApp {
        background-color: var(--bg);
        color: var(--text);
        font-family: 'Inter', sans-serif;
    }
    
    [data-testid="stSidebar"] {
        background-color: #020617;
        border-right: 1px solid var(--border);
    }
    
    h1, h2, h3, h4, h5, h6, p, span, div {
        font-family: 'Inter', sans-serif;
    }

    .hero-container {
        text-align: center;
        padding: 60px 20px;
        background: linear-gradient(180deg, rgba(30,41,59,0) 0%, rgba(30,41,59,0.5) 100%);
        border-radius: 16px;
        border: 1px solid var(--border);
        margin-bottom: 32px;
    }
    .hero-title {
        font-size: 3rem;
        font-weight: 800;
        color: var(--text);
        margin-bottom: 16px;
        letter-spacing: -0.02em;
    }
    .hero-subtitle {
        font-size: 1.125rem;
        color: var(--muted);
        max-width: 650px;
        margin: 0 auto;
        line-height: 1.6;
    }
    
    .card {
        background-color: var(--card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
    }
    
    .metric-card {
        background-color: var(--card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 24px;
        text-align: center;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 12px 0;
    }
    .metric-label {
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .risk-low { color: var(--low); }
    .risk-medium { color: var(--med); }
    .risk-high { color: var(--high); }
    
    .verdict-card {
        background-color: var(--card);
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
        border-left: 6px solid var(--border);
    }
    .verdict-card.high { border-left-color: var(--high); background-color: rgba(239, 68, 68, 0.05); }
    .verdict-card.medium { border-left-color: var(--med); background-color: rgba(245, 158, 11, 0.05); }
    .verdict-card.low { border-left-color: var(--low); background-color: rgba(16, 185, 129, 0.05); }
    
    .v-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--text);
    }
    
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
    }
    .badge.high { background: rgba(239, 68, 68, 0.1); color: var(--high); border: 1px solid rgba(239, 68, 68, 0.2); }
    .badge.medium { background: rgba(245, 158, 11, 0.1); color: var(--med); border: 1px solid rgba(245, 158, 11, 0.2); }
    .badge.low { background: rgba(16, 185, 129, 0.1); color: var(--low); border: 1px solid rgba(16, 185, 129, 0.2); }
    
    .section-header {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--text);
        margin-bottom: 16px;
        border-bottom: 1px solid var(--border);
        padding-bottom: 8px;
    }
    
    /* Native Overrides */
    button[kind="primary"] {
        background-color: var(--accent) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 600 !important;
    }
    button[kind="primary"]:hover {
        background-color: #2563eb !important;
    }
    button[kind="secondary"] {
        background-color: transparent !important;
        color: var(--text) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
    }
    button[kind="secondary"]:hover {
        border-color: var(--accent) !important;
        color: var(--accent) !important;
    }
    
    div[data-testid="stFileUploader"] {
        background-color: var(--card);
        border: 1px dashed var(--border);
        border-radius: 12px;
        padding: 24px;
    }
    
    .stCheckbox > label {
        color: var(--text) !important;
        font-weight: 500;
    }
    
    [data-testid="stDataFrame"] {
        background-color: var(--card);
        border: 1px solid var(--border);
        border-radius: 12px;
        overflow: hidden;
    }
    </style>
    """, unsafe_allow_html=True)

# ---------------------------
# PAGE VIEWS
# ---------------------------

def render_dashboard():
    st.markdown('''
    <div class="hero-container">
        <div class="hero-title">Aawaaz Dashboard</div>
        <div class="hero-subtitle">Dual-layer AI deepfake detection and spectral watermark verification.<br>Protecting audio authenticity reliably and effectively.</div>
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
            <div class="metric-label">Total Analyses</div>
            <div class="metric-value" style="color: var(--accent);">{total_analyses}</div>
        </div>
        ''', unsafe_allow_html=True)
    with col2:
        high_class = "risk-high" if high_risk_count > 0 else "risk-low"
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">High Risk Count</div>
            <div class="metric-value {high_class}">{high_risk_count}</div>
        </div>
        ''', unsafe_allow_html=True)
    with col3:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">Average Risk Score</div>
            <div class="metric-value">{avg_score:.1f}%</div>
        </div>
        ''', unsafe_allow_html=True)
        
    st.markdown('''
    <div class="card">
        <div class="section-header" style="border-bottom: none;">System Overview</div>
        <p style="color: var(--muted); line-height: 1.6; margin-top: 0;">
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
    st.markdown('<div class="section-header">Upload Audio</div>', unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Upload Audio File (WAV/MP3)", type=["wav", "mp3"], label_visibility="collapsed")
    
    if uploaded_file is not None:
        suffix = os.path.splitext(uploaded_file.name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_filepath = tmp_file.name
        
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.audio(uploaded_file, format=f"audio/{suffix.strip('.')}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="section-header">Analysis Controls</div>', unsafe_allow_html=True)
        st.markdown('<div class="card">', unsafe_allow_html=True)
        embed_wm = st.checkbox("Embed watermark before analysis", key="embed_chk")
        st.markdown('<br>', unsafe_allow_html=True)
        analyze_clicked = st.button("Analyze Audio", type="primary", use_container_width=True)
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
                    
            st.markdown('<div class="section-header" style="margin-top: 32px;">Analysis Results</div>', unsafe_allow_html=True)
            
            ai_val = verdict_results.get("ai_risk_component", 0.0)
            wm_val = verdict_results.get("watermark_risk_component", 0.0)
            risk_score = verdict_results.get("risk_score", 0.0)
            risk_level = verdict_results.get("risk_level", "Unknown")
            final_verdict = verdict_results.get("final_verdict", "Unknown")
            explanation = verdict_results.get("explanation", "")
            
            c1, c2, c3 = st.columns(3)
            
            ai_color = "var(--low)" if deepfake_label.lower() == "real" else "var(--high)"
            wm_color = "var(--low)" if watermark_confidence >= 0.7 else "var(--med)"
            risk_class = "risk-high" if risk_level == "High" else ("risk-medium" if risk_level == "Medium" else "risk-low")
            badge_class = risk_level.lower()
            
            with c1:
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-label">Deepfake Detection</div>
                    <div class="metric-value" style="color: {ai_color};">{deepfake_label.upper()}</div>
                    <div style="font-size: 0.875rem; color: var(--muted); margin-bottom: 12px;">Confidence: {deepfake_confidence*100:.1f}%</div>
                    <div style="background: var(--border); height: 6px; border-radius: 4px; overflow: hidden;">
                        <div style="background: {ai_color}; width: {deepfake_confidence*100}%; height: 100%;"></div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            with c2:
                wm_label = "DETECTED" if watermark_confidence >= 0.7 else "NOT DETECTED"
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-label">Watermark Verification</div>
                    <div class="metric-value" style="color: {wm_color};">{wm_label}</div>
                    <div style="font-size: 0.875rem; color: var(--muted); margin-bottom: 12px;">Confidence: {watermark_confidence*100:.1f}%</div>
                    <div style="background: var(--border); height: 6px; border-radius: 4px; overflow: hidden;">
                        <div style="background: {wm_color}; width: {watermark_confidence*100}%; height: 100%;"></div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            with c3:
                risk_accent = "var(--high)" if risk_level == "High" else ("var(--med)" if risk_level == "Medium" else "var(--low)")
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-label">Aggregated Risk Score</div>
                    <div class="metric-value {risk_class}">{risk_score}%</div>
                    <div style="font-size: 0.875rem; color: var(--muted); margin-bottom: 12px;">Rating: {risk_level.upper()}</div>
                    <div style="background: var(--border); height: 6px; border-radius: 4px; overflow: hidden;">
                        <div style="background: {risk_accent}; width: {risk_score}%; height: 100%;"></div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
                
            st.markdown(f'''
            <div class="verdict-card {badge_class}">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                    <div class="v-title">{final_verdict}</div>
                    <div class="badge {badge_class}">{risk_level.upper()} RISK</div>
                </div>
                <div style="color: var(--muted); line-height: 1.6;">{explanation}</div>
            </div>
            ''', unsafe_allow_html=True)
            
            consistency_msg = "No definitive conflict detected."
            consistency_type = "low"
            if ai_val > 60 and watermark_confidence >= 0.7:
                consistency_msg = "Warning: Watermark is present but AI model indicates synthetic characteristics. Possible watermark injection attack."
                consistency_type = "med"
            elif ai_val < 40 and watermark_confidence < 0.3:
                consistency_msg = "Warning: AI model suggests authenticity, but watermark verification failed. Possible unauthorized recording."
                consistency_type = "med"
            elif ai_val > 60 and watermark_confidence < 0.3:
                consistency_msg = "Both AI and watermark layers agree: audio is highly suspicious."
                consistency_type = "high"
            elif ai_val < 40 and watermark_confidence >= 0.7:
                consistency_msg = "Both AI and watermark layers are consistent and indicate authenticity."
                consistency_type = "low"
                
            st.markdown(f'''
            <div class="card">
                <div style="font-weight: 700; color: var(--text); margin-bottom: 12px;">Cross-Layer Consistency Analysis</div>
                <div style="padding: 16px; background: rgba(248, 250, 252, 0.03); border-radius: 8px; border-left: 4px solid var(--{consistency_type}); color: var(--muted); font-size: 0.95rem;">
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
    st.markdown('<div class="section-header">Watermark Studio</div>', unsafe_allow_html=True)
    st.markdown('<p style="color: var(--muted); margin-bottom: 24px; font-size: 1.1rem;">Upload an audio file to embed a secure spectral watermark. This process does not perform deepfake analysis.</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="card" style="height: 100%;">', unsafe_allow_html=True)
        st.markdown('<div style="font-weight: 600; margin-bottom: 12px;">Original Audio</div>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Upload Audio", type=["wav", "mp3"], key="wm_uploader", label_visibility="collapsed")
        gen_clicked = None
        if uploaded_file:
            st.markdown('<br>', unsafe_allow_html=True)
            gen_clicked = st.button("Generate Watermarked Audio", type="primary", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        st.markdown('<div class="card" style="height: 100%;">', unsafe_allow_html=True)
        st.markdown('<div style="font-weight: 600; margin-bottom: 12px;">Watermarked Audio</div>', unsafe_allow_html=True)
        
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
                    st.download_button(label="Download Watermarked Audio", data=aud_bytes, file_name=f"watermarked_{uploaded_file.name}", mime="audio/wav", type="primary", use_container_width=True)
                except Exception as e:
                    st.error(f"Watermark failed to embed: {e}")
        else:
            st.markdown('<div style="color: var(--border); border: 2px dashed var(--border); padding: 40px; text-align: center; border-radius: 8px;">No file processed yet.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


def render_history():
    st.markdown('<div class="section-header">History</div>', unsafe_allow_html=True)
    
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
    
    st.markdown('<div class="section-header" style="margin-top: 32px;">Recent Risk Score Trends</div>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    
    recent = history_records[:20]
    recent.reverse()
    
    if len(recent) > 1:
        plt.style.use("dark_background")
        fig, ax = plt.subplots(figsize=(10, 4))
        times = [r["timestamp"].split(" ")[1] for r in recent]
        scores = [r["risk_score"] for r in recent]
        
        ax.plot(times, scores, color="#3b82f6", marker="o", linewidth=2, markersize=5)
        fig.patch.set_facecolor('#1e293b')
        ax.set_facecolor('#1e293b')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#334155')
        ax.spines['bottom'].set_color('#334155')
        ax.tick_params(colors='#94a3b8')
        ax.set_ylabel("Risk Score", color="#94a3b8")
        plt.xticks(rotation=45, ha='right', fontsize=8)
        ax.grid(True, linestyle="--", alpha=0.2, color="#94a3b8")
        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.markdown('<div style="text-align: center; color: var(--muted); padding: 20px;">Need at least 2 historical records to plot trends.</div>', unsafe_allow_html=True)
        
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="section-header" style="margin-top: 32px; color: var(--high); border-bottom-color: var(--high);">Clear History</div>', unsafe_allow_html=True)
    st.markdown('<div class="card" style="border: 1px solid var(--high); background: rgba(239, 68, 68, 0.03);">', unsafe_allow_html=True)
    st.markdown('<div style="color: var(--text); font-weight: 700; margin-bottom: 8px;">Delete Data</div>', unsafe_allow_html=True)
    st.markdown('<div style="color: var(--muted); margin-bottom: 16px;">This action will permanently delete all analysis history from the database.</div>', unsafe_allow_html=True)
    
    confirm = st.checkbox("I understand, proceed to clear")
    if confirm:
        if st.button("Clear History", type="primary"):
            clear_history()
            st.success("History successfully cleared.")
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


def render_analytics():
    st.markdown('<div class="section-header">Analytics</div>', unsafe_allow_html=True)
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
        st.markdown('<div class="card"><div style="font-weight: 600; margin-bottom: 16px;">Risk Distribution</div>', unsafe_allow_html=True)
        
        plt.style.use("dark_background")
        fig, ax = plt.subplots(figsize=(6, 4))
        labels = ['Low Risk', 'Medium Risk', 'High Risk']
        sizes = [low_count, med_count, high_count]
        colors = ['#10b981', '#f59e0b', '#ef4444']
        
        # Filter zeroes
        valid_sizes, valid_lbls, valid_cols = [], [], []
        for i in range(len(sizes)):
            if sizes[i] > 0:
                valid_sizes.append(sizes[i])
                valid_lbls.append(labels[i])
                valid_cols.append(colors[i])
                
        if valid_sizes:
            ax.pie(valid_sizes, labels=valid_lbls, colors=valid_cols, autopct='%1.1f%%', startangle=90, textprops={'color': '#f8fafc', 'fontweight': 'bold'})
            centre_circle = plt.Circle((0,0), 0.70, fc='#1e293b')
            fig.gca().add_artist(centre_circle)
            
        fig.patch.set_facecolor('#1e293b')
        ax.set_facecolor('#1e293b')
        plt.tight_layout()
        st.pyplot(fig)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div style="font-weight: 600; margin-bottom: 16px;">Average Scores</div>', unsafe_allow_html=True)
        
        avg_wm = sum(r['watermark_confidence'] for r in history) / total
        avg_ai = sum(r['deepfake_confidence'] for r in history) / total
        
        st.markdown(f'''
        <div style="margin-bottom: 24px;">
            <div style="color: var(--muted); font-size: 0.875rem; text-transform: uppercase;">Average Watermark Confidence</div>
            <div style="font-size: 2rem; font-weight: 700; color: var(--accent);">{avg_wm*100:.1f}%</div>
        </div>
        <div style="margin-bottom: 24px;">
            <div style="color: var(--muted); font-size: 0.875rem; text-transform: uppercase;">Average AI Detection Confidence</div>
            <div style="font-size: 2rem; font-weight: 700; color: var(--accent);">{avg_ai*100:.1f}%</div>
        </div>
        <div style="margin-bottom: 12px;">
            <div style="color: var(--muted); font-size: 0.875rem; text-transform: uppercase;">Total Analyses Run</div>
            <div style="font-size: 2rem; font-weight: 700; color: var(--text);">{total} operations</div>
        </div>
        ''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

def render_architecture():
    st.markdown('<div class="section-header">System Architecture</div>', unsafe_allow_html=True)
    st.markdown('''
    <div class="card">
        <h3 style="margin-top: 0; margin-bottom: 16px; color: var(--accent);">Processing Pipeline</h3>
        <p style="color: var(--text); line-height: 1.8; margin-bottom: 0;">
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
st.sidebar.markdown('<h2 style="color: var(--text); text-align: center; margin-bottom: 32px; margin-top: 16px;">Navigation</h2>', unsafe_allow_html=True)
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
