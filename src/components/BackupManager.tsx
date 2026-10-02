import React, { useState } from 'react';
import { TelemetryData, UserRole } from '../types';
import { roleAllows } from '../permissions';
import { Cloud, Download, Upload, CheckCircle, Database, HardDrive, Shield } from 'lucide-react';

interface BackupManagerProps {
  telemetry: TelemetryData;
  onRestoreSnapshot: (data: any) => void;
  currentUserRole: UserRole;
  isOnline: boolean;
}

export const BackupManager: React.FC<BackupManagerProps> = ({
  telemetry,
  onRestoreSnapshot,
  currentUserRole,
  isOnline,
}) => {
  const [restoreMessage, setRestoreMessage] = useState<string | null>(null);

  const handleDownloadSnapshot = () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(telemetry, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `ResilientEdge_Snapshot_${Date.now()}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const parsed = JSON.parse(event.target?.result as string);
        onRestoreSnapshot(parsed);
        setRestoreMessage('Snapshot restored successfully.');
        setTimeout(() => setRestoreMessage(null), 4000);
      } catch (err) {
        setRestoreMessage('Error: Invalid JSON snapshot file.');
      }
    };
    reader.readAsText(file);
  };

  const canManage = roleAllows(currentUserRole, 'destructive');

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
          <Cloud className="w-4 h-4 text-blue-500" />
          Cloud Backup &amp; Offline Data Synchronization
        </h2>
        <p className="text-xs text-slate-500">
          Export persistent telemetry snapshots, restore prior fleet configurations, and manage offline data state.
        </p>
      </div>

      {restoreMessage && (
        <div className="p-3 rounded-lg bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300 text-xs flex items-center gap-2">
          <CheckCircle className="w-4 h-4 text-emerald-500" />
          {restoreMessage}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
        {/* Export / Backup */}
        <div className="bg-white dark:bg-slate-900 rounded-xl p-4 border border-slate-200 dark:border-slate-800 space-y-3">
          <div className="flex items-center gap-2 font-bold text-slate-900 dark:text-slate-100">
            <Download className="w-4 h-4 text-blue-500" />
            Export System Snapshot
          </div>
          <p className="text-slate-500 text-[11px] leading-relaxed">
            Downloads a timestamped JSON snapshot containing active robot coordinates, battery levels, task allocation states, and incidents.
          </p>

          <button
            onClick={handleDownloadSnapshot}
            className="w-full py-2 bg-slate-900 dark:bg-blue-600 hover:bg-slate-800 text-white rounded-lg font-medium transition-colors cursor-pointer flex items-center justify-center gap-2"
          >
            <Download className="w-3.5 h-3.5" />
            Download Snapshot JSON
          </button>
        </div>

        {/* Restore / Import */}
        <div className="bg-white dark:bg-slate-900 rounded-xl p-4 border border-slate-200 dark:border-slate-800 space-y-3">
          <div className="flex items-center gap-2 font-bold text-slate-900 dark:text-slate-100">
            <Upload className="w-4 h-4 text-amber-500" />
            Restore Fleet Snapshot
          </div>
          <p className="text-slate-500 text-[11px] leading-relaxed">
            Upload an existing ResilientEdge state backup to restore fleet positions, world configurations, and active task queues.
          </p>

          <label className={`w-full py-2 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 rounded-lg font-medium transition-colors flex items-center justify-center gap-2 text-slate-800 dark:text-slate-200 ${canManage ? 'cursor-pointer' : 'opacity-40 cursor-not-allowed'}`}>
            <Upload className="w-3.5 h-3.5 text-slate-500" />
            Upload Snapshot File
            <input
              type="file"
              accept=".json"
              disabled={!canManage}
              onChange={handleFileUpload}
              className="hidden"
            />
          </label>
        </div>
      </div>

      {/* Persistence Architecture Status */}
      <div className="bg-white dark:bg-slate-900 rounded-xl p-4 border border-slate-200 dark:border-slate-800 text-xs space-y-2">
        <h3 className="font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
          <Database className="w-4 h-4 text-blue-500" />
          Persistence &amp; Storage Architecture Status
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-2">
          <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700">
            <span className="text-[11px] text-slate-500 block">Database Engine</span>
            <span className="font-mono font-bold text-slate-900 dark:text-slate-100">SQLite 3</span>
            <span className="text-[10px] text-emerald-600 dark:text-emerald-400 block mt-0.5">./data/resilientedge.db</span>
          </div>

          <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700">
            <span className="text-[11px] text-slate-500 block">Local Client Cache</span>
            <span className="font-mono font-bold text-slate-900 dark:text-slate-100">LocalStorage Active</span>
            <span className="text-[10px] text-emerald-600 dark:text-emerald-400 block mt-0.5">Continuous Sync</span>
          </div>

          <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700">
            <span className="text-[11px] text-slate-500 block">Offline Resiliency</span>
            <span className="font-mono font-bold text-slate-900 dark:text-slate-100">Offline-capable local cache</span>
            <span className="text-[10px] text-emerald-600 dark:text-emerald-400 block mt-0.5">{isOnline ? 'Online (Real Telemetry)' : 'Offline (Cached Mode)'}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
