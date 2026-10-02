import React, { useState } from 'react';
import { IncidentTelemetry } from '../../types';
import { AlertCircle, AlertTriangle, Info, Search, Filter } from 'lucide-react';

interface IncidentTimelineProps {
  incidents: IncidentTelemetry[];
}

export const IncidentTimeline: React.FC<IncidentTimelineProps> = ({ incidents }) => {
  const [filterSeverity, setFilterSeverity] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState('');

  const filtered = incidents
    .slice()
    .reverse()
    .filter((inc) => {
      if (filterSeverity !== 'ALL' && inc.severity !== filterSeverity) return false;
      if (
        searchTerm &&
        !inc.message.toLowerCase().includes(searchTerm.toLowerCase()) &&
        !inc.entity.toLowerCase().includes(searchTerm.toLowerCase())
      ) {
        return false;
      }
      return true;
    });

  return (
    <div className="bg-white dark:bg-slate-900 rounded-xl p-4 border border-slate-200 dark:border-slate-800 space-y-3">
      {/* Header and filters */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-100 dark:border-slate-800">
        <div>
          <h3 className="font-bold text-sm text-slate-900 dark:text-slate-100">
            Real-Time Incident &amp; Alert Timeline
          </h3>
          <p className="text-xs text-slate-500">
            Chronological audit log of state changes, faults, deadlock events, and recovery actions.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs">
          {/* Search box */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search incidents..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-8 pr-2.5 py-1 rounded-md border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs text-slate-800 dark:text-slate-200 focus:outline-none"
            />
          </div>

          {/* Severity filter */}
          <select
            value={filterSeverity}
            onChange={(e) => setFilterSeverity(e.target.value)}
            className="rounded-md border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 px-2 py-1 text-xs text-slate-800 dark:text-slate-200"
          >
            <option value="ALL">All Severities</option>
            <option value="CRITICAL">Critical Only</option>
            <option value="WARNING">Warnings</option>
            <option value="INFO">Info</option>
          </select>
        </div>
      </div>

      {/* Events stream */}
      <div className="divide-y divide-slate-100 dark:divide-slate-800 max-h-96 overflow-y-auto pr-1">
        {filtered.length === 0 ? (
          <div className="py-6 text-center text-xs text-slate-400">
            No incidents matching current criteria.
          </div>
        ) : (
          filtered.map((inc) => {
            const isCrit = inc.severity === 'CRITICAL';
            const isWarn = inc.severity === 'WARNING';

            return (
              <div key={inc.incident_id} className="py-2.5 flex items-start gap-3 text-xs">
                {/* Severity icon */}
                <div className="mt-0.5 shrink-0">
                  {isCrit ? (
                    <AlertCircle className="w-4 h-4 text-rose-500" />
                  ) : isWarn ? (
                    <AlertTriangle className="w-4 h-4 text-amber-500" />
                  ) : (
                    <Info className="w-4 h-4 text-blue-500" />
                  )}
                </div>

                {/* Details */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="font-mono font-bold text-slate-800 dark:text-slate-200">
                      t={inc.timestamp.toFixed(1)}s
                    </span>
                    <span className="font-mono px-1.5 py-0.2 rounded text-[10px] bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                      {inc.entity}
                    </span>
                    <span className={`text-[10px] font-mono uppercase font-bold ${
                      isCrit ? 'text-rose-600 dark:text-rose-400' :
                      isWarn ? 'text-amber-600 dark:text-amber-400' :
                      'text-blue-600 dark:text-blue-400'
                    }`}>
                      {inc.severity}
                    </span>
                    {inc.fault && (
                      <span className="text-[10px] font-mono text-slate-500">
                        [{inc.fault}]
                      </span>
                    )}
                  </div>
                  <p className="text-slate-600 dark:text-slate-300 text-[11px] leading-relaxed break-words">
                    {inc.message}
                  </p>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
