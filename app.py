# import os
# import tempfile

# import streamlit as st

# from detector import DeepfakeDetector
# from watermark import detect_watermark
# from decision import generate_verdict

# st.set_page_config(
#     page_title="VoiceGuard - Audio Authenticity Analyzer",
#     layout="centered"
# )

# st.title("VoiceGuard")
# st.subheader("Dual-Layer Audio Deepfake & Watermark Verification System")
# st.write(
#     "This system combines AI-based deepfake classification with spectral watermark "
#     "verification to analyze audio authenticity."
# )

# @st.cache_resource
# def load_model() -> DeepfakeDetector:
#     """
#     Initializes and caches the DeepfakeDetector to prevent reloading
#     the model on every Streamlit rerun.
#     """
#     return DeepfakeDetector()

# try:
#     detector_model = load_model()
# except Exception as e:
#     st.error(f"Failed to initialize the deepfake detection model: {e}")
#     st.stop()

# uploaded_file = st.file_uploader(
#     "Upload Audio File",
#     type=["wav", "mp3"],
#     accept_multiple_files=False
# )

# if uploaded_file is None:
#     st.info("Please upload an audio file to begin analysis.")
#     st.stop()

# # Safely save the uploaded file to a temporary location
# file_suffix = os.path.splitext(uploaded_file.name)[1]
# with tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix) as tmp_file:
#     tmp_file.write(uploaded_file.getvalue())
#     tmp_filepath = tmp_file.name

# st.audio(uploaded_file, format=f"audio/{file_suffix.strip('.')}")

# if st.button("Analyze Audio"):
#     with st.spinner("Analyzing audio..."):
#         try:
#             # 1. Deepfake Detection
#             deepfake_label, deepfake_confidence = detector_model.detect(
#                 uploaded_file.getvalue(),
#                 suffix=file_suffix
#             )

#             # 2. Watermark Verification
#             watermark_confidence = detect_watermark(tmp_filepath)

#             # 3. Decision Logic
#             verdict_results = generate_verdict(
#                 deepfake_label,
#                 deepfake_confidence,
#                 watermark_confidence
#             )

#             # Display Results
#             st.divider()
            
#             # --- Section A: AI Deepfake Analysis ---
#             st.header("AI Deepfake Analysis")
#             st.write(f"**Predicted Label:** {deepfake_label.capitalize()}")
#             st.write(f"**Confidence:** {deepfake_confidence * 100:.2f}%")
#             st.progress(deepfake_confidence)
            
#             st.divider()

#             # --- Section B: Watermark Verification ---
#             st.header("Watermark Verification")
#             st.write(f"**Watermark Detection Confidence:** {watermark_confidence * 100:.2f}%")
#             st.progress(watermark_confidence)
            
#             st.divider()

#             # --- Section C & D: Final Risk Assessment & Explanation ---
#             st.header("Final Risk Assessment")
            
#             risk_level = verdict_results.get("risk_level", "Unknown")
#             final_verdict = verdict_results.get("final_verdict", "Unknown Verdict")
#             risk_score = verdict_results.get("risk_score", 0.0)
#             explanation = verdict_results.get("explanation", "No explanation provided.")

#             st.write(f"### {final_verdict}")
#             st.write(f"**Risk Level:** {risk_level}")
#             st.write(f"**Risk Score:** {risk_score}%")

#             if risk_level == "High":
#                 st.error("Status: High Risk")
#             elif risk_level == "Medium":
#                 st.warning("Status: Medium Risk")
#             elif risk_level == "Low":
#                 st.success("Status: Low Risk")
#             else:
#                 st.info(f"Status: {risk_level}")

#             st.info(explanation)
            
#         except Exception as e:
#             st.error(f"An error occurred during analysis: {e}")

# # Cleanup temporary file
# if os.path.exists(tmp_filepath):
#     try:
#         os.remove(tmp_filepath)
#     except OSError:
#         pass


import os
import tempfile
import streamlit as st

from detector import DeepfakeDetector
from watermark import detect_watermark
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
# File Upload
# ---------------------------

uploaded_file = st.file_uploader(
    "Upload Audio File",
    type=["wav", "mp3"],
    accept_multiple_files=False
)

if uploaded_file is None:
    st.info("Please upload a WAV or MP3 file to begin analysis.")
    st.stop()


# ---------------------------
# Save Temp File Safely
# ---------------------------

file_suffix = os.path.splitext(uploaded_file.name)[1]

with tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix) as tmp_file:
    tmp_file.write(uploaded_file.getvalue())
    tmp_filepath = tmp_file.name


# ---------------------------
# Audio Playback
# ---------------------------

st.audio(uploaded_file, format=f"audio/{file_suffix.strip('.')}")


# ---------------------------
# Analysis Button
# ---------------------------

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

    if ai_risk_component < 30 and watermark_risk_component > 60:
        st.warning("AI model suggests authenticity, but watermark verification failed. Possible unauthorized recording.")
    elif ai_risk_component > 60 and watermark_risk_component < 30:
        st.warning("Watermark is present but AI model indicates synthetic characteristics. Possible watermark injection attack.")
    elif ai_risk_component >= 60 and watermark_risk_component >= 60:
        st.error("Both AI and watermark layers indicate high risk.")
    elif ai_risk_component <= 30 and watermark_risk_component <= 30:
        st.success("AI and watermark layers are consistent and indicate authenticity.")
    else:
        st.info("No significant cross-layer conflict detected.")

    st.divider()

    # --- Explanation ---
    st.header("System Explanation")
    st.info(explanation)

    # Cleanup temp file after analysis
    if os.path.exists(tmp_filepath):
        os.remove(tmp_filepath)