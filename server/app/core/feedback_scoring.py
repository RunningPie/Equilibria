"""
Modul NLP Feedback Quality Scoring

Pipeline:
1. Gibberish & Length Check (Prefilter)
2. Domain Relevance Check (Sentence-level)
3. Word-Level Semantic (Feature Scoring)
"""

import re
from typing import List, Dict
import numpy as np
from fastembed import TextEmbedding

# Model Init
MODEL_NAME = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
model = TextEmbedding(model_name=MODEL_NAME)

# Semantic Anchors
ANCHOR_DATA = {
    "identification": ["salah", "error", "bug", "mistake", "masalah"],
    "justification": ["karena", "sebab", "alasan", "because", "reason"],
    "constructive": ["sebaiknya", "perbaiki", "saran", "should", "fix", "suggest"],
    "blooms_high": ["analisis", "optimasi", "refactor", "analyze", "optimize"],
    "domain_relevance": [
        "technical programming feedback", "code review comment", 
        "sql query feedback", "software implementation review",
        "komentar review kode", "masukan teknis pemrograman"
    ]
}

def _get_embeddings(texts: List[str]) -> np.ndarray:
    return np.array(list(model.embed(texts)))

ANCHOR_VECTORS = {
    category: _get_embeddings(keywords)
    for category, keywords in ANCHOR_DATA.items()
}

def _is_gibberish(text: str) -> bool:
    """Basic heuristic to catch 'asdfghjkl' style gibberish."""
    # Cek rasio huruf hidup
    vowels = len(re.findall(r'[aeiou]', text.lower()))
    total_chars = len(re.sub(r'\s+', '', text))
    if total_chars == 0: return True
    vowel_ratio = vowels / total_chars
    
    consonant_runs = re.findall(r'[^aeiou\s]{5,}', text.lower())
    
    return vowel_ratio < 0.1 or len(consonant_runs) > 0

def calculate_system_score(feedback_text: str) -> float:
    # Basic Prefilters
    if not feedback_text or len(feedback_text.strip()) < 15:
        return 0.1
    
    if _is_gibberish(feedback_text):
        return 0.1

    text = feedback_text.strip()
    
    # Domain Relevance Check (Sentence Level)
    sentence_vector = next(model.embed([text]))
    domain_anchors = ANCHOR_VECTORS["domain_relevance"]
    relevance_sim = float(np.max(np.dot(domain_anchors, sentence_vector)))
    
    is_relevant = relevance_sim > 0.5

    # Word-Level Feature Scoring
    clean_text = text.lower().replace('.', ' ').replace(',', ' ').replace('!', ' ')
    words = [w for w in clean_text.split() if len(w) > 2]
    if not words: return 0.1
    
    word_vectors = np.array(list(model.embed(words)))
    category_scores = []
    for cat in ["identification", "justification", "constructive", "blooms_high"]:
        anchors = ANCHOR_VECTORS[cat]
        sim_matrix = np.dot(word_vectors, anchors.T)
        category_scores.append(float(np.max(sim_matrix)))

    final_score = sum(category_scores) / 4.0
    
    if not is_relevant:
        return min(0.15, final_score)

    return max(0.0, min(1.0, final_score))
