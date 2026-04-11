# 📘 PRODUCT REQUIREMENTS DOCUMENT: EQUILIBRIA
**Version:** 1.0  
**Status:** Implementation-Ready  
**Domain:** Computer Science Education / Adaptive Assessment  
**Core Innovation:** Collaborative Adaptive Assessment with Algorithmic Overpersonalization Mitigation

---

## 1. PRODUCT OVERVIEW
**Equilibria** is a web-based adaptive assessment platform designed for university-level SQL querying instruction. It dynamically calibrates question difficulty and student proficiency using a modified Elo-rating system, while proactively detecting learning stagnation. Upon stagnation detection, the system triggers a structured peer-review intervention matched via constraint-based re-ranking. This dual-track approach ensures that personalization enhances, rather than isolates, the learner from diverse cognitive perspectives.

---

## 2. TARGET AUDIENCE & PERSONAS
| Persona | Role | Primary Goal |
|---------|------|--------------|
| **Learner (Student)** | Undergraduate CS/IT student | Master SQL concepts through adaptive practice, receive timely feedback, and engage in structured peer collaboration without self-directed navigation overhead. |
| **Instructor/Lab Assistant** | Course facilitator | Seed question bank, monitor cohort progress via anonymized analytics, and validate learning outcomes without manual grading burden. |
| **Researcher** | Academic evaluator | Isolate the impact of collaborative interventions on learning gain using controlled ablation (Group A vs B). |

---

## 3. PROBLEM STATEMENT & VALUE PROPOSITION
### 🔍 Problem
Traditional adaptive systems optimize exclusively for individual competency, creating **overpersonalization** (filter bubbles). Students receive questions that match their current comfort zone, leading to:
- Premature convergence of Elo ratings (stagnation)
- Lack of exposure to heterogeneous problem-solving approaches
- Illusion of mastery without collaborative or higher-order critical thinking

### 💡 Value Proposition
Equilibria replaces passive adaptive sequencing with **proactive cognitive diversification**. By treating peer assessment as a first-class competency signal (Social Elo) and algorithmically enforcing heterogeneous pairings, the system guarantees that learners experience both personalized challenge and socially scaffolded growth.

---

## 4. CORE OBJECTIVES & SUCCESS METRICS
| Objective | Metric | Target |
|-----------|--------|--------|
| Improve conceptual mastery | Normalized Learning Gain (NLG) | `g ≥ 0.3` (Medium-High) |
| Mitigate overpersonalization | Post-intervention Δθ slope vs pre-intervention | `Slope_post > Slope_pre` |
| Ensure meaningful peer exposure | Cohen’s `d` between matched pairs | `d ≥ 0.5` for 100% of pairs |
| Trigger timely interventions | Stagnation detection rate per group | `≥ 50%` (min 5/10 users) |
| Validate social competency signal | Average NLP `system_score` on peer feedback | `≥ 0.6` |
| Maintain system responsiveness | API p95 latency | `≤ 500ms` |

---

## 5. FUNCTIONAL REQUIREMENTS
### 5.1 Authentication & Onboarding
- JWT-based login with Argon2id password hashing
- Mandatory 5-question adaptive pretest for cold-start calibration
- Auto-assignment to Group A (with intervention) or Group B (ablation control)

### 5.2 Adaptive Learning Engine
- Module-based progression (CH01 → CH02 → CH03) with theta-gated unlocks
- Max 3 attempts per question; Elo updates only on `final_attempt`
- Real-time difficulty recalibration per question
- Fallback session termination (24h auto-abandon)

### 5.3 Stagnation Detection & Peer Intervention
- Primary trigger: Variance of last 5 `Δθ` (final attempts) `< 165`
- Secondary trigger: `≥ 8` final attempts in current chapter without next chapter unlock
- Automatic transition to Collaborative Mode upon trigger (Group A only)
- Anonymous peer matching with heterogeneity enforcement

### 5.4 Peer Assessment Workflow
- Reviewer sees anonymized query + rubric
- Dual scoring: `final_score = 0.5 × system_NLP + 0.5 × requester_vote`
- Social Elo update post-rating
- 24-hour expiration for pending reviews

### 5.5 Progress Visualization & Social Awareness
- `theta_display = (0.8 × θ_individu) + (0.2 × θ_social)`
- Anonymized leaderboard with obfuscated names
- Module completion radar & attempt history

---

