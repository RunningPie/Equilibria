import { useState } from 'react';

interface ReferenceImageProps {
  /** Image source URL - can be relative path from public folder or full URL */
  src: string;
  /** Title displayed above the image */
  title?: string;
  /** Alternative text for accessibility */
  alt?: string;
  /** Additional context/description shown below the image */
  description?: string;
  /** CSS class for custom styling */
  className?: string;
  /** Enable click-to-enlarge zoom feature */
  allowZoom?: boolean;
  /** Custom zoom button text */
  zoomLabel?: string;
}

/**
 * ReferenceImage - A reusable component for displaying large, rectangular,
 * material-related or reference images (e.g., database schema diagrams, charts, etc.)
 * 
 * Used consistently across PretestPage, SessionPage, and other assessment pages.
 */
export function ReferenceImage({
  src,
  title = 'Reference Image',
  alt,
  description,
  className = '',
  allowZoom = false,
  zoomLabel = 'Click to enlarge',
}: ReferenceImageProps) {
  const [isZoomed, setIsZoomed] = useState(false);

  return (
    <>
      <div className={`mt-6 p-4 bg-gray-50 rounded-lg ${className}`}>
        <h3 className="text-sm font-medium text-gray-700 mb-2">{title}</h3>
        <div 
          className={`bg-white border border-gray-200 rounded-lg overflow-hidden ${
            allowZoom ? 'cursor-pointer hover:ring-2 hover:ring-blue-400 transition-all' : ''
          }`}
          onClick={() => allowZoom && setIsZoomed(true)}
        >
          <img
            src={src}
            alt={alt || title}
            className="w-full h-auto object-contain"
          />
          {allowZoom && (
            <div className="flex items-center justify-center gap-1 py-2 bg-gray-50 border-t border-gray-200 text-xs text-gray-500">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
              </svg>
              {zoomLabel}
            </div>
          )}
        </div>
        {description && (
          <p className="text-xs text-gray-500 mt-2">{description}</p>
        )}
      </div>

      {/* Zoom Modal */}
      {isZoomed && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
          onClick={() => setIsZoomed(false)}
        >
          <div className="relative max-w-full max-h-full">
            {/* Close button */}
            <button
              onClick={() => setIsZoomed(false)}
              className="absolute -top-12 right-0 p-2 text-white hover:text-gray-300 transition-colors"
              aria-label="Close zoom"
            >
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
            
            {/* Zoomed image */}
            <img
              src={src}
              alt={alt || title}
              className="max-w-full max-h-[85vh] w-auto h-auto object-contain rounded-lg shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            />
            
            {/* Zoomed title */}
            <p className="text-center text-white text-sm mt-4 opacity-80">
              {title} — Click anywhere to close
            </p>
          </div>
        </div>
      )}
    </>
  );
}

export default ReferenceImage;
