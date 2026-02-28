import os
import tempfile
import streamlit as st
import matplotlib.pyplot as plt

from detector import DeepfakeDetector
from watermark import detect_watermark, embed_watermark
from decision import generate_verdict
from database import init_db, save_analysis, fetch_all_history, clear_history


# ---------------------------
# Initialization & Setup
# ---------------------------

# Initialize the persistent SQLite database
init_db()

# Page Configuration
st.set_page_config(
    page_title="Aawaaz - Audio Authenticity Analyzer",
    layout="centered"
)


# ---------------------------
# UI Header
# ---------------------------

st.title("Aawaaz")
st.subheader("Dual-Layer Audio Deepfake & Watermark Verification System")

st.write(
    "Aawaaz combines AI-based deepfake classification with spectral "
    "watermark verification to evaluate audio authenticity using a "
    "layered risk assessment framework."
)


# ---------------------------
# Model Initialization
# ---------------------------

@st.cache_resource
def load_model() -> DeepfakeDetector:
    return DeepfakeDetector()

try:
    detector_model = load_model()
except Exception as e:
    st.error(f"Model initialization failed: {e}")
    st.stop()


# ---------------------------
# File Upload
# ---------------------------

uploaded_file = st.file_uploader(
    "Upload Audio File (WAV/MP3)",
    type=["wav", "mp3"],
    accept_multiple_files=False
)

if uploaded_file is None:
    st.info("Please upload an audio file to begin analysis.")
