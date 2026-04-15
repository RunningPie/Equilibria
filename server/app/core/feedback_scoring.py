"""
Modul NLP Feedback Quality Scoring - Tech Specs v4.2 Bagian 6.6 (Revisi)

Implementasi weighted keyword matching untuk assessment kualitas peer review feedback.
Berdasarkan Kerman et al. (2024) cognitive features dan ACM Bloom's for Computing (2023).
"""

from typing import List


# Bagian 6.6: NLP Feedback Quality Scoring

# 1. Identification: Problem localization & error detection
# Sumber: Kerman et al. (2024) - Cognitive Identification Feature
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
# Sumber: Kerman et al. (2024) - Cognitive Justification Feature (BARU)
JUSTIFICATION_KEYWORDS = [
    # Indonesian
    'karena', 'sebab', 'akibat', 'sehingga', 'maka', 'akibatnya',
    'alasan', 'penyebab', 'mengapa', 'due to', 'oleh karena',
    # English
    'because', 'therefore', 'thus', 'hence', 'due to', 'leads to',
    'causes', 'reason', 'why', 'since', 'as a result'
]

# 3. Constructive: Actionable Recommendations & Plans
# Sumber: Kerman et al. (2024) - Constructive Feature
CONSTRUCTIVE_KEYWORDS = [
    # Indonesian
    'seharusnya', 'coba', 'gunakan', 'ubah', 'perbaiki', 'tambahkan',
    'hapus', 'pindahkan', 'solusi', 'sarankan', 'usulkan', 'ganti',
    # English
    'should', 'try', 'use', 'change', 'fix', 'add', 'remove', 'move',
    'consider', 'recommend', 'suggest', 'replace', 'update'
]

# 4. Bloom's Higher-Order Verbs (Quality Bonus)
# Sumber: ACM Bloom's for Computing (2023) - Evaluating & Analyzing Levels
BLOOMS_HIGH_ORDER_KEYWORDS = [
    # Indonesian
    'debug', 'optimize', 'validasi', 'trace', 'telusuri', 'analisis',
    'evaluasi', 'refactor', 'struktur ulang', 'prioritas', 'bukti',
    # English
    'debug', 'optimize', 'validate', 'trace', 'analyze', 'evaluate',
    'refactor', 'prioritize', 'prove', 'verify', 'test', 'secure'
]


def _contains_keyword(text: str, keywords: List[str]) -> bool:
    """Periksa apakah ada keyword dalam teks (case-insensitive)."""
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)


def _count_keywords(text: str, keywords: List[str]) -> int:
    """Hitung berapa banyak keyword yang muncul dalam teks (case-insensitive)."""
    text_lower = text.lower()
    count = 0
    for kw in keywords:
        count += text_lower.count(kw.lower())
    return count


def calculate_system_score(feedback_text: str) -> float:
    """
    Hitung feedback quality score pakai weighted keyword matching.

    Algoritma (Bagian 6.6 revisi):
    - Tier 1: Structural Quality (weighted components)
      - Identification (0.3): Problem localization & error detection
      - Justification (0.4): Reasoning & causal explanation (bobot tertinggi)
      - Constructive (0.3): Actionable recommendations
    - Tier 2: Cognitive Depth Bonus (Bloom's Taxonomy)
      - Bonus maksimal 0.2 untuk higher-order verbs

    Args:
        feedback_text: Teks feedback dari reviewer

    Returns:
        Quality score dalam rentang [0.0, 1.0]
    """
    # --- Pre-processing ---
    if not feedback_text or len(feedback_text.strip()) < 15:
        return 0.1  # Terlalu pendek untuk bermakna

    text = feedback_text.strip()

    # --- Tier 1: Structural Quality (Weighted Components) ---
    # Berdasarkan temuan Kerman et al. (2024) tentang predictive features

    has_identification = _contains_keyword(text, IDENTIFICATION_KEYWORDS)
    has_justification = _contains_keyword(text, JUSTIFICATION_KEYWORDS)
    has_constructive = _contains_keyword(text, CONSTRUCTIVE_KEYWORDS)

    # Weighted Sum: Justification dengan bobot tertinggi sesuai prediktor sukses Kerman
    structural_score = 0.0
    if has_identification:
        structural_score += 0.3
    if has_justification:
        structural_score += 0.4
    if has_constructive:
        structural_score += 0.3

    # --- Tier 2: Cognitive Depth Bonus (Bloom's Taxonomy) ---
    # Berdasarkan ACM Bloom's for Computing (2023) Higher-Order Verbs

    high_order_count = _count_keywords(text, BLOOMS_HIGH_ORDER_KEYWORDS)

    depth_bonus = 0.0
    if high_order_count > 0:
        # Batasi bonus maksimal 0.2 untuk mencegah mengaburkan structural quality
        depth_bonus = min(0.2, high_order_count * 0.1)

    # --- Final Calculation ---
    final_score = structural_score + depth_bonus

    # Pastikan score tetap dalam rentang [0.0, 1.0]
    return max(0.0, min(1.0, final_score))
