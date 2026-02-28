import os
import tempfile
import streamlit as st

from detector import DeepfakeDetector
from watermark import detect_watermark, embed_watermark
from decision import generate_verdict


# ---------------------------
# Page Configuration
# ---------------------------

st.set_page_config(
    page_title="VoiceGuard - Audio Authenticity Analyzer",
    layout="centered"
)

st.title("VoiceGuard")
st.subheader("Dual-Layer Audio Deepfake & Watermark Verification System")

st.write(
    "VoiceGuard combines AI-based deepfake classification with spectral "
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
# Mode Selection
# ---------------------------

app_mode = st.radio(
    "Select Mode",
    options=["Verify Audio", "Embed Watermark"],
    horizontal=True
)

st.divider()


# ---------------------------
# File Upload
# ---------------------------

uploaded_file = st.file_uploader(
    "Upload Audio File" if app_mode == "Verify Audio" else "Upload Original Audio to Watermark",
    type=["wav", "mp3"],
    accept_multiple_files=False
)

if uploaded_file is None:
    st.info("Please upload a WAV or MP3 file to begin.")
    st.stop()


# ---------------------------
# Save Temp File Safely
# ---------------------------

file_suffix = os.path.splitext(uploaded_file.name)[1]

with tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix) as tmp_file:
    tmp_file.write(uploaded_file.getvalue())
    tmp_filepath = tmp_file.name


# ==========================================
# MODE 1: Verify Audio
# ==========================================

if app_mode == "Verify Audio":
    st.audio(uploaded_file, format=f"audio/{file_suffix.strip('.')}")

    if st.button("Analyze Audio"):
        with st.spinner("Running deepfake detection and watermark verification..."):
            try:
                # Deepfake Detection
                deepfake_label, deepfake_confidence = detector_model.detect(
                    uploaded_file.getvalue(),
                    suffix=file_suffix
                )

                # Watermark Detection
                watermark_confidence = detect_watermark(tmp_filepath)

                # Decision Engine
                verdict_results = generate_verdict(
                    deepfake_label,
                    deepfake_confidence,
                    watermark_confidence
                )

            except Exception as e:
                st.error(f"Analysis failed: {e}")
                if os.path.exists(tmp_filepath):
                    os.remove(tmp_filepath)
                st.stop()

        # ---------------------------
        # Display Results
        # ---------------------------

        st.divider()

        # --- AI Deepfake Analysis ---
        st.header("AI Deepfake Analysis")
        st.write(f"**Predicted Label:** {deepfake_label.capitalize()}")
        st.write(f"**Model Confidence:** {deepfake_confidence * 100:.2f}%")

        ai_risk_component = verdict_results.get("ai_risk_component", 0.0) / 100
        st.progress(ai_risk_component)
        st.caption(f"AI Risk Contribution: {verdict_results.get('ai_risk_component', 0.0)}%")

        st.divider()

        # --- Watermark Verification ---
        st.header("Watermark Verification")
        st.write(f"**Watermark Confidence:** {watermark_confidence * 100:.2f}%")

        watermark_risk_component = verdict_results.get("watermark_risk_component", 0.0) / 100
        st.progress(watermark_risk_component)
        st.caption(f"Watermark Risk Contribution: {verdict_results.get('watermark_risk_component', 0.0)}%")

        st.divider()

        # --- Final Risk Assessment ---
        st.header("Final Risk Assessment")

        final_verdict = verdict_results.get("final_verdict", "Unknown")
        risk_level = verdict_results.get("risk_level", "Unknown")
        risk_score = verdict_results.get("risk_score", 0.0)
        explanation = verdict_results.get("explanation", "")

        st.markdown(f"## {final_verdict}")
        st.write(f"**Risk Level:** {risk_level}")
        st.write(f"**Aggregated Risk Score:** {risk_score}%")

        st.progress(risk_score / 100)

        if risk_level == "High":
            st.error("Overall Status: High Risk")
        elif risk_level == "Medium":
            st.warning("Overall Status: Medium Risk")
        elif risk_level == "Low":
            st.success("Overall Status: Low Risk")
        else:
            st.info("Overall Status: Undetermined")

        st.divider()

        # --- Cross-Layer Consistency Analysis ---
        st.header("Cross-Layer Consistency Analysis")

        ai_val = verdict_results.get("ai_risk_component", 0.0)
        wm_val = verdict_results.get("watermark_risk_component", 0.0)

        if ai_val < 30 and wm_val > 60:
            st.warning("AI model suggests authenticity, but watermark verification failed. Possible unauthorized recording.")
        elif ai_val > 60 and wm_val < 30:
            st.warning("Watermark is present but AI model indicates synthetic characteristics. Possible watermark injection attack.")
        elif ai_val >= 60 and wm_val >= 60:
            st.error("Both AI and watermark layers indicate high risk.")
        elif ai_val <= 30 and wm_val <= 30:
            st.success("AI and watermark layers are consistent and indicate authenticity.")
        else:
            st.info("No significant cross-layer conflict detected.")

        st.divider()

        # --- Explanation ---
        st.header("System Explanation")
        st.info(explanation)


# ==========================================
# MODE 2: Embed Watermark
# ==========================================

elif app_mode == "Embed Watermark":
    
    st.write("### Original Audio")
    st.audio(uploaded_file, format=f"audio/{file_suffix.strip('.')}")

    if st.button("Generate Watermarked Audio"):
        with st.spinner("Embedding spectral watermark..."):
            
            # Create a path for the output file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as out_tmp:
                output_filepath = out_tmp.name

            try:
                # Embed the watermark
                embed_watermark(tmp_filepath, output_filepath)
                
                st.success("Watermark successfully embedded!")
                
                st.write("### Watermarked Audio")
                st.audio(output_filepath, format="audio/wav")
                
                # Provide a download button
                with open(output_filepath, "rb") as f:
                    audio_bytes = f.read()
                    
                st.download_button(
                    label="Download Watermarked Audio",
                    data=audio_bytes,
                    file_name="watermarked_audio.wav",
                    mime="audio/wav"
                )
                
            except Exception as e:
                st.error(f"Failed to embed watermark: {e}")
                
            finally:
                # Cleanup the output temp file
                if os.path.exists(output_filepath):
                    try:
                        os.remove(output_filepath)
                    except OSError:
                        pass

# Cleanup the uploaded input temp file
if os.path.exists(tmp_filepath):
    try:
        os.remove(tmp_filepath)
    except OSError:
        pass