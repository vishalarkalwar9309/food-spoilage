import React from 'react';
import { AlertItem } from '../types';
import { Bell, ShieldAlert, AlertTriangle, Info, Check, CheckCheck } from 'lucide-react';

interface AlertsPanelProps {
  alerts: AlertItem[];
  onAcknowledge: (alertId: number) => Promise<void>;
  isLoading: boolean;
}

export const AlertsPanel: React.FC<AlertsPanelProps> = ({ alerts, onAcknowledge, isLoading }) => {
  const getSeverityStyle = (severity: string) => {
    switch (severity) {
      case 'Critical':
        return {
          border: 'border-red-500/40',
          bg: 'bg-red-950/20',
          badge: 'bg-red-950 text-red-400 border border-red-800',
          icon: ShieldAlert
        };
      case 'High':
        return {
          border: 'border-orange-500/40',
          bg: 'bg-orange-950/20',
          badge: 'bg-orange-950 text-orange-400 border border-orange-800',
          icon: AlertTriangle
        };
      case 'Moderate':
        return {
          border: 'border-amber-500/40',
          bg: 'bg-amber-950/20',
          badge: 'bg-amber-950 text-amber-400 border border-amber-800',
          icon: Info
        };
      default:
        return {
          border: 'border-emerald-500/40',
          bg: 'bg-emerald-950/20',
          badge: 'bg-emerald-950 text-emerald-400 border border-emerald-800',
          icon: Check
        };
    }
  };

  return (
    <div className="bg-dark-900 border border-dark-700/80 rounded-xl p-5 lg:p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-dark-800 pb-3">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2 font-mono">
            <Bell className="w-5 h-5 text-cyan-400" />
            INCIDENT ALERTS &amp; NOTIFICATIONS
          </h3>
          <p className="text-xs text-slate-400">
            Automated alerts dispatched when environmental spoilage risk severity escalates
          </p>
        </div>
        <span className="text-xs font-mono px-2 py-0.5 rounded bg-dark-800 text-slate-300 border border-dark-700">
          Total: {alerts.length}
        </span>
      </div>

      {/* Alerts Timeline / Feed */}
      {alerts.length === 0 ? (
        <div className="py-10 text-center text-slate-500 font-mono text-xs">
          No active alerts. All environmental conditions have stayed within acceptable baseline limits.
        </div>
      ) : (
        <div className="space-y-2.5 max-h-72 overflow-y-auto pr-1">
          {alerts.map((a) => {
            const style = getSeverityStyle(a.severity);
            const Icon = style.icon;
            return (
              <div
                key={a.id}
                className={`p-3.5 rounded-lg border ${style.border} ${style.bg} flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs font-mono transition`}
              >
                <div className="flex items-start gap-3">
                  <div className="p-1.5 rounded-md bg-dark-900 border border-dark-700 flex-shrink-0 mt-0.5">
                    <Icon className="w-4 h-4 text-white" />
                  </div>
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`px-2 py-0.2 rounded text-[10px] font-bold uppercase ${style.badge}`}>
                        {a.severity} RISK
                      </span>
                      <span className="text-slate-400 text-[11px]">
                        Triggered at: {new Date(a.timestamp).toLocaleString()}
                      </span>
                      <span className="text-amber-400 font-bold">
                        (Risk: {a.risk_score.toFixed(1)}%)
                      </span>
                    </div>
                    <p className="text-slate-300 leading-snug mt-1">{a.message}</p>
                  </div>
                </div>

                {/* Acknowledge Button */}
                <div className="self-end sm:self-center flex-shrink-0">
                  {a.acknowledged ? (
                    <span className="inline-flex items-center gap-1 text-[11px] text-emerald-400 font-semibold px-2 py-1 rounded bg-emerald-950/60 border border-emerald-900">
                      <CheckCheck className="w-3.5 h-3.5" /> Acknowledged
                    </span>
                  ) : (
                    <button
                      onClick={() => onAcknowledge(a.id)}
                      className="px-2.5 py-1 rounded bg-dark-800 hover:bg-dark-700 border border-dark-700 text-slate-300 hover:text-white transition"
                    >
                      Acknowledge
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
