import { useNavigate } from 'react-router-dom';

interface FAQItem {
  question: string;
  answer: string;
}

const faqData: FAQItem[] = [
  {
    question: 'What is Equilibria?',
    answer: 'Equilibria is an adaptive SQL assessment platform designed for university-level database instruction. Unlike traditional adaptive systems that only focus on individual competency, Equilibria proactively detects learning stagnation and triggers structured peer-review interventions to ensure you gain exposure to diverse problem-solving approaches.'
  },
  {
    question: 'How does the adaptive learning engine work?',
    answer: 'The system uses a modified Elo-rating algorithm to calibrate question difficulty and your proficiency level (θ). Based on your performance, the system dynamically adjusts question difficulty. Max 3 attempts per question are allowed, and Elo updates only on your final attempt. As you answer questions correctly, your θ increases and more challenging questions are presented.'
  },
  {
    question: 'What are the modules and how do I progress?',
    answer: 'Content is organized into modules (CH01 → CH02 → CH03). Each module has a θ-gated unlock threshold. You must demonstrate sufficient mastery in your current module before progressing to the next. Your progress is visualized on your dashboard showing both individual (θ_individu) and social (θ_social) scores.'
  },
  {
    question: 'What is stagnation detection?',
    answer: 'Stagnation occurs when your learning plateaus—typically when the variance of your last 5 proficiency changes (Δθ) falls below 165, or when you have attempted 8+ questions in a chapter without unlocking the next. When stagnation is detected, the system automatically transitions you to Collaborative Mode for peer intervention (Group A only).'
  },
  {
    question: 'What happens in Collaborative Mode?',
    answer: 'In Collaborative Mode, you are anonymously matched with a peer who has a meaningfully different proficiency level (Cohen\'s d ≥ 0.5). You will either submit a query for peer review or review a peer\'s query using a structured rubric. Your feedback is scored by both an NLP system and the requester\'s rating, contributing to your Social Elo (θ_social).'
  },
  {
    question: 'How is my progress displayed?',
    answer: 'Your displayed theta is calculated as: θ_display = (0.8 × θ_individu) + (0.2 × θ_social). The leaderboard shows anonymized rankings with obfuscated names. Your dashboard includes a module completion radar and attempt history.'
  },
  {
    question: 'What is the Peer Hub?',
    answer: 'The Peer Hub is where you can find peers to review. When you are in Collaborative Mode (status: NEEDS_PEER_REVIEW), you can submit queries for review. When matched as a reviewer, you will see anonymized queries with a rubric to provide structured feedback.'
  },
  {
    question: 'How does the SQL sandbox work?',
    answer: 'All SQL queries run in an isolated sandbox environment with SELECT-only permissions. Dangerous operations (DROP, DELETE, INSERT, UPDATE, ALTER, CREATE, TRUNCATE, etc.) are blocked. Queries timeout after 5 seconds for safety and performance.'
  },
  {
    question: 'Is my data private?',
    answer: 'Yes. Peer assessments are double-blind—neither reviewer nor requester identities are revealed. The leaderboard obfuscates all names except your own. We require explicit informed consent for lab participation and data collection. All assessment logs are immutable after commit.'
  },
  {
    question: 'What are the pretest and posttest?',
    answer: 'The pretest is a mandatory 5-question adaptive assessment for cold-start calibration that determines your initial θ. The posttest occurs at the end of your session to measure learning gain (NLG). This helps evaluate the effectiveness of the adaptive and collaborative interventions.'
  },
  // {
  //   question: 'How long do sessions last?',
  //   answer: 'Standard lab sessions are 105 minutes: 15 minutes pretest, 75 minutes interaction (individual + collaborative modes), and 15 minutes posttest. Sessions auto-abandon after 24 hours of inactivity. Pending peer reviews expire after 24 hours if unrated.'
  // },
  // {
  //   question: 'What are Group A and Group B?',
  //   answer: 'You are randomly assigned to Group A (full intervention) or Group B (ablation control). Group A receives peer interventions when stagnation is detected. Group B continues in individual mode with stagnation logged but no peer intervention. This controlled design helps isolate the impact of collaboration on learning gain.'
  // }
];

function FAQItemComponent({ item, index }: { item: FAQItem; index: number }) {
  return (
    <div className="border-b border-gray-200 last:border-b-0">
      <details className="group">
        <summary className="flex items-center justify-between py-4 cursor-pointer list-none">
          <div className="flex items-start gap-3">
            <span className="flex-shrink-0 w-8 h-8 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center text-sm font-semibold">
              {index + 1}
            </span>
            <span className="text-gray-900 font-medium text-lg pt-0.5">{item.question}</span>
          </div>
          <svg
            className="w-5 h-5 text-gray-500 group-open:rotate-180 transition-transform flex-shrink-0 ml-2"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </summary>
        <div className="pb-4 pl-11 pr-4">
          <p className="text-gray-600 leading-relaxed">{item.answer}</p>
        </div>
      </details>
    </div>
  );
}

export function FAQPage() {
  const navigate = useNavigate();

  return (
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Back Button */}
        <button
          onClick={() => navigate('/dashboard')}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6 transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          <span>Back to Dashboard</span>
        </button>

        {/* Header */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-xl bg-indigo-100 flex items-center justify-center">
              <svg className="w-7 h-7 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-gray-900">Frequently Asked Questions</h1>
          </div>
          <p className="text-gray-600">
            Find answers to common questions about Equilibria's adaptive assessment system,
            peer collaboration features, and how to make the most of your learning experience.
          </p>
        </div>

        {/* FAQ List */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
          {faqData.map((item, index) => (
            <FAQItemComponent key={index} item={item} index={index} />
          ))}
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-gray-500 text-sm">
          <p>Still have questions? Contact your instructor or lab assistant.</p>
          <p className="mt-1">Equilibria Adaptive SQL Assessment Platform v1.0</p>
        </div>
      </div>
  );
}

export default FAQPage;
