"""
decision.py

Decision engine for the Aawaaz authentication framework.
This module processes the scores from the deepfake detector and the watermark 
verification steps to compute a final authenticity risk score and generate a comprehensive verdict.
"""

def generate_verdict(deepfake_label: str, deepfake_score: float, watermark_confidence: float) -> dict:
    """
    Computes a final risk score and verdict based on AI classification and watermark presence.
    
    Args:
        deepfake_label (str): The label predicted by the deepfake model (e.g., 'real', 'fake').
        deepfake_score (float): The confidence probability (0.0 to 1.0) of the target label.
        watermark_confidence (float): The confidence probability (0.0 to 1.0) that a valid 
                                      watermark is present in the audio.
                                      
    Returns:
        dict: A dictionary containing the final verdict, risk level, aggregated risk score,
              and the individual components for AI and watermark risk.
    """
    
    # 1. Normalize the deepfake label for consistent comparison
    normalized_label = deepfake_label.strip().lower()
    
    # 2. Compute the AI Risk factor (0.0 to 1.0)
    # The score from the model reflects confidence in the predicted label.
    # If the model strongly predicts 'fake', ai_risk is high.
    # If the model strongly predicts 'real', ai_risk is low.
    if normalized_label == "fake":
        ai_risk = deepfake_score
    elif normalized_label == "real":
        ai_risk = 1.0 - deepfake_score
    else:
        # Fallback for unexpected labels
        ai_risk = deepfake_score
        
    # 3. Compute Watermark Risk factor (0.0 to 1.0)
    # A high confidence of a watermark means low risk of tampering/forgery.
    watermark_risk = 1.0 - watermark_confidence
    
    # 4. Compute Final Risk Score (0 to 100 scale)
    # Weighted calculation: 70% weight to AI prediction, 30% weight to watermark absence
    raw_risk_score = (ai_risk * 0.7 + watermark_risk * 0.3) * 100
    risk_score = round(raw_risk_score, 2)

    # 5. Determine the appropriate verdict and explanation based on thresholds
    if risk_score >= 75:
        final_verdict = "Synthetic or Heavily Tampered Audio"
        risk_level = "High"
        explanation = "AI model indicates strong deepfake characteristics and/or watermark authentication failed."
    elif risk_score >= 45:
        final_verdict = "Suspicious Audio"
        risk_level = "Medium"
        explanation = "Partial inconsistencies detected between AI classification and watermark verification."
    else:
        final_verdict = "Likely Authentic Audio"
        risk_level = "Low"
        explanation = "AI classification and watermark verification suggest authenticity."
        
    # 6. Construct and return the result dictionary
    return {
        "final_verdict": final_verdict,
        "risk_level": risk_level,
        "risk_score": risk_score,
        "explanation": explanation,
        "ai_risk_component": round(ai_risk * 100, 2),
        "watermark_risk_component": round(watermark_risk * 100, 2)
    }
