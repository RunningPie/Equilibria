import { useParams } from 'react-router-dom';

/**
 * Session Page
 * Phase 5 will implement the full session with CodeMirror
 * This is a placeholder for Phase 2 routing setup
 */
export function Session() {
  const { sessionId } = useParams<{ sessionId: string }>();

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">Assessment Session</h1>
        <div className="bg-white p-6 rounded-lg shadow-md">
          <p className="text-gray-600">Session placeholder - Phase 5 implementation</p>
          <p className="text-gray-500 mt-2">Session ID: {sessionId}</p>
          <p className="text-gray-500">Will include CodeMirror SQL editor</p>
        </div>
      </div>
    </div>
  );
}

export default Session;
