import React, { useState } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceArea,
  ReferenceLine
} from 'recharts';
import { TelemetryPoint, FoodProfile } from '../types';
import { Calendar, BarChart3, Thermometer, Droplets, Wind, ShieldAlert } from 'lucide-react';

interface HistoricalAnalyticsProps {
  data: TelemetryPoint[];
  profile: FoodProfile;
  selectedRange: '1h' | '24h' | '7d';
  onRangeChange: (range: '1h' | '24h' | '7d') => void;
  isLoading: boolean;
}

export const HistoricalAnalytics: React.FC<HistoricalAnalyticsProps> = ({
  data,
  profile,
  selectedRange,
  onRangeChange,
  isLoading
}) => {
  const [activeTab, setActiveTab] = useState<'all' | 'temp' | 'humidity' | 'gas' | 'risk'>('all');

  // Format timestamp for chart X-axis
  const formattedData = data.map((pt) => {
    const d = new Date(pt.timestamp);
    const timeStr = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const dateStr = `${d.getMonth() + 1}/${d.getDate()} ${timeStr}`;
    return {
      ...pt,
      displayTime: selectedRange === '7d' ? dateStr : timeStr
    };
  });

  // Custom Dark Tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const p = payload[0].payload;
      return (
        <div className="bg-dark-900 border border-dark-700 p-3 rounded-lg shadow-xl text-xs font-mono space-y-1">
          <p className="text-slate-400 font-semibold mb-1.5 border-b border-dark-800 pb-1">{p.displayTime}</p>
          <p className="text-cyan-400 flex items-center justify-between gap-4">
            <span>Temperature:</span>
            <strong>{p.temperature?.toFixed(1)}°C</strong>
          </p>
          <p className="text-blue-400 flex items-center justify-between gap-4">
            <span>Humidity:</span>
            <strong>{p.humidity?.toFixed(1)}%</strong>
          </p>
          <p className="text-purple-400 flex items-center justify-between gap-4">
            <span>Gas (MQ-135):</span>
            <strong>{Math.round(p.gas)} ADC</strong>
          </p>
          <p className="text-amber-400 flex items-center justify-between gap-4 border-t border-dark-800 pt-1">
            <span>Spoilage Risk:</span>
            <strong>{p.composite_risk?.toFixed(1)}% ({p.risk_category || 'N/A'})</strong>
          </p>
          <p className="text-[10px] text-slate-500 uppercase">Source: {p.source}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-dark-900 border border-dark-700/80 rounded-xl p-5 lg:p-6 space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-dark-800 pb-4">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2 font-mono">
            <BarChart3 className="w-5 h-5 text-cyan-400" />
            HISTORICAL ANALYTICS &amp; SENSOR KINETICS
          </h3>
          <p className="text-xs text-slate-400">
            Real-time psychrometric and metabolic degradation trajectories retrieved from SQLite
          </p>
        </div>

        {/* Range Buttons */}
        <div className="flex items-center space-x-1.5 bg-dark-800 p-1 rounded-lg border border-dark-700 self-start sm:self-auto">
          {(['1h', '24h', '7d'] as const).map((r) => (
            <button
              key={r}
              onClick={() => onRangeChange(r)}
              className={`px-3 py-1 rounded text-xs font-mono font-medium transition ${
                selectedRange === r
                  ? 'bg-cyan-500 text-dark-950 font-bold shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {r === '1h' ? 'Last 1 Hour' : r === '24h' ? 'Last 24 Hours' : 'Last 7 Days'}
            </button>
          ))}
        </div>
      </div>

      {formattedData.length === 0 ? (
        <div className="py-16 text-center text-slate-500 font-mono text-xs">
          No historical telemetry points stored yet. Start the sensor simulator or send ESP32 readings.
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Chart 1: Temperature (°C) */}
          <div className="bg-dark-850 p-4 rounded-xl border border-dark-700/60 flex flex-col justify-between">
            <div className="flex items-center justify-between mb-3 text-xs font-mono">
              <span className="flex items-center gap-1.5 text-cyan-400 font-bold">
                <Thermometer className="w-4 h-4" /> TEMPERATURE HISTORY (°C)
              </span>
              <span className="text-[11px] text-slate-400">
                Safe Band: {profile.temp_min}–{profile.temp_max}°C
              </span>
            </div>
            <div className="h-56 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={formattedData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                  <XAxis dataKey="displayTime" stroke="#64748B" fontSize={10} tickLine={false} />
                  <YAxis
                    stroke="#64748B"
                    fontSize={10}
                    domain={[
                      (dataMin: number) => Math.floor(Math.min(isNaN(dataMin) ? profile.temp_min : dataMin, profile.temp_min - 2)),
                      (dataMax: number) => Math.ceil(Math.max(isNaN(dataMax) ? profile.temp_max : dataMax, profile.temp_max + 2))
                    ]}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <ReferenceArea
                    y1={profile.temp_min}
                    y2={profile.temp_max}
                    fill="#10B981"
                    fillOpacity={0.12}
                    stroke="#10B981"
                    strokeOpacity={0.3}
                  />
                  <Line
                    type="monotone"
                    dataKey="temperature"
                    stroke="#06B6D4"
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4, stroke: '#06B6D4', strokeWidth: 2, fill: '#080E1A' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Chart 2: Relative Humidity (%) */}
          <div className="bg-dark-850 p-4 rounded-xl border border-dark-700/60 flex flex-col justify-between">
            <div className="flex items-center justify-between mb-3 text-xs font-mono">
              <span className="flex items-center gap-1.5 text-blue-400 font-bold">
                <Droplets className="w-4 h-4" /> RELATIVE HUMIDITY HISTORY (%)
              </span>
              <span className="text-[11px] text-slate-400">
                Safe Envelope: {profile.humidity_min}–{profile.humidity_max}%
              </span>
            </div>
            <div className="h-56 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={formattedData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                  <XAxis dataKey="displayTime" stroke="#64748B" fontSize={10} tickLine={false} />
                  <YAxis stroke="#64748B" fontSize={10} domain={[0, 100]} />
                  <Tooltip content={<CustomTooltip />} />
                  <ReferenceArea
                    y1={profile.humidity_min}
                    y2={profile.humidity_max}
                    fill="#3B82F6"
                    fillOpacity={0.12}
                    stroke="#3B82F6"
                    strokeOpacity={0.3}
                  />
                  <Line
                    type="monotone"
                    dataKey="humidity"
                    stroke="#3B82F6"
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4, stroke: '#3B82F6', strokeWidth: 2, fill: '#080E1A' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Chart 3: MQ-135 Gas Sensor Response */}
          <div className="bg-dark-850 p-4 rounded-xl border border-dark-700/60 flex flex-col justify-between">
            <div className="flex items-center justify-between mb-3 text-xs font-mono">
              <span className="flex items-center gap-1.5 text-purple-400 font-bold">
                <Wind className="w-4 h-4" /> MQ-135 GAS SENSOR (ADC COUNT)
              </span>
              <span className="text-[11px] text-slate-400">
                Threshold: {profile.gas_threshold} ADC
              </span>
            </div>
            <div className="h-56 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={formattedData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                  <XAxis dataKey="displayTime" stroke="#64748B" fontSize={10} tickLine={false} />
                  <YAxis
                    stroke="#64748B"
                    fontSize={10}
                    domain={[
                      0,
                      (dataMax: number) => Math.max(Math.ceil((profile.gas_threshold || 400) * 1.15), Math.ceil((isNaN(dataMax) ? 0 : dataMax) * 1.15))
                    ]}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <ReferenceLine
                    y={profile.gas_threshold}
                    stroke="#EF4444"
                    strokeDasharray="4 4"
                    label={{ value: 'Senescence Limit', fill: '#EF4444', fontSize: 10, position: 'top' }}
                  />
                  <ReferenceLine
                    y={profile.gas_baseline}
                    stroke="#10B981"
                    strokeDasharray="2 2"
                    label={{ value: 'Baseline', fill: '#10B981', fontSize: 10, position: 'bottom' }}
                  />
                  <Line
                    type="monotone"
                    dataKey="gas"
                    stroke="#A855F7"
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4, stroke: '#A855F7', strokeWidth: 2, fill: '#080E1A' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Chart 4: Composite Spoilage-Risk Trajectory */}
          <div className="bg-dark-850 p-4 rounded-xl border border-dark-700/60 flex flex-col justify-between">
            <div className="flex items-center justify-between mb-3 text-xs font-mono">
              <span className="flex items-center gap-1.5 text-amber-400 font-bold">
                <ShieldAlert className="w-4 h-4" /> COMPOSITE SPOILAGE RISK TRAJECTORY (%)
              </span>
              <span className="text-[11px] text-slate-400">
                Tiers: 30% Mod / 60% High / 80% Crit
              </span>
            </div>
            <div className="h-56 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={formattedData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                  <XAxis dataKey="displayTime" stroke="#64748B" fontSize={10} tickLine={false} />
                  <YAxis stroke="#64748B" fontSize={10} domain={[0, 100]} />
                  <Tooltip content={<CustomTooltip />} />
                  {/* Risk Tier Reference Lines */}
                  <ReferenceLine y={30} stroke="#F59E0B" strokeDasharray="3 3" label={{ value: '30% Mod', fill: '#F59E0B', fontSize: 9 }} />
                  <ReferenceLine y={60} stroke="#F97316" strokeDasharray="3 3" label={{ value: '60% High', fill: '#F97316', fontSize: 9 }} />
                  <ReferenceLine y={80} stroke="#EF4444" strokeDasharray="3 3" label={{ value: '80% Crit', fill: '#EF4444', fontSize: 9 }} />
                  <Line
                    type="monotone"
                    dataKey="composite_risk"
                    stroke="#F59E0B"
                    strokeWidth={2.5}
                    dot={false}
                    activeDot={{ r: 5, stroke: '#F59E0B', strokeWidth: 2, fill: '#080E1A' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
