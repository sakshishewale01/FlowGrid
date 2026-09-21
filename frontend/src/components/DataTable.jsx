import React, { useState, useMemo } from 'react';
import LoadingState from './LoadingState';
import EmptyState from './EmptyState';

/**
 * Reusable DataTable component with sorting, pagination, skeleton loading, and empty states.
 *
 * @param {Object} props
 * @param {Array<{ key: string, header: string, render?: Function, sortable?: boolean, align?: 'left'|'center'|'right' }>} props.columns
 * @param {Array<Object>} props.data
 * @param {boolean} [props.loading=false]
 * @param {React.ReactNode} [props.emptyState]
 * @param {boolean} [props.pagination=true]
 * @param {number} [props.pageSize=10]
 * @param {string} [props.keyField='id']
 * @param {Function} [props.onRowClick]
 */
export default function DataTable({
  columns = [],
  data = [],
  loading = false,
  emptyState = null,
  pagination = true,
  pageSize = 10,
  keyField = 'id',
  onRowClick = null,
}) {
  const [currentPage, setCurrentPage] = useState(1);
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });

  // Sorting
  const sortedData = useMemo(() => {
    if (!sortConfig.key) return data;

    return [...data].sort((a, b) => {
      let aVal = a[sortConfig.key];
      let bVal = b[sortConfig.key];

      if (aVal === undefined || aVal === null) aVal = '';
      if (bVal === undefined || bVal === null) bVal = '';

      if (typeof aVal === 'string') {
        const cmp = aVal.localeCompare(String(bVal));
        return sortConfig.direction === 'asc' ? cmp : -cmp;
      }

      if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });
  }, [data, sortConfig]);

  // Pagination
  const totalPages = Math.ceil(sortedData.length / pageSize) || 1;
  const paginatedData = useMemo(() => {
    if (!pagination) return sortedData;
    const start = (currentPage - 1) * pageSize;
    return sortedData.slice(start, start + pageSize);
  }, [sortedData, pagination, currentPage, pageSize]);

  const handleSort = (colKey, sortable) => {
    if (!sortable) return;
    setSortConfig((current) => {
      if (current.key === colKey) {
        return {
          key: colKey,
          direction: current.direction === 'asc' ? 'desc' : 'asc',
        };
      }
      return { key: colKey, direction: 'asc' };
    });
  };

  const startEntry = (currentPage - 1) * pageSize + 1;
  const endEntry = Math.min(currentPage * pageSize, sortedData.length);

  return (
    <div className="fg-datatable-wrapper">
      <div className="table-container">
        <table className="ops-table">
          <thead>
            <tr>
              {columns.map((col) => {
                const isSorted = sortConfig.key === col.key;
                const sortIcon = isSorted ? (sortConfig.direction === 'asc' ? ' ▲' : ' ▼') : '';
                return (
                  <th
                    key={col.key}
                    style={{
                      textAlign: col.align || 'left',
                      cursor: col.sortable ? 'pointer' : 'default',
                      userSelect: 'none',
                    }}
                    onClick={() => handleSort(col.key, col.sortable)}
                  >
                    <span>{col.header}</span>
                    {col.sortable && <span className="fg-sort-indicator">{sortIcon || ' ↕'}</span>}
                  </th>
                );
              })}
            </tr>
          </thead>

          {loading ? (
            <LoadingState variant="skeleton-table" rows={pageSize > 5 ? 5 : pageSize} columns={columns.length} />
          ) : paginatedData.length === 0 ? (
            <tbody>
              <tr>
                <td colSpan={columns.length} className="table-empty-cell">
                  {emptyState || <EmptyState />}
                </td>
              </tr>
            </tbody>
          ) : (
            <tbody>
              {paginatedData.map((item, idx) => (
                <tr
                  key={item[keyField] ?? idx}
                  onClick={onRowClick ? () => onRowClick(item) : undefined}
                  style={{ cursor: onRowClick ? 'pointer' : 'default' }}
                >
                  {columns.map((col) => (
                    <td key={col.key} style={{ textAlign: col.align || 'left' }}>
                      {col.render ? col.render(item) : item[col.key] ?? '—'}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          )}
        </table>
      </div>

      {pagination && !loading && sortedData.length > 0 && (
        <div className="fg-table-pagination">
          <div className="fg-pagination-meta">
            Showing <strong>{startEntry}</strong> to <strong>{endEntry}</strong> of <strong>{sortedData.length}</strong> entries
          </div>

          <div className="fg-pagination-actions">
            <button
              type="button"
              className="fg-page-btn"
              disabled={currentPage <= 1}
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            >
              Previous
            </button>
            <span className="fg-page-indicator">
              Page {currentPage} of {totalPages}
            </span>
            <button
              type="button"
              className="fg-page-btn"
              disabled={currentPage >= totalPages}
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
