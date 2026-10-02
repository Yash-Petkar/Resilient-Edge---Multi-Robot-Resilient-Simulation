import React from 'react';
import { SimulationMetrics, RobotTelemetry, TaskTelemetry } from '../types';
import { BarChart3, Download, FileText, CheckCircle, Clock, Zap, Activity } from 'lucide-react';

interface MetricsDashboardProps {
  metrics: SimulationMetrics;
  robots: RobotTelemetry[];
  tasks: TaskTelemetry[];
  simTime: number;
}

export const MetricsDashboard: React.FC<MetricsDashboardProps> = ({
  metrics,
  robots,
  tasks,
  simTime,
}) => {
  // Export CSV
  const handleExportCSV = () => {
    const rows = [
      ['Metric', 'Value'],
      ['Timestamp (s)', simTime.toFixed(1)],
      ['Total Tasks', metrics.total_tasks],
      ['Completed Tasks', metrics.completed_tasks],
      ['Completion Rate (%)', metrics.task_completion_rate],
      ['Makespan (s)', metrics.makespan],
      ['Avg Waiting Time (s)', metrics.average_waiting_time],
      ['Avg Route Length', metrics.average_route_length],
      ['Conflicts Count', metrics.conflict_count],
      ['Deadlocks Count', metrics.deadlock_count],
      ['Failure Detection Latency (s)', metrics.failure_detection_time],
      ['Task Reassignment Latency (s)', metrics.task_reassignment_time],
      ['Messages Sent', metrics.messages_sent],
      ['Messages Dropped', metrics.messages_dropped],
      ['Degraded State Duration (s)', metrics.degraded_duration],
      ['Local Autonomy Duration (s)', metrics.local_autonomy_duration],
      ['Resync Duration (s)', metrics.resync_duration],
    ];

    const csvContent = 'data:text/csv;charset=utf-8,' + rows.map((e) => e.join(',')).join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `ResilientEdge_Report_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Export Printable Report / PDF
  const handleExportReport = () => {
    window.print();
  };

  return (
    <div className="space-y-4">
      {/* Header and export buttons */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-blue-500" />
            Analytical Telemetry &amp; System Performance
          </h2>
          <p className="text-xs text-slate-500">
            Real-time event-driven KPIs, latency profiles, and compliance metrics.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleExportCSV}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 font-medium text-xs shadow-2xs transition-colors cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            Export CSV
          </button>

          <button
            onClick={handleExportReport}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-medium text-xs shadow-sm transition-colors cursor-pointer"
          >
            <FileText className="w-3.5 h-3.5" />
            Export Printable PDF / Report
          </button>
        </div>
      </div>

      {/* Primary KPI Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-white dark:bg-slate-900 rounded-xl p-3.5 border border-slate-200 dark:border-slate-800">
          <span className="text-[11px] text-slate-500 block mb-1">Completion Rate</span>
          <div className="text-xl font-bold font-mono text-slate-900 dark:text-slate-100">
            {metrics.task_completion_rate}%
          </div>
          <span className="text-[10px] text-slate-400 font-mono">
            {metrics.completed_tasks} of {metrics.total_tasks} tasks
          </span>
        </div>

        <div className="bg-white dark:bg-slate-900 rounded-xl p-3.5 border border-slate-200 dark:border-slate-800">
          <span className="text-[11px] text-slate-500 block mb-1">Makespan Duration</span>
          <div className="text-xl font-bold font-mono text-slate-900 dark:text-slate-100">
            {metrics.makespan}s
          </div>
          <span className="text-[10px] text-slate-400 font-mono">Elapsed simulation time</span>
        </div>

        <div className="bg-white dark:bg-slate-900 rounded-xl p-3.5 border border-slate-200 dark:border-slate-800">
          <span className="text-[11px] text-slate-500 block mb-1">Failure Detection Latency</span>
          <div className="text-xl font-bold font-mono text-slate-900 dark:text-slate-100">
            {metrics.failure_detection_time}s
          </div>
          <span className="text-[10px] text-slate-400 font-mono">Heartbeat drop threshold</span>
        </div>

        <div className="bg-white dark:bg-slate-900 rounded-xl p-3.5 border border-slate-200 dark:border-slate-800">
          <span className="text-[11px] text-slate-500 block mb-1">Reassignment Duration</span>
          <div className="text-xl font-bold font-mono text-slate-900 dark:text-slate-100">
            {metrics.task_reassignment_time}s
          </div>
          <span className="text-[10px] text-slate-400 font-mono">Autonomous task handoff</span>
        </div>
      </div>

      {/* Network & Resilience Durations */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
        {/* Network Throughput */}
        <div className="bg-white dark:bg-slate-900 rounded-xl p-4 border border-slate-200 dark:border-slate-800 space-y-3">
          <h3 className="font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Activity className="w-4 h-4 text-blue-500" />
            Network Message Protocol Telemetry
          </h3>

          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-slate-500">Messages Sent:</span>
              <span className="font-mono font-bold text-slate-900 dark:text-slate-100">
                {metrics.messages_sent}
              </span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-slate-500">Messages Dropped (Packet Loss):</span>
              <span className="font-mono font-bold text-rose-600 dark:text-rose-400">
                {metrics.messages_dropped}
              </span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-slate-500">Delivery Reliability:</span>
              <span className="font-mono font-bold text-emerald-600 dark:text-emerald-400">
                {metrics.messages_sent > 0
                  ? (((metrics.messages_sent - metrics.messages_dropped) / metrics.messages_sent) * 100).toFixed(1)
                  : '100.0'}%
              </span>
            </div>
          </div>
        </div>

        {/* Resilience State Profile */}
        <div className="bg-white dark:bg-slate-900 rounded-xl p-4 border border-slate-200 dark:border-slate-800 space-y-3">
          <h3 className="font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Clock className="w-4 h-4 text-emerald-500" />
            Resilience State Machine Durations
          </h3>

          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-slate-500">Degraded Duration:</span>
              <span className="font-mono font-semibold text-amber-600 dark:text-amber-400">
                {metrics.degraded_duration}s
              </span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-slate-500">Local Autonomy Duration:</span>
              <span className="font-mono font-semibold text-purple-600 dark:text-purple-400">
                {metrics.local_autonomy_duration}s
              </span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-slate-500">Resynchronization Latency:</span>
              <span className="font-mono font-semibold text-blue-600 dark:text-blue-400">
                {metrics.resync_duration}s
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
