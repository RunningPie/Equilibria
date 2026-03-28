"""
NLP Feedback Quality Scoring Module - Tech Specs v4.2 Section 6.6 (Revised)

Implements weighted keyword matching for peer review feedback quality assessment.
Based on Kerman et al. (2024) cognitive features and ACM Bloom's for Computing (2023).
"""

from typing import List


# Section 6.6: NLP Feedback Quality Scoring

# 1. Identification: Problem localization & error detection
# Source: Kerman et al. (2024) - Cognitive Identification Feature
IDENTIFICATION_KEYWORDS = [
    # Indonesian
    'error', 'salah', 'bug', 'masalah', 'issue', 'kurang', 'hilang',
    'tidak muncul', 'tidak berjalan', 'kosong', 'null', 'gagal',
    'exception', 'typo', 'keliru', 'cacat', 'anomali',
    # English
    'missing', 'wrong', 'incorrect', 'failed', 'issue', 'problem',
    'undefined', 'empty', 'invalid'
]

# 2. Justification: Reasoning & Causal Explanation
# Source: Kerman et al. (2024) - Cognitive Justification Feature (NEW)
JUSTIFICATION_KEYWORDS = [
    # Indonesian
    'karena', 'sebab', 'akibat', 'sehingga', 'maka', 'akibatnya',
    'alasan', 'penyebab', 'mengapa', 'due to', 'oleh karena',
    # English
    'because', 'therefore', 'thus', 'hence', 'due to', 'leads to',
    'causes', 'reason', 'why', 'since', 'as a result'
]

# 3. Constructive: Actionable Recommendations & Plans
# Source: Kerman et al. (2024) - Constructive Feature
CONSTRUCTIVE_KEYWORDS = [
    # Indonesian
    'seharusnya', 'coba', 'gunakan', 'ubah', 'perbaiki', 'tambahkan',
    'hapus', 'pindahkan', 'solusi', 'sarankan', 'usulkan', 'ganti',
    # English
    'should', 'try', 'use', 'change', 'fix', 'add', 'remove', 'move',
    'consider', 'recommend', 'suggest', 'replace', 'update'
]

# 4. Bloom's Higher-Order Verbs (Quality Bonus)
# Source: ACM Bloom's for Computing (2023) - Evaluating & Analyzing Levels
BLOOMS_HIGH_ORDER_KEYWORDS = [
    # Indonesian
    'debug', 'optimize', 'validasi', 'trace', 'telusuri', 'analisis',
    'evaluasi', 'refactor', 'struktur ulang', 'prioritas', 'bukti',
    # English
    'debug', 'optimize', 'validate', 'trace', 'analyze', 'evaluate',
    'refactor', 'prioritize', 'prove', 'verify', 'test', 'secure'
]


def _contains_keyword(text: str, keywords: List[str]) -> bool:
    """Check if any keyword exists in the text (case-insensitive)."""
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)


def _count_keywords(text: str, keywords: List[str]) -> int:
    """Count how many keywords appear in the text (case-insensitive)."""
    text_lower = text.lower()
    count = 0
    for kw in keywords:
        count += text_lower.count(kw.lower())
    return count


def calculate_system_score(feedback_text: str) -> float:
    """
    Calculate feedback quality score using weighted keyword matching.

    Algorithm (Section 6.6 revised):
    - Tier 1: Structural Quality (weighted components)
      - Identification (0.3): Problem localization & error detection
      - Justification (0.4): Reasoning & causal explanation (highest weight)
      - Constructive (0.3): Actionable recommendations
    - Tier 2: Cognitive Depth Bonus (Bloom's Taxonomy)
      - Up to 0.2 bonus for higher-order verbs

    Args:
        feedback_text: The reviewer's feedback text

    Returns:
        Quality score in range [0.0, 1.0]
    """
    # --- Pre-processing ---
    if not feedback_text or len(feedback_text.strip()) < 15:
        return 0.1  # Too short to be meaningful

    text = feedback_text.strip()

    # --- Tier 1: Structural Quality (Weighted Components) ---
    # Based on Kerman et al. (2024) findings on predictive features

    has_identification = _contains_keyword(text, IDENTIFICATION_KEYWORDS)
    has_justification = _contains_keyword(text, JUSTIFICATION_KEYWORDS)
    has_constructive = _contains_keyword(text, CONSTRUCTIVE_KEYWORDS)

    # Weighted Sum: Justification weighted highest as per Kerman's success predictors
    structural_score = 0.0
    if has_identification:
        structural_score += 0.3
    if has_justification:
        structural_score += 0.4
    if has_constructive:
        structural_score += 0.3

    # --- Tier 2: Cognitive Depth Bonus (Bloom's Taxonomy) ---
    # Based on ACM Bloom's for Computing (2023) Higher-Order Verbs

    high_order_count = _count_keywords(text, BLOOMS_HIGH_ORDER_KEYWORDS)

    depth_bonus = 0.0
    if high_order_count > 0:
        # Cap bonus at 0.2 to prevent overshadowing structural quality
        depth_bonus = min(0.2, high_order_count * 0.1)

    # --- Final Calculation ---
    final_score = structural_score + depth_bonus

    # Ensure score stays within [0.0, 1.0] range
    return max(0.0, min(1.0, final_score))
