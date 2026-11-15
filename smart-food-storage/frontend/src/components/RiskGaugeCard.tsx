import React from 'react';
import { AlertCircle, ShieldAlert, CheckCircle2, AlertTriangle, Info } from 'lucide-react';
import { RiskAssessment, FoodProfile } from '../types';

interface RiskGaugeCardProps {
  risk: RiskAssessment | null;
  profile: FoodProfile;
}

export const RiskGaugeCard: React.FC<RiskGaugeCardProps> = ({ risk, profile }) => {
  const score = risk ? Math.min(100, Math.max(0, risk.composite_score)) : 0;
  const category = risk?.category || 'Low';
  const recommendation = risk?.recommendation || 'No data recorded yet. Initialize session or start simulation.';

  // Color mapping based on category
  const colorMap = {
    Low: {
      bg: 'bg-emerald-500/10',
      border: 'border-emerald-500/30',
      text: 'text-emerald-400',
      fill: '#10B981',
      badgeBg: 'bg-emerald-950/80 text-emerald-400 border-emerald-800',
      icon: CheckCircle2,
      label: 'Low Risk (0–30%)'
    },
    Moderate: {
      bg: 'bg-amber-500/10',
      border: 'border-amber-500/30',
      text: 'text-amber-400',
      fill: '#F59E0B',
      badgeBg: 'bg-amber-950/80 text-amber-400 border-amber-800',
      icon: Info,
      label: 'Moderate Risk (31–60%)'
    },
    High: {
      bg: 'bg-orange-500/10',
      border: 'border-orange-500/30',
      text: 'text-orange-400',
      fill: '#F97316',
      badgeBg: 'bg-orange-950/80 text-orange-400 border-orange-800',
      icon: AlertTriangle,
      label: 'High Risk (61–80%)'
    },
    Critical: {
      bg: 'bg-red-500/10',
      border: 'border-red-500/30',
      text: 'text-red-400',
      fill: '#EF4444',
      badgeBg: 'bg-red-950/80 text-red-400 border-red-800',
      icon: ShieldAlert,
      label: 'Critical Risk (81–100%)'
    }
  };

  const theme = colorMap[category] || colorMap.Low;
  const IconComponent = theme.icon;

  // Component scores
  const ts = risk?.components?.temp_score ?? 0;
  const hs = risk?.components?.humidity_score ?? 0;
  const gs = risk?.components?.gas_score ?? 0;
  const ds = risk?.components?.duration_score ?? 0;

  // Circumference for SVG gauge circle
  const radius = 68;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <div className={`rounded-xl border ${theme.border} ${theme.bg} p-5 lg:p-6 transition-colors duration-300 relative overflow-hidden backdrop-blur-sm`}>
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-dark-700/60 pb-4 mb-5">
        <div>
          <span className="text-xs uppercase tracking-wider text-slate-400 font-mono">
            Composite Spoilage Risk Engine
          </span>
          <h2 className="text-lg lg:text-xl font-bold text-white flex items-center gap-2">
            Target Commodity: <span className="text-cyan-400">{profile.name}</span>
            {profile.scientific_name && (
              <span className="text-xs font-normal italic text-slate-400">({profile.scientific_name})</span>
            )}
          </h2>
        </div>

        <div className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-semibold border ${theme.badgeBg}`}>
          <IconComponent className="w-3.5 h-3.5" />
          <span>{category.toUpperCase()} RISK STATE</span>
        </div>
      </div>

      {/* Main Grid: Gauge Circle + Breakdown + Recommendations */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
        {/* Prominent Radial Gauge */}
        <div className="md:col-span-4 flex flex-col items-center justify-center p-2">
          <div className="relative w-44 h-44 flex items-center justify-center">
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 160 160">
              {/* Background Track */}
              <circle
                cx="80"
                cy="80"
                r={radius}
                stroke="#1E293B"
                strokeWidth="12"
                fill="transparent"
              />
              {/* Active Progress Arc */}
              <circle
                cx="80"
                cy="80"
                r={radius}
                stroke={theme.fill}
                strokeWidth="12"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
                fill="transparent"
                className="transition-all duration-700 ease-out"
              />
            </svg>
            {/* Center Value */}
            <div className="absolute flex flex-col items-center justify-center text-center">
              <span className={`text-4xl font-black font-mono tracking-tight ${theme.text}`}>
                {score.toFixed(1)}%
              </span>
              <span className="text-xs uppercase tracking-widest text-slate-400 font-mono mt-0.5">
                Risk Score
              </span>
            </div>
          </div>

          <span className="text-xs text-slate-400 mt-2 font-mono text-center">
            Scale: 0% (Optimal) to 100% (Critical)
          </span>
        </div>

        {/* Component Risk Breakdown Bars */}
        <div className="md:col-span-8 flex flex-col justify-center space-y-3.5">
          <div className="flex items-center justify-between text-xs font-mono text-slate-300">
            <span>Mathematical Model Parameters:</span>
            <span className="text-slate-400">R = (Ts·0.30) + (Hs·0.25) + (Gs·0.25) + (Ds·0.20)</span>
          </div>

          {/* Ts: Temperature Score */}
          <div className="space-y-1">
            <div className="flex justify-between text-xs font-mono">
              <span className="text-slate-300">
                <strong className="text-cyan-400">Ts</strong> — Temperature Deviation Score (Weight: 30%)
              </span>
              <span className="font-semibold text-slate-200">{ts.toFixed(1)} / 100</span>
            </div>
            <div className="h-2 w-full bg-dark-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-cyan-400 transition-all duration-500 rounded-full"
                style={{ width: `${Math.min(100, Math.max(0, ts))}%` }}
              />
            </div>
          </div>

          {/* Hs: Humidity Score */}
          <div className="space-y-1">
            <div className="flex justify-between text-xs font-mono">
              <span className="text-slate-300">
                <strong className="text-blue-400">Hs</strong> — Relative Humidity Deviation Score (Weight: 25%)
              </span>
              <span className="font-semibold text-slate-200">{hs.toFixed(1)} / 100</span>
            </div>
            <div className="h-2 w-full bg-dark-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-400 transition-all duration-500 rounded-full"
                style={{ width: `${Math.min(100, Math.max(0, hs))}%` }}
              />
            </div>
          </div>

          {/* Gs: Gas Score */}
          <div className="space-y-1">
            <div className="flex justify-between text-xs font-mono">
              <span className="text-slate-300">
                <strong className="text-purple-400">Gs</strong> — MQ-135 Volatile Gas Response Score (Weight: 25%)
              </span>
              <span className="font-semibold text-slate-200">{gs.toFixed(1)} / 100</span>
            </div>
            <div className="h-2 w-full bg-dark-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-purple-400 transition-all duration-500 rounded-full"
                style={{ width: `${Math.min(100, Math.max(0, gs))}%` }}
              />
            </div>
          </div>

          {/* Ds: Duration Score */}
          <div className="space-y-1">
            <div className="flex justify-between text-xs font-mono">
              <span className="text-slate-300">
                <strong className="text-amber-400">Ds</strong> — Cumulative Stress Exposure Duration Score (Weight: 20%)
              </span>
              <span className="font-semibold text-slate-200">{ds.toFixed(1)} / 100</span>
            </div>
            <div className="h-2 w-full bg-dark-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-amber-400 transition-all duration-500 rounded-full"
                style={{ width: `${Math.min(100, Math.max(0, ds))}%` }}
              />
            </div>
          </div>

          {/* Recommendation Banner */}
          <div className="mt-2 p-3 rounded-lg bg-dark-900/80 border border-dark-700 text-xs">
            <div className="flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-cyan-400 flex-shrink-0 mt-0.5" />
              <div>
                <strong className="text-slate-200">Preservation Guidance: </strong>
                <span className="text-slate-300">{recommendation}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
