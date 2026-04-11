import type { QueryResult } from '../types';

interface QueryResultDisplayProps {
  result: QueryResult;
  errorMessage?: string;
}

/**
 * QueryResultDisplay
 * Displays the results of a SQL query execution in a formatted table
 */
export function QueryResultDisplay({ result, errorMessage }: QueryResultDisplayProps) {
  if (errorMessage) {
    return (
      <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
        <div className="flex items-center gap-2 text-red-700 mb-2">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="font-medium">Query Execution Error</span>
        </div>
        <p className="text-sm text-red-600">{errorMessage}</p>
      </div>
    );
  }

  if (!result || result.row_count === 0) {
    return (
      <div className="mt-4 p-4 bg-gray-50 border border-gray-200 rounded-lg">
        <p className="text-sm text-gray-600">Query executed successfully but returned no rows.</p>
        <p className="text-xs text-gray-500 mt-1">Row count: 0</p>
      </div>
    );
  }

  // Get column headers from the first row
  const columns = Object.keys(result.rows[0]);

  return (
    <div className="mt-4">
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-sm font-semibold text-gray-700">Query Results</h4>
        <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
          {result.row_count} {result.row_count === 1 ? 'row' : 'rows'}
        </span>
      </div>

      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <div className="overflow-x-auto max-h-60">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50 sticky top-0">
              <tr>
                {columns.map((column) => (
                  <th
                    key={column}
                    className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    {column}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {result.rows.map((row, rowIndex) => (
                <tr key={rowIndex} className="hover:bg-gray-50">
                  {columns.map((column) => (
                    <td
                      key={`${rowIndex}-${column}`}
                      className="px-3 py-2 text-sm text-gray-900 whitespace-nowrap"
                    >
                      {row[column] === null ? (
                        <span className="text-gray-400 italic">NULL</span>
                      ) : typeof row[column] === 'boolean' ? (
                        row[column] ? 'true' : 'false'
                      ) : (
                        String(row[column])
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default QueryResultDisplay;
