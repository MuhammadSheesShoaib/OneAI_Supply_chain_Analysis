import { useState, useMemo } from 'react';
import { motion } from 'motion/react';
import {
  ChevronUp,
  ChevronDown,
  Search,
  Eye,
  Filter,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import type { Risk, Priority, RiskCategory } from '../types';

interface RiskTableProps {
  risks: Risk[];
  onViewDetails: (risk: Risk) => void;
}

type SortField = 'id' | 'riskScore' | 'priority' | 'timeline';
type SortDirection = 'asc' | 'desc';

export function RiskTable({ risks, onViewDetails }: RiskTableProps) {
  const [sortField, setSortField] = useState<SortField>('riskScore');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterCategory, setFilterCategory] = useState<RiskCategory | 'all'>('all');
  const [filterPriority, setFilterPriority] = useState<Priority | 'all'>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const filteredAndSortedRisks = useMemo(() => {
    let filtered = risks.filter((risk) => {
      const matchesSearch =
        risk.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        risk.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        risk.impact.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesCategory =
        filterCategory === 'all' || risk.category === filterCategory;
      const matchesPriority =
        filterPriority === 'all' || risk.priority === filterPriority;
      return matchesSearch && matchesCategory && matchesPriority;
    });

    filtered.sort((a, b) => {
      let aVal: any = a[sortField];
      let bVal: any = b[sortField];

      if (sortField === 'timeline') {
        aVal = parseInt(a.timeline);
        bVal = parseInt(b.timeline);
      }

      if (sortField === 'priority') {
        const priorityOrder: Record<Priority, number> = {
          Critical: 4,
          High: 3,
          Medium: 2,
          Low: 1,
        };
        aVal = priorityOrder[a.priority];
        bVal = priorityOrder[b.priority];
      }

      if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });

    return filtered;
  }, [risks, searchTerm, filterCategory, filterPriority, sortField, sortDirection]);

  const totalPages = Math.ceil(filteredAndSortedRisks.length / itemsPerPage);
  const paginatedRisks = filteredAndSortedRisks.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const getPriorityColor = (priority: Priority) => {
    const colors = {
      Critical: 'bg-red-100 text-red-800',
      High: 'bg-orange-100 text-orange-800',
      Medium: 'bg-yellow-100 text-yellow-800',
      Low: 'bg-green-100 text-green-800',
    };
    return colors[priority];
  };

  const getRowColor = (priority: Priority) => {
    const colors = {
      Critical: 'bg-red-50',
      High: 'bg-orange-50',
      Medium: 'bg-yellow-50',
      Low: 'bg-green-50',
    };
    return colors[priority];
  };

  const getCategoryColor = (category: RiskCategory) => {
    const colors: Record<RiskCategory, string> = {
      Suppliers: 'bg-blue-100 text-blue-800',
      Manufacturing: 'bg-purple-100 text-purple-800',
      Inventory: 'bg-green-100 text-green-800',
      Demand: 'bg-orange-100 text-orange-800',
      Transportation: 'bg-indigo-100 text-indigo-800',
      'External Factors': 'bg-pink-100 text-pink-800',
    };
    return colors[category];
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="bg-white rounded-lg shadow-md p-6"
    >
      <h2 className="text-2xl mb-6">Risk Analysis Table</h2>

      {/* Filters and Search */}
      <div className="mb-6 flex flex-col md:flex-row gap-4">
        {/* Search */}
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            placeholder="Search risks..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setCurrentPage(1);
            }}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#1769FF] focus:border-transparent"
          />
        </div>

        {/* Category Filter */}
        <div className="relative">
          <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <select
            value={filterCategory}
            onChange={(e) => {
              setFilterCategory(e.target.value as RiskCategory | 'all');
              setCurrentPage(1);
            }}
            className="pl-10 pr-8 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#1769FF] focus:border-transparent appearance-none bg-white"
          >
            <option value="all">All Categories</option>
            <option value="Suppliers">Suppliers</option>
            <option value="Manufacturing">Manufacturing</option>
            <option value="Inventory">Inventory</option>
            <option value="Demand">Demand</option>
            <option value="Transportation">Transportation</option>
            <option value="External Factors">External Factors</option>
          </select>
        </div>

        {/* Priority Filter */}
        <div>
          <select
            value={filterPriority}
            onChange={(e) => {
              setFilterPriority(e.target.value as Priority | 'all');
              setCurrentPage(1);
            }}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#1769FF] focus:border-transparent appearance-none bg-white"
          >
            <option value="all">All Priorities</option>
            <option value="Critical">Critical</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left">
                <button
                  onClick={() => handleSort('id')}
                  className="flex items-center gap-1 hover:text-[#1769FF]"
                >
                  Risk ID
                  {sortField === 'id' &&
                    (sortDirection === 'asc' ? (
                      <ChevronUp className="w-4 h-4" />
                    ) : (
                      <ChevronDown className="w-4 h-4" />
                    ))}
                </button>
              </th>
              <th className="px-4 py-3 text-left">Category</th>
              <th className="px-4 py-3 text-left">Impact</th>
              <th className="px-4 py-3 text-left">
                <button
                  onClick={() => handleSort('riskScore')}
                  className="flex items-center gap-1 hover:text-[#1769FF]"
                >
                  Risk Score
                  {sortField === 'riskScore' &&
                    (sortDirection === 'asc' ? (
                      <ChevronUp className="w-4 h-4" />
                    ) : (
                      <ChevronDown className="w-4 h-4" />
                    ))}
                </button>
              </th>
              <th className="px-4 py-3 text-left">
                <button
                  onClick={() => handleSort('priority')}
                  className="flex items-center gap-1 hover:text-[#1769FF]"
                >
                  Priority
                  {sortField === 'priority' &&
                    (sortDirection === 'asc' ? (
                      <ChevronUp className="w-4 h-4" />
                    ) : (
                      <ChevronDown className="w-4 h-4" />
                    ))}
                </button>
              </th>
              <th className="px-4 py-3 text-left">
                <button
                  onClick={() => handleSort('timeline')}
                  className="flex items-center gap-1 hover:text-[#1769FF]"
                >
                  Timeline
                  {sortField === 'timeline' &&
                    (sortDirection === 'asc' ? (
                      <ChevronUp className="w-4 h-4" />
                    ) : (
                      <ChevronDown className="w-4 h-4" />
                    ))}
                </button>
              </th>
              <th className="px-4 py-3 text-left">Affected Entities</th>
              <th className="px-4 py-3 text-left">Actions</th>
            </tr>
          </thead>
          <tbody>
            {paginatedRisks.map((risk) => (
              <tr
                key={risk.id}
                className={`border-t border-gray-200 hover:shadow-md transition-shadow ${getRowColor(
                  risk.priority
                )}`}
              >
                <td className="px-4 py-3">
                  <code className="text-sm bg-gray-100 px-2 py-1 rounded">
                    {risk.id}
                  </code>
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`inline-block px-3 py-1 rounded-full text-xs ${getCategoryColor(
                      risk.category
                    )}`}
                  >
                    {risk.category}
                  </span>
                </td>
                <td className="px-4 py-3 max-w-xs">
                  <p className="truncate text-sm">{risk.impact}</p>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="flex-1 bg-gray-200 rounded-full h-2 w-24">
                      <div
                        className={`h-2 rounded-full ${
                          risk.riskScore >= 90
                            ? 'bg-red-600'
                            : risk.riskScore >= 70
                            ? 'bg-orange-500'
                            : risk.riskScore >= 50
                            ? 'bg-yellow-500'
                            : 'bg-green-500'
                        }`}
                        style={{ width: `${risk.riskScore}%` }}
                      />
                    </div>
                    <span className="text-sm">{risk.riskScore}</span>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`inline-block px-3 py-1 rounded-full text-xs ${getPriorityColor(
                      risk.priority
                    )}`}
                  >
                    {risk.priority}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm">{risk.timeline}</td>
                <td className="px-4 py-3 text-sm">
                  {risk.affectedEntities.length} entities
                </td>
                <td className="px-4 py-3">
                  <button
                    onClick={() => onViewDetails(risk)}
                    className="flex items-center gap-1 text-[#1769FF] hover:underline text-sm"
                  >
                    <Eye className="w-4 h-4" />
                    View Details
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="mt-6 flex items-center justify-between">
          <p className="text-sm text-gray-600">
            Showing {(currentPage - 1) * itemsPerPage + 1} to{' '}
            {Math.min(currentPage * itemsPerPage, filteredAndSortedRisks.length)} of{' '}
            {filteredAndSortedRisks.length} risks
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            {Array.from({ length: totalPages }, (_, i) => i + 1)
              .filter(
                (page) =>
                  page === 1 ||
                  page === totalPages ||
                  Math.abs(page - currentPage) <= 1
              )
              .map((page, idx, arr) => (
                <>
                  {idx > 0 && arr[idx - 1] !== page - 1 && (
                    <span key={`ellipsis-${page}`} className="px-2 py-2">
                      ...
                    </span>
                  )}
                  <button
                    key={page}
                    onClick={() => setCurrentPage(page)}
                    className={`px-4 py-2 rounded-lg ${
                      currentPage === page
                        ? 'bg-[#1769FF] text-white'
                        : 'border border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    {page}
                  </button>
                </>
              ))}
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </motion.div>
  );
}