else:
    file_suffix = os.path.splitext(uploaded_file.name)[1]
    original_filename = uploaded_file.name
    
    # Safely write the uploaded bytes to a temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_filepath = tmp_file.name

    st.write("### Original Audio")
    st.audio(uploaded_file, format=f"audio/{file_suffix.strip('.')}")
    
    # Provide a simple checkbox for active watermark embedding
    embed_wm = st.checkbox("Embed watermark before analysis")
    
    analysis_filepath = tmp_filepath
    watermarked_tmp = None

    if embed_wm:
        with st.spinner("Embedding spectral watermark..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as wt_file:
                watermarked_tmp = wt_file.name
                
            try:
                embed_watermark(tmp_filepath, watermarked_tmp)
                st.success("Watermark successfully embedded.")
                st.write("### Watermarked Audio")
                st.audio(watermarked_tmp, format="audio/wav")
                
                # Provide download for the watermarked version
                with open(watermarked_tmp, "rb") as f:
                    wm_bytes = f.read()
                st.download_button(
                    label="Download Watermarked Audio",
                    data=wm_bytes,
                    file_name=f"watermarked_{original_filename}",
                    mime="audio/wav"
                )
                
                # If checked, we analyze the newly watermarked file
                analysis_filepath = watermarked_tmp
            except Exception as e:
                st.error(f"Watermark embedding failed: {e}")
                # Fallback to the original file for analysis if it fails
                analysis_filepath = tmp_filepath

    # ---------------------------
    # Core Analysis Execution
    # ---------------------------
    
    if st.button("Analyze Audio"):
        with st.spinner("Processing deepfake classification and spectral watermark..."):
            try:
                # To feed Hugging Face, we read the bytes of whichever file we are analyzing
                with open(analysis_filepath, "rb") as af:
                    analysis_bytes = af.read()
                    analysis_suffix = os.path.splitext(analysis_filepath)[1]

                # 1. Deepfake Detection
                deepfake_label, deepfake_confidence = detector_model.detect(
                    analysis_bytes,
                    suffix=analysis_suffix
                )

                # 2. Watermark Detection
                watermark_confidence = detect_watermark(analysis_filepath)

                # 3. Decision Logic
                verdict_results = generate_verdict(
                    deepfake_label,
                    deepfake_confidence,
                    watermark_confidence
                )
                
                # 4. Save to Persistent DB
                save_analysis(
                    filename=original_filename,
                    deepfake_label=deepfake_label,
                    deepfake_confidence=deepfake_confidence,
                    watermark_confidence=watermark_confidence,
                    risk_score=verdict_results.get("risk_score", 0.0),
                    final_verdict=verdict_results.get("final_verdict", "Unknown"),
                    risk_level=verdict_results.get("risk_level", "Unknown")
                )

            except Exception as e:
                st.error(f"Analysis failed: {e}")
                st.stop()

        # ---------------------------
        # Display Current Results
        # ---------------------------
        st.divider()
        st.header("Analysis Results")
        
        # Determine risk values
        ai_val = verdict_results.get("ai_risk_component", 0.0)
        wm_val = verdict_results.get("watermark_risk_component", 0.0)
        risk_score = verdict_results.get("risk_score", 0.0)
        explanation = verdict_results.get("explanation", "")
        risk_level = verdict_results.get("risk_level", "Unknown")
        final_verdict = verdict_results.get("final_verdict", "Unknown")

        col1, col2 = st.columns(2)
        
        with col1:
            st.write("#### AI Deepfake Predictor")
            st.write(f"Label: **{deepfake_label.capitalize()}**")
            st.write(f"Model Confidence: **{deepfake_confidence * 100:.2f}%**")
            st.progress(ai_val / 100)
            
        with col2:
            st.write("#### Watermark Verification")
            st.write(f"Detection Confidence: **{watermark_confidence * 100:.2f}%**")
            st.progress(wm_val / 100)

        st.write("---")
        st.markdown(f"### {final_verdict}")
        st.write(f"**Aggregated Risk Score:** {risk_score}%")
        st.write(f"**Risk Level:** {risk_level}")
        st.progress(risk_score / 100)
        
        if risk_level == "High":
            st.error("Status: High Risk")
        elif risk_level == "Medium":
            st.warning("Status: Medium Risk")
        elif risk_level == "Low":
            st.success("Status: Low Risk")

        st.info(explanation)
        
        # ---------------------------
        # Cross-Layer Consistency
        # ---------------------------
        st.write("#### Cross-Layer Consistency Analysis")

        # Normalize components for consistency matching 
        # Assume AI says fake if ai_val is high
        if ai_val > 60 and watermark_confidence >= 0.7:
            st.warning("Watermark is present but AI model indicates synthetic characteristics. Possible watermark injection attack.")
        elif ai_val < 40 and watermark_confidence < 0.3:
             st.warning("Unauthenticated authentic audio. AI model suggests authenticity, but watermark verification failed. Possible unauthorized recording.")
        elif ai_val > 60 and watermark_confidence < 0.3:
            st.error("Both AI and watermark layers agree: audio is highly suspicious.")
        elif ai_val < 40 and watermark_confidence >= 0.7:
            st.success("Both AI and watermark layers are consistent and indicate authenticity.")
        else:
             st.info("No definitive cross-layer conflict detected.")
             
        # Generate Text Report
        timestamp = verdict_results.get('timestamp', 'Now')
        report_text = f'''Aawaaz Analysis Report
------------------------
Filename: {original_filename}
Timestamp: {timestamp}

AI Prediction: {deepfake_label.capitalize()} ({deepfake_confidence * 100:.2f}% confidence)
Watermark Confidence: {watermark_confidence * 100:.2f}%

Aggregated Risk Score: {risk_score}%
Risk Level: {risk_level}
Final Verdict: {final_verdict}

System Explanation:
{explanation}
'''     
        st.download_button(
             label="Download Text Report",
             data=report_text,
             file_name=f"report_{original_filename}.txt",
             mime="text/plain"
        )
        
    # Cleanup temp files when done processing this cycle
    if os.path.exists(tmp_filepath):
        os.remove(tmp_filepath)
    if watermarked_tmp and os.path.exists(watermarked_tmp):
        os.remove(watermarked_tmp)


# ---------------------------
# Processing History & Trends
# ---------------------------

st.divider()
st.header("Processing History")

history_records = fetch_all_history()

if not history_records:
    st.write("No historical data available. Run an analysis to generate history.")
else:
    # Build dataframe-ready list
    df_data = []
    for rec in history_records:
        df_data.append({
            "ID": rec["id"],
            "Filename": rec["filename"],
            "Time": rec["timestamp"],
            "AI Label": rec["deepfake_label"],
            "AI Conf": round(rec["deepfake_confidence"], 3),
            "WM Conf": round(rec["watermark_confidence"], 3),
            "Risk Score": rec["risk_score"],
            "Verdict": rec["final_verdict"]
        })
        
    st.dataframe(df_data, use_container_width=True)
    
    st.write("---")
    st.warning("This action will permanently delete all analysis history.")
    
    if "confirm_clear" not in st.session_state:
        st.session_state.confirm_clear = False
        
    def toggle_confirm():
        st.session_state.confirm_clear = not st.session_state.confirm_clear
        
    st.checkbox("I understand, proceed to clear", value=st.session_state.confirm_clear, on_change=toggle_confirm, key="chk_clear")
    
    if st.session_state.confirm_clear:
        if st.button("Clear History", type="primary"):
            clear_history()
            st.session_state.confirm_clear = False
            st.success("History successfully cleared.")
            st.rerun()
    
    # ---------------------------
    # Confidence Trend Chart
    # ---------------------------
    st.write("#### Recent Risk Score Trends (Last 10)")
    # Grab up to 10 latest, sort by chronological order for plotting
    recent_records = history_records[:10]
    recent_records.reverse()
    
    if len(recent_records) > 1:
        times = [r["timestamp"].split(" ")[1] for r in recent_records] # Extract just time for cleaner x-axis
        scores = [r["risk_score"] for r in recent_records]
        
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(times, scores, marker='o', linestyle='-', linewidth=2)
        ax.set_xlabel("Time")
        ax.set_ylabel("Risk Score")
        ax.set_title("Aggregated Risk Score over Last 10 Analyses")
        ax.grid(True, linestyle='--', alpha=0.7)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        st.pyplot(fig)
    else:
        st.write("*Need at least 2 historical records to plot trends.*")

# ---------------------------
# Architecture Diagram
# ---------------------------
st.divider()
with st.expander("System Architecture"):
    st.markdown("""
    **Audio Upload**
    ↓
    **Resampling (librosa)**
    ↓
    **Parallel Processing:**
    * **Deepfake Detection** (`wav2vec2`)
    * **Watermark Detection** (FFT)
    ↓
    **Risk Engine**
    ↓
    **Final Verdict**
    """)
