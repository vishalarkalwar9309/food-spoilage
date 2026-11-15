import React, { useState } from 'react';
import { Play, Square, FastForward, Sliders, Cpu, Activity, Sparkles, ShieldAlert, ToggleLeft } from 'lucide-react';
import { SimulatorState } from '../types';

interface SimulatorDockProps {
  simulator: SimulatorState | undefined;
  systemMode?: 'simulation' | 'hardware';
  onSetMode: (mode: string) => Promise<void>;
  onStart: (intervalSeconds?: number) => Promise<void>;
  onStop: () => Promise<void>;
  onStep: () => Promise<void>;
  onSwitchToSimulation?: () => void;
}

export const SimulatorDock: React.FC<SimulatorDockProps> = ({
  simulator,
  systemMode = 'simulation',
  onSetMode,
  onStart,
  onStop,
  onStep,
  onSwitchToSimulation
}) => {
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const isRunning = simulator?.is_running ?? false;
  const currentMode = simulator?.current_mode ?? 'normal';
  const isHardwareMode = systemMode === 'hardware';

  const modes = [
    { id: 'normal', label: '1. Normal Conditions', desc: 'Optimal Temp, Optimal RH, Low Clean Headspace Gas' },
    { id: 'high_temp', label: '2. High Temperature', desc: 'Elevated Temp (26–30°C), Nominal RH & Gas' },
    { id: 'high_humidity', label: '3. High Humidity', desc: 'Excess Humidity (>95% RH), Condensation Risk' },
    { id: 'elevated_gas', label: '4. Elevated Gas', desc: 'High VOC / Metabolic Gas (350–550 ADC)' },
    { id: 'combined_stress', label: '5. Combined Stress', desc: 'Severe Thermal + Desiccation + Gas Release' },
  ];

  const handleModeChange = async (modeId: string) => {
    setIsProcessing(true);
    try {
      await onSetMode(modeId);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleToggleRunning = async () => {
    setIsProcessing(true);
    try {
      if (isRunning) {
        await onStop();
      } else {
        await onStart(3.5);
      }
    } finally {
      setIsProcessing(false);
    }
  };

  const handleStepOnce = async () => {
    setIsProcessing(true);
    try {
      await onStep();
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className={`border rounded-xl p-5 lg:p-6 space-y-4 shadow-lg transition-all duration-300 ${
      isHardwareMode
        ? 'bg-dark-900/60 border-emerald-500/30 shadow-emerald-950/10'
        : 'bg-dark-900 border-amber-500/30 shadow-amber-950/10'
    }`}>
      {/* Hardware Mode Banner Notice */}
      {isHardwareMode && (
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 rounded-lg bg-emerald-950/40 border border-emerald-800/60 text-emerald-300 text-xs font-mono">
          <div className="flex items-center gap-2.5">
            <Cpu className="w-4 h-4 text-emerald-400 flex-shrink-0" />
            <div>
              <strong>PHYSICAL HARDWARE MODE ACTIVE: </strong>
              <span>Streaming telemetry from physical ESP32. Simulator paused to prevent synthetic data contamination.</span>
            </div>
          </div>
          <button
            onClick={onSwitchToSimulation}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-emerald-900/60 hover:bg-emerald-800 border border-emerald-700 text-white font-bold transition flex-shrink-0"
          >
            <ToggleLeft className="w-3.5 h-3.5" /> Switch to Simulation
          </button>
        </div>
      )}

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-dark-800 pb-3">
        <div>
          <div className="flex items-center gap-2">
            <Sliders className="w-5 h-5 text-amber-400" />
            <h3 className="text-base font-bold text-white font-mono uppercase">
              HARDWARE EMULATION &amp; SENSOR SIMULATOR
            </h3>
            <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-semibold ${
              isHardwareMode
                ? 'bg-dark-800 text-slate-400 border border-dark-700'
                : 'bg-amber-950 text-amber-300 border border-amber-800'
            }`}>
              {isHardwareMode ? 'STANDBY (HW PRIORITY)' : 'SIMULATED TELEMETRY'}
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Generates synthetic microclimate telemetry to test the spoilage risk engine ahead of ESP32 deployment
          </p>
        </div>

        {/* Global Auto-Stream & Step Controls */}
        <div className="flex items-center space-x-2">
          <button
            onClick={handleStepOnce}
            disabled={isProcessing}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-dark-800 hover:bg-dark-700 border border-dark-700 text-slate-200 font-mono text-xs font-semibold transition disabled:opacity-50"
            title="Inject a single simulated reading"
          >
            <FastForward className="w-3.5 h-3.5 text-cyan-400" /> Step Once
          </button>

          <button
            onClick={handleToggleRunning}
            disabled={isProcessing}
            className={`flex items-center gap-1.5 px-4 py-1.5 rounded-lg font-mono text-xs font-bold transition shadow-sm disabled:opacity-50 ${
              isRunning
                ? 'bg-red-600 hover:bg-red-500 text-white'
                : 'bg-emerald-600 hover:bg-emerald-500 text-white'
            }`}
          >
            {isRunning ? (
              <>
                <Square className="w-3.5 h-3.5 fill-current" /> Stop Auto-Stream
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" /> Start Auto-Stream (3.5s)
              </>
            )}
          </button>
        </div>
      </div>

      {/* 5 Simulation Modes */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2.5">
        {modes.map((m) => {
          const isSelected = currentMode === m.id;
          return (
            <button
              key={m.id}
              onClick={() => handleModeChange(m.id)}
              disabled={isProcessing}
              className={`p-3 rounded-lg text-left transition-all duration-150 border flex flex-col justify-between ${
                isSelected
                  ? 'bg-amber-950/40 border-amber-500/70 text-amber-200 shadow-sm'
                  : 'bg-dark-800/80 hover:bg-dark-800 border-dark-700 text-slate-300'
              }`}
            >
              <div>
                <div className="flex items-center justify-between text-xs font-bold font-mono">
                  <span>{m.label}</span>
                  {isSelected && <Sparkles className="w-3 h-3 text-amber-400" />}
                </div>
                <p className="text-[11px] text-slate-400 mt-1 leading-tight">
                  {m.desc}
                </p>
              </div>

              {isSelected && (
                <div className="mt-2 text-[10px] font-mono text-amber-400 font-semibold flex items-center gap-1">
                  <Activity className="w-2.5 h-2.5 animate-pulse" /> Active Profile Stress
                </div>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
};
