
import sys
import os
import numpy as np

if os.getcwd() not in sys.path:
    sys.path.append(os.getcwd())

try:
    from app.core.feedback_scoring import calculate_system_score, model, ANCHOR_VECTORS, split_into_sentences
    print("NLP System Scoring Module Loaded Successfully.")
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def get_detailed_sentence_scores(text: str):
    # Sentence level relevance (uses whole text)
    text_vector = next(model.embed([text]))
    domain_anchors = ANCHOR_VECTORS["domain_relevance"]
    relevance_sim = float(np.max(np.dot(domain_anchors, text_vector)))

    sentences = split_into_sentences(text)
    if not sentences:
        sentences = [text]
        
    sentence_vectors = np.array(list(model.embed(sentences)))
    results = {"relevance": relevance_sim}
    
    scoring_categories = [
        "cognitive_description", 
        "cognitive_identification", 
        "cognitive_justification", 
        "constructive", 
        "affective"
    ]
    
    for cat in scoring_categories:
        anchors = ANCHOR_VECTORS[cat]
        sim_matrix = np.dot(sentence_vectors, anchors.T)
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

    print("\nSentence-Level Semantic Max: Calibrated with Domain Filter")
    header = f"{'Category':<7} | {'Lang':<4} | {'Score':<5} | {'Rel':<5} | {'Desc':<5} | {'Iden':<5} | {'Just':<5} | {'Cons':<5} | {'Affc':<5} | {'Feedback Text'}"
    print(header)
    print("-" * 140)

    for tc in test_suite:
        score = calculate_system_score(tc['text'])
        raw = get_detailed_sentence_scores(tc['text'])
        
        if raw:
            scores_str = f"{raw['relevance']:<5.2f} | {raw['cognitive_description']:<5.2f} | {raw['cognitive_identification']:<5.2f} | {raw['cognitive_justification']:<5.2f} | {raw['constructive']:<5.2f} | {raw['affective']:<5.2f}"
        else:
            scores_str = f"{'N/A':<5} | {'N/A':<5} | {'N/A':<5} | {'N/A':<5} | {'N/A':<5} | {'N/A':<5}"
            
        print(f"{tc['cat']:<7} | {tc['lang']:<4} | {score:<5.2f} | {scores_str} | {tc['text'][:40]}..." )

if __name__ == "__main__":
    run_tests()