## 6. NON-FUNCTIONAL REQUIREMENTS
| Category | Requirement |
|----------|-------------|
| **Performance** | Near real-time rating updates (<500ms p95); efficient Elo computation |
| **Security** | Isolated `sandbox` schema with `SELECT`-only role; dangerous SQL keyword blocklist; 5s query timeout |
| **Privacy** | Double-blind peer assessment; no raw scores exposed; explicit consent for data collection |
| **Scalability** | Supports ~50 concurrent users; connection pooling via asyncpg |
| **Reliability** | ACID-compliant transactions; idempotent session start/resume; graceful fallback on peer unavailability |
| **Maintainability** | Alembic migrations; structured JSON logging; dual log streams (system vs assessment) |

---

## 7. CORE ALGORITHMIC LOGIC (HIGH-LEVEL BREAKDOWN)
Below is the logical flow of the three core algorithms. Pseudocode is provided for clarity without implementation specifics.

### 7.1 Individual Elo Update (Vesin-Aligned)
```pseudocode
FUNCTION update_individual_elo(user_theta, question_difficulty, k_factor, attempts):
    W = calculate_success_rate(attempts)  // Maps to Vesin Eq.3
    We = 1 / (1 + 10^((user_theta - question_difficulty) / 400))  // Eq.4
    
    delta = k_factor * (W - We)
    new_user_theta = clamp(user_theta + delta, 0, 2000)
    new_question_diff = clamp(question_difficulty - delta, 0, 2000)
    
    RETURN new_user_theta, new_question_diff
```
*Key Notes:* 
- `W` incorporates attempt ratio, binary sandbox result, and time decay.
- `K` decays per Vesin thresholds: `{<10:30, 10-24:20, 25-49:15, ≥50:10}`.

### 7.2 Stagnation Detection
```pseudocode
FUNCTION detect_stagnation(user_id, current_module):
    IF current_module == 'CH03' RETURN FALSE  // Convergence is expected here
    
    last_5_final_logs = query_final_attempts(user_id, limit=5)
    IF count(last_5_final_logs) < 5 RETURN FALSE
    
    deltas = [log.theta_after - log.theta_before FOR log IN last_5_final_logs]
    variance = population_variance(deltas)
    
    RETURN variance < 165
```
*Key Notes:* Global scope (cross-session), calibrated for [0,2000] scale with K=30.

### 7.3 Constraint-Based Peer Matching
```pseudocode
FUNCTION find_heterogeneous_peer(requester_theta):
    pop_std = standard_deviation(all_active_user_thetas)
    min_diff = 0.5 * pop_std  // Cohen's d = 0.5
    
    candidates = filter_active_users(
        WHERE ABS(theta_individu - requester_theta) >= min_diff
        AND status != 'NEEDS_PEER_REVIEW'
    )
    
    IF empty(candidates) RETURN NULL
    RETURN random_select(top_5_sorted_by_descending_diff(candidates))
```
*Key Notes:* Guarantees meaningful cognitive distance; falls back gracefully if population is too homogeneous.

---

## 8. SYSTEM ARCHITECTURE & TECH STACK
```
┌─────────────────┐      HTTPS/JSON      ┌──────────────────┐
│   FRONTEND      │ ◄──────────────────► │    BACKEND       │
│   (React SPA)   │                      │   (FastAPI)      │
└────────┬────────┘                      └────────┬─────────┘
         │                                        │
         ▼                                        ▼
┌─────────────────┐                      ┌──────────────────┐
│  Browser        │                      │  PostgreSQL      │
│  (CodeMirror 6) │                      │  ├ public        │
└─────────────────┘                      │  └ sandbox       │
                                         └──────────────────┘
```
| Layer | Technology | Rationale |
|-------|------------|-----------|
| Frontend | React 18, Vite, Zustand, Tailwind, CodeMirror 6 | Component-driven, lightweight state, SQL syntax highlighting |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic | Async support, automatic OpenAPI docs, ACID ORM |
| Database | PostgreSQL 15 | MVCC, schema isolation, robust for transitive rating updates |
| Deployment | Vercel (FE), Render/Railway (BE), Supabase (DB) | Free-tier optimized, Docker-composable, zero infra cost |

---

