def generate_verdict(deepfake_label: str, deepfake_score: float, watermark_confidence: float) -> dict:
    normalized_label = deepfake_label.strip().lower()
    if normalized_label == 'fake':
        ai_risk = deepfake_score
    elif normalized_label == 'real':
        ai_risk = 1.0 - deepfake_score
    else:
        ai_risk = deepfake_score
    watermark_risk = 1.0 - watermark_confidence
    if normalized_label == 'fake' and deepfake_score >= 0.9:
        return {'final_verdict': 'Synthetic Audio', 'risk_level': 'High', 'risk_score': round(ai_risk * 100, 2), 'explanation': 'AI model strongly indicates synthetic voice. Watermark presence cannot override high-confidence AI detection.', 'ai_risk_component': round(ai_risk * 100, 2), 'watermark_risk_component': round(watermark_risk * 100, 2), 'conflict_type': 'AI Override'}
    if normalized_label == 'fake' and deepfake_score >= 0.8 and (watermark_confidence >= 0.8):
        return {'final_verdict': 'Watermark Injection Suspected', 'risk_level': 'High', 'risk_score': round((ai_risk * 0.8 + watermark_risk * 0.2) * 100, 2), 'explanation': 'Synthetic voice detected with valid watermark. Possible post-generation watermark embedding attack.', 'ai_risk_component': round(ai_risk * 100, 2), 'watermark_risk_component': round(watermark_risk * 100, 2), 'conflict_type': 'Injection Suspected'}
    if normalized_label == 'real' and deepfake_score >= 0.8 and (watermark_confidence < 0.3):
        return {'final_verdict': 'Unauthenticated Audio', 'risk_level': 'Medium', 'risk_score': round((ai_risk * 0.5 + watermark_risk * 0.5) * 100, 2), 'explanation': 'Audio appears human-generated but lacks expected watermark authentication.', 'ai_risk_component': round(ai_risk * 100, 2), 'watermark_risk_component': round(watermark_risk * 100, 2), 'conflict_type': 'Missing Watermark'}
    raw_risk_score = (ai_risk * 0.7 + watermark_risk * 0.3) * 100
    risk_score = round(raw_risk_score, 2)
    if risk_score >= 75:
        final_verdict = 'Synthetic or Heavily Tampered Audio'
        risk_level = 'High'
        explanation = 'AI model and watermark analysis indicate high tampering probability.'
        conflict_type = 'Strong Agreement - Synthetic'
    elif risk_score >= 45:
        final_verdict = 'Suspicious Audio'
        risk_level = 'Medium'
        explanation = 'Partial inconsistencies detected between AI classification and watermark verification.'
        conflict_type = 'Partial Inconsistency'
    else:
        final_verdict = 'Likely Authentic Audio'
        risk_level = 'Low'
        explanation = 'AI classification and watermark verification are consistent and indicate authenticity.'
        conflict_type = 'Strong Agreement - Authentic'
    return {'final_verdict': final_verdict, 'risk_level': risk_level, 'risk_score': risk_score, 'explanation': explanation, 'ai_risk_component': round(ai_risk * 100, 2), 'watermark_risk_component': round(watermark_risk * 100, 2), 'conflict_type': conflict_type}
