
import sys
import os
import numpy as np

if os.getcwd() not in sys.path:
    sys.path.append(os.getcwd())

try:
    from app.core.feedback_scoring import calculate_system_score, model, ANCHOR_VECTORS
    print("NLP System Scoring Module Loaded Successfully.")
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def get_detailed_word_scores(text: str):
    clean_text = text.lower().replace('.', ' ').replace(',', ' ').replace('!', ' ')
    words = [w for w in clean_text.split() if len(w) > 2]
    if not words: return {}
    
    # Sentence level relevance
    sentence_vector = next(model.embed([text]))
    domain_anchors = ANCHOR_VECTORS["domain_relevance"]
    relevance_sim = float(np.max(np.dot(domain_anchors, sentence_vector)))

    # Word level feature scores
    word_vectors = np.array(list(model.embed(words)))
    results = {"relevance": relevance_sim}
    for cat in ["identification", "justification", "constructive", "blooms_high"]:
        anchors = ANCHOR_VECTORS[cat]
        sim_matrix = np.dot(word_vectors, anchors.T)
        results[cat] = float(np.max(sim_matrix))
        
    return results

def run_tests():
    test_suite = [
        {"cat": "ID", "lang": "ID", "text": "Logikanya melenceng di bagian join ini."},
        {"cat": "ID", "lang": "EN", "text": "The implementation seems quite flawed here."},
        {"cat": "Full", "lang": "ID", "text": "Ada yang nggak pas di line 5 soalnya kurang filter, mending ditambahin WHERE."},
        {"cat": "Full", "lang": "EN", "text": "Something is off in the query as it lacks filtering; aim to add a WHERE clause."},
        {"cat": "Vague", "lang": "ID", "text": "Wah kodenya mantap banget nih bro!"},
        {"cat": "Irrel", "lang": "ID", "text": "Saya ingin makan nasi goreng pedas sekali."},
        {"cat": "Irrel", "lang": "EN", "text": "The weather today is quite sunny and bright."},
        {"cat": "Short", "lang": "ID", "text": "Oke sip."},
        {"cat": "Gibber", "lang": "EN", "text": "asdfghjkl qwerty uiop zxcvbnm."},
    ]

    print("\nWord-Level Semantic Max: Calibrated with Domain Filter")
    header = f"{'Category':<7} | {'Lang':<4} | {'Score':<5} | {'Rel':<5} | {'ID':<5} | {'Jus':<5} | {'Con':<5} | {'Bloom':<5} | {'Feedback Text'}"
    print(header)
    print("-" * 130)

    for tc in test_suite:
        score = calculate_system_score(tc['text'])
        raw = get_detailed_word_scores(tc['text'])
        
        if raw:
            scores_str = f"{raw['relevance']:<5.2f} | {raw['identification']:<5.2f} | {raw['justification']:<5.2f} | {raw['constructive']:<5.2f} | {raw['blooms_high']:<5.2f}"
        else:
            scores_str = f"{'N/A':<5} | {'N/A':<5} | {'N/A':<5} | {'N/A':<5} | {'N/A':<5}"
            
        print(f"{tc['cat']:<7} | {tc['lang']:<4} | {score:<5.2f} | {scores_str} | {tc['text'][:40]}...")

if __name__ == "__main__":
    run_tests()
