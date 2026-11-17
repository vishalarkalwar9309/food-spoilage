import React, { useState } from 'react';
import { StorageSession, FoodProfile } from '../types';
import { Clock, Play, Square, History, PlusCircle, CheckCircle2 } from 'lucide-react';

interface StorageSessionManagerProps {
  activeSession: StorageSession | null;
  sessions: StorageSession[];
  profiles: FoodProfile[];
  onStartSession: (foodProfileId: string, sessionName?: string) => Promise<void>;
  onEndSession: () => Promise<void>;
}

export const StorageSessionManager: React.FC<StorageSessionManagerProps> = ({
  activeSession,
  sessions,
  profiles,
  onStartSession,
  onEndSession
}) => {
  const [showModal, setShowModal] = useState<boolean>(false);
  const [sessionName, setSessionName] = useState<string>('');
  const [selectedProfileId, setSelectedProfileId] = useState<string>(profiles[0]?.id || 'rice');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const handleStart = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await onStartSession(selectedProfileId, sessionName || undefined);
      setSessionName('');
      setShowModal(false);
    } finally {
      setIsSubmitting(false);
    }
  };

  const calculateElapsed = (startTimeStr: string) => {
    try {
      const start = new Date(startTimeStr).getTime();
      const now = Date.now();
      const diffMs = Math.max(0, now - start);
      const diffHrs = Math.floor(diffMs / (1000 * 60 * 60));
      const diffMins = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
      return `${diffHrs}h ${diffMins}m`;
    } catch {
      return '--';
    }
  };

  return (
    <div className="bg-dark-900 border border-dark-700/80 rounded-xl p-5 lg:p-6 space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-dark-800 pb-3">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2 font-mono">
            <Clock className="w-5 h-5 text-cyan-400" />
            STORAGE SESSION LIFECYCLE
          </h3>
          <p className="text-xs text-slate-400">
            Track continuous batch storage duration and stress accumulation persisted in SQLite
          </p>
        </div>

        {/* Action Button */}
        {activeSession ? (
          <button
            onClick={onEndSession}
            className="flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-red-600/90 hover:bg-red-500 text-white font-mono text-xs font-bold transition shadow-sm"
          >
            <Square className="w-3.5 h-3.5 fill-current" /> End Active Session
          </button>
        ) : (
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-dark-950 font-mono text-xs font-bold transition shadow-sm"
          >
            <Play className="w-3.5 h-3.5 fill-current" /> Start New Session
          </button>
        )}
      </div>

      {/* Active Session Status Banner */}
      {activeSession ? (
        <div className="p-4 rounded-xl bg-dark-800 border border-cyan-500/30 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1 font-mono text-xs">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-slate-400">Active Storage Batch:</span>
              <strong className="text-white text-sm">{activeSession.session_name}</strong>
              <span className="px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
                {activeSession.food_name || activeSession.food_profile_id}
              </span>
            </div>
            <p className="text-slate-400">
              Started: {new Date(activeSession.start_time).toLocaleString()}
            </p>
          </div>

          <div className="flex items-center gap-6 font-mono text-xs">
            <div className="text-right">
              <span className="text-slate-400 block text-[11px]">Nominal Elapsed:</span>
              <span className="text-white font-bold text-sm">
                {calculateElapsed(activeSession.start_time)}
              </span>
            </div>
            <div className="text-right">
              <span className="text-slate-400 block text-[11px]">Effective Stress-Exposure:</span>
              <span className="text-amber-400 font-bold text-sm">
                {activeSession.accumulated_effective_hours.toFixed(2)} hrs
              </span>
            </div>
            <div className="text-right">
              <span className="text-slate-400 block text-[11px]">Readings Logged:</span>
              <span className="text-cyan-400 font-bold text-sm">
                {activeSession.total_readings_count}
              </span>
            </div>
          </div>
        </div>
      ) : (
        <div className="p-4 rounded-xl bg-dark-850/60 border border-dark-700 text-center font-mono text-xs text-slate-400 py-6">
          No active storage session. System is operating in unmanaged default monitoring state.
        </div>
      )}

      {/* Sessions History List */}
      <div>
        <h4 className="text-xs font-bold text-slate-300 font-mono flex items-center gap-2 mb-3">
          <History className="w-4 h-4 text-slate-400" />
          SESSION HISTORY LOG (SQLITE)
        </h4>

        <div className="overflow-x-auto max-h-52 rounded-lg border border-dark-700/60">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-dark-800 text-slate-400 border-b border-dark-700">
              <tr>
                <th className="py-2.5 px-3">ID</th>
                <th className="py-2.5 px-3">Batch Name</th>
                <th className="py-2.5 px-3">Commodity</th>
                <th className="py-2.5 px-3">Start Time</th>
                <th className="py-2.5 px-3">End Time</th>
                <th className="py-2.5 px-3">Stress-Hours</th>
                <th className="py-2.5 px-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-dark-800 text-slate-300">
              {sessions.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-4 text-center text-slate-500">
                    No past sessions found.
                  </td>
                </tr>
              ) : (
                sessions.map((s) => (
                  <tr key={s.id} className="hover:bg-dark-800/40">
                    <td className="py-2 px-3 text-slate-400">#{s.id}</td>
                    <td className="py-2 px-3 font-semibold text-white">{s.session_name}</td>
                    <td className="py-2 px-3 text-cyan-300">{s.food_name || s.food_profile_id}</td>
                    <td className="py-2 px-3 text-slate-400">
                      {new Date(s.start_time).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                    </td>
                    <td className="py-2 px-3 text-slate-400">
                      {s.end_time ? new Date(s.end_time).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' }) : 'Active'}
                    </td>
                    <td className="py-2 px-3 text-amber-300 font-semibold">
                      {s.accumulated_effective_hours.toFixed(1)} hrs
                    </td>
                    <td className="py-2 px-3">
                      {s.is_active ? (
                        <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-950 text-emerald-400 border border-emerald-800 font-semibold">
                          ACTIVE
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-[10px] bg-dark-700 text-slate-400">
                          COMPLETED
                        </span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Start Session Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-dark-900 border border-dark-700 rounded-xl p-6 max-w-md w-full shadow-2xl font-mono text-xs">
            <h3 className="text-base font-bold text-white mb-1 flex items-center gap-2">
              <PlusCircle className="w-5 h-5 text-cyan-400" />
              START NEW STORAGE BATCH
            </h3>
            <p className="text-slate-400 mb-4">
              Select food commodity and initialize cumulative exposure tracking.
            </p>

            <form onSubmit={handleStart} className="space-y-4">
              <div>
                <label className="block text-slate-300 mb-1 font-semibold">Batch / Session Label:</label>
                <input
                  type="text"
                  placeholder="e.g. Rice Storage Chamber Batch #1"
                  value={sessionName}
                  onChange={(e) => setSessionName(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-dark-800 border border-dark-700 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-slate-300 mb-1 font-semibold">Food Commodity Profile:</label>
                <select
                  value={selectedProfileId}
                  onChange={(e) => setSelectedProfileId(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-dark-800 border border-dark-700 text-white focus:outline-none focus:border-cyan-500"
                >
                  {profiles.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} (Optimal: {p.temp_min}–{p.temp_max}°C, {p.humidity_min}–{p.humidity_max}% RH)
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-center justify-end space-x-3 pt-3 border-t border-dark-800">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 rounded-lg bg-dark-800 text-slate-300 hover:text-white border border-dark-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-dark-950 font-bold disabled:opacity-50"
                >
                  {isSubmitting ? 'Starting...' : 'Confirm & Start'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
