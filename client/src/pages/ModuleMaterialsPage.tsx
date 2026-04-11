import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getModuleMaterials, type ModuleMaterials, type PDFMaterial } from '../data/moduleMaterials';
import { sessionService } from '../services/session';

/**
 * ModuleMaterialsPage
 * Displays module learning materials with accordion-style PDF viewer
 */
export function ModuleMaterialsPage() {
  const { moduleId } = useParams<{ moduleId: string }>();
  const navigate = useNavigate();

  const [moduleData, setModuleData] = useState<ModuleMaterials | null>(null);
  const [expandedPdf, setExpandedPdf] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!moduleId) {
      navigate('/dashboard');
      return;
    }

    const materials = getModuleMaterials(moduleId);
    if (!materials) {
      navigate('/dashboard');
      return;
    }

    setModuleData(materials);
  }, [moduleId, navigate]);

  const handleStartAssessment = useCallback(async () => {
    if (!moduleId) return;

    setIsLoading(true);
    setError('');

    try {
      const result = await sessionService.startSession({ module_id: moduleId });
      navigate(`/session/${result.session_id}`);
    } catch {
      setError('Failed to start assessment session. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }, [moduleId, navigate]);

  const togglePdf = (pdfId: string) => {
    setExpandedPdf(expandedPdf === pdfId ? null : pdfId);
  };

  const openFullscreen = (filename: string) => {
    const pdfUrl = `/learning_modules/${encodeURIComponent(filename)}`;
    window.open(pdfUrl, '_blank');
  };

  const downloadPdf = (filename: string) => {
    const pdfUrl = `/learning_modules/${encodeURIComponent(filename)}`;
    const link = document.createElement('a');
    link.href = pdfUrl;
    link.download = filename;
    link.target = '_blank';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (!moduleData) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading materials...</p>
        </div>
      </div>
    );
  }

  return (
    <>
        {/* Header Section */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex items-center gap-4 mb-4">
            <button
              onClick={() => navigate('/dashboard')}
              className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
            </button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{moduleData.title}</h1>
              <p className="text-sm text-gray-500 mt-1">Module ID: {moduleData.moduleId}</p>
            </div>
          </div>

          <p className="text-gray-700 leading-relaxed">{moduleData.description}</p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg">
            {error}
          </div>
        )}

        {/* Materials Accordion */}
        <div className="bg-white rounded-lg shadow-md overflow-hidden mb-6">
          <div className="p-4 border-b border-gray-200 bg-gray-50">
            <h2 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
              <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
              Learning Materials
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              Expand each section to view the PDF content. You can also download or open in fullscreen.
            </p>
          </div>

          <div className="divide-y divide-gray-200">
            {moduleData.materials.map((pdf: PDFMaterial) => (
              <div key={pdf.id} className="border-b border-gray-200 last:border-b-0">
                {/* Accordion Header */}
                <button
                  onClick={() => togglePdf(pdf.id)}
                  className="w-full px-4 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors text-left"
                >
                  <div className="flex items-center gap-3">
                    <div className="shrink-0 w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
                      <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                      </svg>
                    </div>
                    <div>
                      <h3 className="font-medium text-gray-900">{pdf.title}</h3>
                      <p className="text-sm text-gray-500">{pdf.description}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-400">PDF</span>
                    <svg
                      className={`w-5 h-5 text-gray-400 transition-transform ${
                        expandedPdf === pdf.id ? 'rotate-180' : ''
                      }`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </button>

                {/* Accordion Content - PDF Viewer */}
                {expandedPdf === pdf.id && (
                  <div className="px-4 pb-4">
                    <div className="border border-gray-200 rounded-lg overflow-hidden bg-gray-50">
                      {/* PDF Toolbar */}
                      <div className="flex items-center justify-between px-3 py-2 bg-gray-100 border-b border-gray-200">
                        <span className="text-sm font-medium text-gray-700 truncate max-w-xs">
                          {pdf.filename}
                        </span>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => downloadPdf(pdf.filename)}
                            className="flex items-center gap-1 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-200 rounded transition-colors"
                            title="Download PDF"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                            </svg>
                            Download
                          </button>
                          <button
                            onClick={() => openFullscreen(pdf.filename)}
                            className="flex items-center gap-1 px-3 py-1.5 text-sm text-blue-600 hover:bg-blue-50 rounded transition-colors"
                            title="Open in fullscreen"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 4l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                            </svg>
                            Fullscreen
                          </button>
                        </div>
                      </div>

                      {/* PDF Embed */}
                      <div className="w-full h-150">
                        <iframe
                          src={`/learning_modules/${encodeURIComponent(pdf.filename)}`}
                          title={pdf.title}
                          className="w-full h-full"
                          style={{ border: 'none' }}
                        />
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Start Assessment Button */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            <h3 className="text-lg font-semibold text-blue-900">Ready to practice?</h3>
            <p className="text-sm text-blue-700">
              Start an assessment session to test your understanding of {moduleData.title}.
            </p>
          </div>
          <button
            onClick={handleStartAssessment}
            disabled={isLoading}
            className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? (
              <>
                <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Starting...
              </>
            ) : (
              <>
                Start Assessment
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </>
            )}
          </button>
        </div>
    </>
  );
}

export default ModuleMaterialsPage;
