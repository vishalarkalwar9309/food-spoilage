import React from 'react';
import { Thermometer, Droplets, Wind, Clock, TrendingUp, Check, AlertTriangle } from 'lucide-react';
import { SensorReading, FoodProfile, StorageSession, RiskAssessment } from '../types';

interface MetricCardClusterProps {
  reading: SensorReading | null;
  profile: FoodProfile;
  session: StorageSession | null;
  risk: RiskAssessment | null;
}

export const MetricCardCluster: React.FC<MetricCardClusterProps> = ({
  reading,
  profile,
  session,
  risk
}) => {
  const temp = reading?.temperature ?? 0;
  const humidity = reading?.humidity ?? 0;
  const gas = reading?.gas ?? 0;

  // Temperature status
  const isTempOptimal = temp >= profile.temp_min && temp <= profile.temp_max;
  const tempDiff = temp > profile.temp_max
    ? `+${(temp - profile.temp_max).toFixed(1)}°C Above Max`
    : temp < profile.temp_min
    ? `-${(profile.temp_min - temp).toFixed(1)}°C Below Min`
    : 'Within Optimal Range';

  // Humidity status
  const isHumOptimal = humidity >= profile.humidity_min && humidity <= profile.humidity_max;
  const humDiff = humidity > profile.humidity_max
    ? `+${(humidity - profile.humidity_max).toFixed(1)}% Saturation Risk`
    : humidity < profile.humidity_min
    ? `-${(profile.humidity_min - humidity).toFixed(1)}% Desiccation Risk`
    : 'Optimal Humidity Envelope';

  // Gas status
  const isGasElevated = gas > profile.gas_threshold;
  const gasPercentOfThreshold = Math.min(100, Math.round((gas / profile.gas_threshold) * 100));

  // Duration
  const effectiveHours = risk?.effective_exposure_hours ?? (session?.accumulated_effective_hours ?? 0);
  const idealShelfLife = profile.ideal_shelf_life_hours || 168;
  const shelfLifeUsedPercent = Math.min(100, Math.round((effectiveHours / idealShelfLife) * 100));

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* 1. Temperature Card */}
      <div className="bg-dark-900 border border-dark-700/80 hover:border-cyan-500/40 rounded-xl p-4 transition-all duration-200 shadow-sm flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between text-xs text-slate-400 font-mono mb-2">
            <span className="flex items-center gap-1.5">
              <Thermometer className="w-4 h-4 text-cyan-400" />
              TEMPERATURE
            </span>
            <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${isTempOptimal ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-red-950 text-red-400 border border-red-800'}`}>
              {isTempOptimal ? 'OPTIMAL' : 'DEVIATED'}
            </span>
          </div>

          <div className="flex items-baseline space-x-2 mt-1">
            <span className="text-3xl font-black font-mono text-white">
              {reading ? temp.toFixed(1) : '--'}
            </span>
            <span className="text-slate-400 text-sm font-mono">°C</span>
          </div>
        </div>

        <div className="mt-4 pt-3 border-t border-dark-800 text-[11px] font-mono space-y-1">
          <div className="flex justify-between text-slate-400">
            <span>Optimal Window:</span>
            <span className="text-cyan-300 font-semibold">{profile.temp_min} – {profile.temp_max}°C</span>
          </div>
          <div className={`text-[10px] font-semibold ${isTempOptimal ? 'text-emerald-400' : 'text-amber-400'}`}>
            {tempDiff}
          </div>
        </div>
      </div>

      {/* 2. Humidity Card */}
      <div className="bg-dark-900 border border-dark-700/80 hover:border-blue-500/40 rounded-xl p-4 transition-all duration-200 shadow-sm flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between text-xs text-slate-400 font-mono mb-2">
            <span className="flex items-center gap-1.5">
              <Droplets className="w-4 h-4 text-blue-400" />
              RELATIVE HUMIDITY
            </span>
            <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${isHumOptimal ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-amber-950 text-amber-400 border border-amber-800'}`}>
              {isHumOptimal ? 'OPTIMAL' : 'DEVIATED'}
            </span>
          </div>

          <div className="flex items-baseline space-x-2 mt-1">
            <span className="text-3xl font-black font-mono text-white">
              {reading ? humidity.toFixed(1) : '--'}
            </span>
            <span className="text-slate-400 text-sm font-mono">% RH</span>
          </div>
        </div>

        <div className="mt-4 pt-3 border-t border-dark-800 text-[11px] font-mono space-y-1">
          <div className="flex justify-between text-slate-400">
            <span>Target Envelope:</span>
            <span className="text-blue-300 font-semibold">{profile.humidity_min} – {profile.humidity_max}%</span>
          </div>
          <div className={`text-[10px] font-semibold ${isHumOptimal ? 'text-emerald-400' : 'text-amber-400'}`}>
            {humDiff}
          </div>
        </div>
      </div>

      {/* 3. MQ-135 Gas Sensor Card */}
      <div className="bg-dark-900 border border-dark-700/80 hover:border-purple-500/40 rounded-xl p-4 transition-all duration-200 shadow-sm flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between text-xs text-slate-400 font-mono mb-2">
            <span className="flex items-center gap-1.5">
              <Wind className="w-4 h-4 text-purple-400" />
              MQ-135 GAS SENSOR
            </span>
            <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${isGasElevated ? 'bg-red-950 text-red-400 border border-red-800' : 'bg-emerald-950 text-emerald-400 border border-emerald-800'}`}>
              {isGasElevated ? 'ELEVATED' : 'BASELINE'}
            </span>
          </div>

          <div className="flex items-baseline space-x-2 mt-1">
            <span className="text-3xl font-black font-mono text-white">
              {reading ? Math.round(gas) : '--'}
            </span>
            <span className="text-slate-400 text-xs font-mono">ADC Count</span>
          </div>
        </div>

        <div className="mt-4 pt-3 border-t border-dark-800 text-[11px] font-mono space-y-1">
          <div className="flex justify-between text-slate-400">
            <span>Calibrated Baseline:</span>
            <span className="text-purple-300 font-semibold">{profile.gas_baseline} ADC</span>
          </div>
          <div className="flex justify-between text-slate-400">
            <span>Senescence Threshold:</span>
            <span className="text-purple-400 font-semibold">{profile.gas_threshold} ADC</span>
          </div>
        </div>
      </div>

      {/* 4. Cumulative Storage Duration Card */}
      <div className="bg-dark-900 border border-dark-700/80 hover:border-amber-500/40 rounded-xl p-4 transition-all duration-200 shadow-sm flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between text-xs text-slate-400 font-mono mb-2">
            <span className="flex items-center gap-1.5">
              <Clock className="w-4 h-4 text-amber-400" />
              EXPOSURE PERSISTENCE
            </span>
            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-dark-800 text-amber-400 border border-dark-700">
              {session?.is_active ? 'ACTIVE SESSION' : 'DEFAULT'}
            </span>
          </div>

          <div className="flex items-baseline space-x-2 mt-1">
            <span className="text-3xl font-black font-mono text-white">
              {effectiveHours.toFixed(1)}
            </span>
            <span className="text-slate-400 text-xs font-mono">Effective Hrs</span>
          </div>
        </div>

        <div className="mt-4 pt-3 border-t border-dark-800 text-[11px] font-mono space-y-1">
          <div className="flex justify-between text-slate-400">
            <span>Ideal Shelf Life:</span>
            <span className="text-amber-300 font-semibold">{idealShelfLife} hrs</span>
          </div>
          <div className="w-full bg-dark-800 h-1.5 rounded-full overflow-hidden mt-1">
            <div
              className="bg-amber-400 h-full rounded-full transition-all duration-500"
              style={{ width: `${shelfLifeUsedPercent}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