## 9. USER JOURNEY & STATE MANAGEMENT
1. **Cold Start** → Login → Pretest (5 adaptive Qs) → `θ_initial` calculated → Dashboard
2. **Individual Mode** → Select Module → Session Start → Solve/Retry/Next → Elo updates → Module unlocks when threshold met
3. **Stagnation Trigger** → Variance `< 165` or `N=8` fallback → `status = NEEDS_PEER_REVIEW` → Match peer → Create `peer_session`
4. **Collaborative Mode** → Reviewer submits feedback → Requester rates → `θ_social` updated → Both return to `ACTIVE`
5. **Completion** → Session ends → Leaderboard/Profile updates → Post-test (lab study) → NLG calculation

*State Guardrails:* Only one `ACTIVE` session per user. Abandoned sessions auto-expire after 24h. Peer sessions expire after 24h if unrated.

---

## 10. DATA, SECURITY & COMPLIANCE
- **Sandbox Isolation:** Dedicated `sandbox_executor` role with `GRANT SELECT` only. `SET LOCAL statement_timeout = 5000`. Blocklist: `DROP, DELETE, INSERT, UPDATE, ALTER, CREATE, TRUNCATE, GRANT, REVOKE, PG_, --`
- **Authentication:** JWT (30m access, 7d refresh), Argon2id (`m=2^16, t=3, p=4`)
- **Privacy:** Double-blind peer review; leaderboard obfuscates all names except self; explicit `Informed Consent` required for lab participation
- **Auditability:** Dual logging (system JSON + structured DB); all Elo deltas, stagnation flags, and peer scores are immutable post-commit

---

## 11. TESTING & EVALUATION STRATEGY
### 11.1 Controlled Lab Study Design
- **Format:** Two-group pretest-posttest with stratified assignment
- **Group A:** Full intervention (variance + fallback triggers peer review)
- **Group B:** Ablation control (stagnation logged, no peer intervention)
- **Duration:** 105 minutes (15m pretest → 75m interaction → 15m posttest)
- **Analysis:** Paired t-tests for grade/rating alignment, NLG comparison, slope analysis pre/post stagnation, thematic analysis of qualitative feedback

### 11.2 Validation Layers
1. **Algorithmic:** Precision/Recall of recommendations, convergence within 7–10 questions (per Vesin)
2. **Pedagogical:** NLG ≥ 0.3, post-intervention Δθ slope increase
3. **Systemic:** p95 latency, sandbox timeout adherence, matching validity (Cohen’s d ≥ 0.5)

---

## 12. IMPLEMENTATION ROADMAP
| Phase | Timeline | Deliverables |
|-------|----------|--------------|
| **1. Backend Core** | Week 1–2 | DB schema, Elo engine, pretest flow, sandbox executor |
| **2. Adaptive Logic** | Week 3–4 | Stagnation detection, K-factor decay, module unlock, fallback trigger |
| **3. Frontend UI** | Week 5–6 | React routes, CodeMirror integration, dashboard, session flow |
| **4. Collaboration** | Week 7 | Peer matching, review UI, Social Elo, dual scoring, expiration tasks |
| **5. Integration & Alpha** | Week 8 | API wiring, logging, deployment, seed content, internal testing |
| **6. Lab Study & Eval** | Week 9–10 | Controlled sessions, data collection, NLG calculation, thematic analysis |
| **7. Thesis & Closure** | Week 11–12 | Final report, visualization dashboards, academic submission |

---

## 13. RISKS & MITIGATIONS
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Stagnation not triggered by variance | Low | High | Fallback `N=8` question safety net |
| No available peer at trigger time | Medium | Medium | Continue individual mode; log `PEER_MATCH_FAIL`; Group B can act as fallback reviewers |
| `θ_social` non-convergence in small sample | High | Low | Accept as documented limitation; rely on `system_score` validation |
| Cold-start `θ_initial` inaccuracy | Low | High | Pretest calibration + Mann-Whitney stratification for group balance |
| Session abandonment mid-flow | Medium | Medium | 24h auto-abandon background task; idempotent resume on restart |

---

## 14. REFERENCES & ALIGNMENT
- **Vesin et al. (2022):** Foundation for modified Elo rating, success rate mapping, K-factor adaptation, and cold-start calibration methodology.
- **Biasio et al. (2023):** Constraint-based re-ranking framework for echo chamber mitigation (adapted to Cohen’s `d` threshold).
- **Kerman et al. (2024):** Cognitive feedback scoring rubric (Identification, Justification, Constructive, Bloom's verbs).
- **ACM CCECC (2023):** Bloom's taxonomy verbs for computing disciplines.
- **Cohen (1988):** Effect size conventions for heterogeneity enforcement (`d = 0.5`).