import React, { useState } from 'react';
import { FoodProfile, StorageSession } from '../types';
import { Apple, Leaf, Banana, Layers, Check, Play, AlertCircle } from 'lucide-react';

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

  // Icon mapper
  const getIcon = (id: string) => {
    switch (id) {
      case 'tomatoes':
        return <Apple className="w-5 h-5 text-red-400" />;
      case 'bananas':
        return <Banana className="w-5 h-5 text-amber-400" />;
      case 'apples':
        return <Apple className="w-5 h-5 text-emerald-400" />;
      case 'leafy_vegetables':
        return <Leaf className="w-5 h-5 text-green-400" />;
      default:
        return <Layers className="w-5 h-5 text-cyan-400" />;
    }
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
            COMMODITY-SPECIFIC STORAGE PROFILES
          </h3>
          <p className="text-xs text-slate-400">
            Psychrometric envelopes and metabolic baselines adapted to specific post-harvest produce physiology
          </p>
        </div>
        <span className="text-xs font-mono text-cyan-400 bg-cyan-950/60 border border-cyan-800/80 px-2.5 py-1 rounded">
          Active: {activeProfile.name}
        </span>
      </div>

      {/* Grid of 4 Profiles */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {profiles.map((p) => {
          const isActive = activeProfile.id === p.id;
          return (
            <div
              key={p.id}
              className={`rounded-xl border p-4 flex flex-col justify-between transition-all duration-200 ${
                isActive
                  ? 'bg-dark-800/90 border-cyan-500 shadow-md shadow-cyan-950/40 ring-1 ring-cyan-500/50'
                  : 'bg-dark-850/60 border-dark-700 hover:border-dark-600'
              }`}
            >
              <div>
                {/* Title & Icon */}
                <div className="flex items-center justify-between mb-2">
                  <div className="w-9 h-9 rounded-lg bg-dark-900 border border-dark-700 flex items-center justify-center">
                    {getIcon(p.id)}
                  </div>
                  {isActive ? (
                    <span className="flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 font-semibold">
                      <Check className="w-3 h-3" /> ACTIVE
                    </span>
                  ) : null}
                </div>

                <h4 className="text-sm font-bold text-white font-mono">{p.name}</h4>
                <p className="text-[11px] italic text-slate-400 mb-3">{p.scientific_name}</p>

                {/* Parameters Matrix */}
                <div className="space-y-1.5 text-xs font-mono border-t border-dark-700/60 pt-2.5">
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

                <p className="text-[11px] text-slate-400 mt-3 line-clamp-2 leading-relaxed">
                  {p.description}
                </p>
              </div>

              {/* Action Button */}
              <div className="mt-4 pt-3 border-t border-dark-700/50">
                <button
                  onClick={() => handleActivate(p.id)}
                  disabled={isActive || isStartingSession}
                  className={`w-full py-1.5 px-3 rounded-lg text-xs font-mono font-medium flex items-center justify-center gap-1.5 transition ${
                    isActive
                      ? 'bg-dark-700/40 text-slate-400 cursor-default'
                      : 'bg-cyan-600 hover:bg-cyan-500 text-dark-950 font-bold disabled:opacity-50'
                  }`}
                >
                  {isActive ? (
                    'Monitoring Profile'
                  ) : (
                    <>
                      <Play className="w-3.5 h-3.5" /> Select Profile
                    </>
                  )}
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Note */}
      <div className="flex items-center gap-2 text-[11px] text-slate-400 font-mono bg-dark-850 p-2.5 rounded-lg border border-dark-700/60">
        <AlertCircle className="w-4 h-4 text-slate-400 flex-shrink-0" />
        <span>
          Note: Psychrometric parameters reflect standard post-harvest recommendations; actual shelf life varies with cultivar, maturity grade, and ambient atmospheric pre-cooling.
        </span>
      </div>
    </div>
  );
};
