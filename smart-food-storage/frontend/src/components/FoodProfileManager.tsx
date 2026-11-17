import React, { useState } from 'react';
import { FoodProfile, StorageSession } from '../types';
import { Wheat, Apple, Package, Layers, Check, Play, AlertCircle, Sparkles } from 'lucide-react';

interface FoodProfileManagerProps {
  profiles: FoodProfile[];
  activeProfile: FoodProfile;
  activeSession: StorageSession | null;
  onSelectProfile: (profileId: string) => Promise<void>;
  isStartingSession: boolean;
}

export const FoodProfileManager: React.FC<FoodProfileManagerProps> = ({
  profiles,
  activeProfile,
  activeSession,
  onSelectProfile,
  isStartingSession
}) => {
  const [selectedId, setSelectedId] = useState<string>(activeProfile.id);

  // Icon mapper for the 3 food modes
  const getIcon = (id: string) => {
    switch (id) {
      case 'normal':
        return <Package className="w-5 h-5 text-cyan-400" />;
      case 'fruits_and_snacks':
        return <Apple className="w-5 h-5 text-emerald-400" />;
      case 'rice':
        return <Wheat className="w-5 h-5 text-amber-400" />;
      default:
        return <Layers className="w-5 h-5 text-slate-400" />;
    }
  };

  const getAdjustmentBadge = (adj?: number) => {
    if (adj === undefined) return null;
    const isPositive = adj > 0;
    const sign = isPositive ? `+${adj}%` : `${adj}%`;
    return (
      <span
        className={`inline-flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded font-bold border ${
          adj < 0
            ? 'bg-emerald-950/70 text-emerald-300 border-emerald-700/60'
            : 'bg-amber-950/70 text-amber-300 border-amber-700/60'
        }`}
        title="Demonstration risk score adjustment applied to base score"
      >
        <Sparkles className="w-3 h-3" />
        {sign} Demo Adj
      </span>
    );
  };

  const handleActivate = async (profileId: string) => {
    setSelectedId(profileId);
    await onSelectProfile(profileId);
  };

  return (
    <div className="bg-dark-900 border border-dark-700/80 rounded-xl p-5 lg:p-6 space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-dark-800 pb-3">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2 font-mono">
            <Layers className="w-5 h-5 text-cyan-400" />
            FOOD STORAGE MODES &amp; COMMODITY PROFILES
          </h3>
          <p className="text-xs text-slate-400">
            Selectable commodity modes with calibrated psychrometric envelopes and demonstration risk adjustments
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-cyan-400 bg-cyan-950/60 border border-cyan-800/80 px-2.5 py-1 rounded">
            Active Mode: {activeProfile.name}
          </span>
          {activeProfile.mode_adjustment !== undefined && (
            <span
              className={`text-xs font-mono px-2 py-1 rounded border font-semibold ${
                activeProfile.mode_adjustment < 0
                  ? 'bg-emerald-950/60 text-emerald-300 border-emerald-800'
                  : 'bg-amber-950/60 text-amber-300 border-amber-800'
              }`}
            >
              {activeProfile.mode_adjustment > 0
                ? `+${activeProfile.mode_adjustment}%`
                : `${activeProfile.mode_adjustment}%`}{' '}
              Adj
            </span>
          )}
        </div>
      </div>

      {/* Grid of Exactly Three Modes: Normal, Fruits & Snacks, Rice */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 lg:gap-5">
        {profiles.map((p) => {
          const isActive = activeProfile.id === p.id;
          return (
            <div
              key={p.id}
              className={`rounded-xl border p-4 lg:p-5 flex flex-col justify-between transition-all duration-200 ${
                isActive
                  ? 'bg-dark-800/90 border-cyan-500 shadow-md shadow-cyan-950/40 ring-1 ring-cyan-500/50'
                  : 'bg-dark-850/60 border-dark-700 hover:border-dark-600'
              }`}
            >
              <div>
                {/* Title, Icon & Badges */}
                <div className="flex items-center justify-between mb-3">
                  <div className="w-10 h-10 rounded-lg bg-dark-900 border border-dark-700 flex items-center justify-center">
                    {getIcon(p.id)}
                  </div>
                  <div className="flex items-center gap-1.5 flex-wrap justify-end">
                    {getAdjustmentBadge(p.mode_adjustment)}
                    {isActive && (
                      <span className="flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 font-semibold">
                        <Check className="w-3.5 h-3.5" /> ACTIVE
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex items-baseline justify-between">
                  <h4 className="text-base font-bold text-white font-mono">{p.name}</h4>
                  <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">{p.category}</span>
                </div>
                <p className="text-xs italic text-cyan-400/80 mb-3">{p.scientific_name}</p>

                {/* Parameters Matrix */}
                <div className="space-y-1.5 text-xs font-mono border-t border-dark-700/60 pt-3">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Optimal Temp:</span>
                    <span className="text-cyan-300 font-semibold">{p.temp_min} – {p.temp_max}°C</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Relative Humidity:</span>
                    <span className="text-blue-300 font-semibold">{p.humidity_min} – {p.humidity_max}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Ideal Shelf Life:</span>
                    <span className="text-amber-300 font-semibold">{p.ideal_shelf_life_hours} hrs</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Gas Threshold:</span>
                    <span className="text-purple-300 font-semibold">{p.gas_threshold} ADC</span>
                  </div>
                </div>

                <p className="text-[11px] text-slate-400 mt-3 leading-relaxed bg-dark-900/60 p-2.5 rounded-lg border border-dark-800">
                  {p.description}
                </p>
              </div>

              {/* Action Button */}
              <div className="mt-4 pt-3 border-t border-dark-700/50">
                <button
                  onClick={() => handleActivate(p.id)}
                  disabled={isActive || isStartingSession}
                  className={`w-full py-2 px-3 rounded-lg text-xs font-mono font-medium flex items-center justify-center gap-1.5 transition ${
                    isActive
                      ? 'bg-dark-700/40 text-slate-400 cursor-default'
                      : 'bg-cyan-600 hover:bg-cyan-500 text-dark-950 font-bold disabled:opacity-50'
                  }`}
                >
                  {isActive ? (
                    'Active Mode'
                  ) : (
                    <>
                      <Play className="w-3.5 h-3.5" /> Switch to {p.name}
                    </>
                  )}
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Scientific & Demonstration Reference Note */}
      <div className="flex items-start gap-2.5 text-[11px] text-slate-400 font-mono bg-dark-850 p-3 rounded-lg border border-dark-700/60">
        <AlertCircle className="w-4 h-4 text-cyan-400 flex-shrink-0 mt-0.5" />
        <div className="space-y-1">
          <div>
            <strong className="text-slate-300">Mode Reference:</strong> Normal (ambient shelf-stable grocery goods baseline); Fruits and Snacks (fresh produce / snacks per UC Davis Postharvest standards); Rice (cooked grains TCS perishable food per USDA/FDA Food Code).
          </div>
          <div className="text-cyan-400/90">
            <strong className="text-cyan-300">Demonstration Adjustment Notice:</strong> Mode offsets (Normal: -15%, Fruits &amp; Snacks: -10%, Rice: +5%) are applied to the physical base risk model for demonstration comparison: <code className="bg-dark-900 px-1 py-0.5 rounded text-white">display_score = clamp(base_score + mode_adj, 0, 100)</code>. Historical sensor telemetry is always preserved.
          </div>
        </div>
      </div>
    </div>
  );
};
