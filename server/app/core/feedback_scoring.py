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

# Semantic Anchors (Sentence-level based on Bloom's Taxonomy & Rubrics)
ANCHOR_DATA = {
    "cognitive_description": [
        "kode ini berfungsi untuk", "secara keseluruhan program ini", "fungsi utama dari bagian ini adalah", "saya melihat kode ini mengimplementasikan", "sebagai rangkuman, kode ini",
        "this code functions to", "overall this program", "the main function of this part is", "i see this code implements", "to summarize, this code"
    ],
    "cognitive_identification": [
        "terdapat error pada baris", "ada bug di bagian fungsi", "saya menemukan kesalahan pada", "masalah terdeteksi ketika", "kode ini bermasalah di",
        "there is an error on line", "there is a bug in the function", "i found a mistake at", "a problem is detected when", "this code has an issue in"
    ],
    "cognitive_justification": [
        "hal ini karena", "alasannya adalah", "sebabnya dikarenakan", "pendekatan ini beresiko karena dapat menyebabkan", "saya mengevaluasi bahwa ini akan",
        "this is because", "the reason is", "the cause is due to", "this approach is risky because it can lead to", "i evaluate that this will"
    ],
    "constructive": [
        "sebaiknya kamu menggunakan", "saran saya adalah mencoba", "akan lebih baik jika dirancang ulang dengan", "coba optimasi bagian ini menggunakan", "mari kita perbaiki dengan",
        "you should use", "my suggestion is to try", "it would be better to redesign it with", "try optimizing this part using", "let's fix this by"
    ],
    "affective": [
        "kode yang sangat rapi", "pendekatan yang hebat", "kerja yang bagus", "saya suka solusi ini", "solusi yang sangat elegan",
        "very clean code", "great approach", "good job", "i like this solution", "a very elegant solution"
    ],
    "domain_relevance": [
        "komentar review kode", "masukan teknis pemrograman", "evaluasi implementasi perangkat lunak", "umpan balik query database", "penilaian logika algoritma",
        "technical programming feedback", "code review comment", "software implementation review", "sql query feedback", "algorithm and logic evaluation"
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

def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences using basic punctuation."""
    sentences = re.split(r'(?<=[.!?])\s+|\n+', text)
    return [s.strip() for s in sentences if len(s.strip()) > 3]

def calculate_system_score(feedback_text: str) -> float:
    # Basic Prefilters
    if not feedback_text or len(feedback_text.strip()) < 15:
        return 0.1
    
    if _is_gibberish(feedback_text):
        return 0.1

    text = feedback_text.strip()
    
    # Domain Relevance Check (Whole Text Level)
    text_vector = next(model.embed([text]))
    domain_anchors = ANCHOR_VECTORS["domain_relevance"]
    relevance_sim = float(np.max(np.dot(domain_anchors, text_vector)))
    
    is_relevant = relevance_sim > 0.5

    # Sentence-Level Feature Scoring
    sentences = split_into_sentences(text)
    if not sentences:
        sentences = [text]
        
    sentence_vectors = _get_embeddings(sentences)
    category_scores = []
    
    scoring_categories = [
        "cognitive_description", 
        "cognitive_identification", 
        "cognitive_justification", 
        "constructive", 
        "affective"
    ]
    
    for cat in scoring_categories:
        anchors = ANCHOR_VECTORS[cat]
        # sim_matrix shape: (len(sentences), len(anchors))
        sim_matrix = np.dot(sentence_vectors, anchors.T)
        category_scores.append(float(np.max(sim_matrix)))

    final_score = sum(category_scores) / len(scoring_categories)
    
    if not is_relevant:
        return min(0.15, final_score)

    return max(0.0, min(1.0, final_score))
