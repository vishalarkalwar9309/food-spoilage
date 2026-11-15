import React, { useState } from 'react';
import { Activity, Cpu, Radio, RefreshCw, Wifi, WifiOff, Globe, Check, Copy } from 'lucide-react';
import { LatestDataResponse } from '../types';

interface NavbarProps {
  latestData: LatestDataResponse | null;
  isLoading: boolean;
  onRefresh: () => void;
  systemMode?: 'simulation' | 'hardware';
  onToggleMode?: (mode: 'simulation' | 'hardware') => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  latestData,
  isLoading,
  onRefresh,
  systemMode = 'simulation',
  onToggleMode
}) => {
  const [copied, setCopied] = useState<boolean>(false);
  const isSimulating = latestData?.simulator?.is_running;
  const source = latestData?.reading?.source || 'none';
  const hardware = latestData?.hardware;
  const isHwOnline = hardware?.is_connected ?? false;
  const hwStatus = hardware?.status ?? 'offline';
  const deviceId = latestData?.reading?.device_id || hardware?.device_id || 'ESP32-FOOD-001';
  const lanIp = hardware?.lan_ip || '192.168.0.101';
  const lanEndpoint = hardware?.lan_endpoint || `http://${lanIp}:5000/api/sensor-data`;

  const lastUpdated = latestData?.reading?.timestamp
    ? new Date(latestData.reading.timestamp).toLocaleTimeString()
    : 'No data yet';

  const handleCopyEndpoint = () => {
    navigator.clipboard.writeText(lanEndpoint);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <header className="border-b border-dark-700 bg-dark-900/90 backdrop-blur sticky top-0 z-50 px-4 lg:px-8 py-3">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        {/* Brand & Subtitle */}
        <div className="flex items-center space-x-3.5">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-cyan-500/20 to-emerald-500/20 border border-cyan-500/40 flex items-center justify-center text-cyan-400 shadow-inner">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-base lg:text-lg font-bold tracking-tight text-white uppercase font-mono">
                Smart Food Storage
              </h1>
              <span className="text-[10px] px-2 py-0.5 rounded-full font-mono bg-cyan-950 text-cyan-400 border border-cyan-800 font-semibold">
                IoT Spoilage Predictor
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Edge Headspace Telemetry &amp; Cumulative Spoilage Risk Engine
            </p>
          </div>
        </div>

        {/* Operating Mode Selector & Hardware Status */}
        <div className="flex items-center flex-wrap gap-2 text-xs">
          {/* Mode Switcher Toggle */}
          <div className="flex items-center p-0.5 rounded-lg bg-dark-800 border border-dark-700 font-mono text-[11px]">
            <button
              onClick={() => onToggleMode && onToggleMode('simulation')}
              className={`px-2.5 py-1 rounded-md font-semibold transition ${
                systemMode === 'simulation'
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                  : 'text-slate-400 hover:text-white'
              }`}
              title="Activate synthetic simulation controls"
            >
              Simulation Mode
            </button>
            <button
              onClick={() => onToggleMode && onToggleMode('hardware')}
              className={`px-2.5 py-1 rounded-md font-semibold transition ${
                systemMode === 'hardware'
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                  : 'text-slate-400 hover:text-white'
              }`}
              title="Activate physical ESP32 streaming mode"
            >
              Physical ESP32
            </button>
          </div>

          {/* Hardware Connection Status */}
          <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-md bg-dark-800 border border-dark-700 font-mono">
            {isHwOnline ? (
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
            ) : hwStatus === 'standby' ? (
              <span className="h-2 w-2 rounded-full bg-amber-500"></span>
            ) : (
              <span className="h-2 w-2 rounded-full bg-slate-500"></span>
            )}
            <Cpu className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-slate-400">Node:</span>
            <span className={`font-semibold ${isHwOnline ? 'text-emerald-400' : hwStatus === 'standby' ? 'text-amber-400' : 'text-slate-400'}`}>
              {isHwOnline ? 'ESP32 Online' : hwStatus === 'standby' ? 'ESP32 Standby' : 'ESP32 Offline'}
            </span>
            <span className="text-slate-500 font-mono text-[10px]">({deviceId})</span>
          </div>

          {/* Telemetry Source Badge */}
          <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-md bg-dark-800 border border-dark-700 font-mono">
            <Radio className={`w-3.5 h-3.5 ${source === 'esp32' ? 'text-emerald-400' : 'text-cyan-400 animate-pulse'}`} />
            <span className="text-slate-400">Stream:</span>
            <span className={`font-semibold uppercase ${source === 'esp32' ? 'text-emerald-400' : 'text-amber-400'}`}>
              {source === 'esp32' ? 'ESP32 Live' : source === 'simulator' ? 'Simulator' : 'Standby'}
            </span>
            {isSimulating && (
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping ml-1" />
            )}
          </div>

          {/* LAN Ingestion Endpoint Helper */}
          <button
            onClick={handleCopyEndpoint}
            className="flex items-center space-x-1 px-2.5 py-1.5 rounded-md bg-dark-800 hover:bg-dark-700 border border-dark-700 text-slate-300 font-mono text-[11px] transition"
            title="Click to copy ESP32 ingestion LAN URL"
          >
            <Globe className="w-3 h-3 text-cyan-400" />
            <span className="text-slate-400">LAN:</span>
            <span className="text-cyan-300">{lanIp}:5000</span>
            {copied ? <Check className="w-3 h-3 text-emerald-400 ml-1" /> : <Copy className="w-3 h-3 text-slate-500 ml-1" />}
          </button>

          {/* Last Update */}
          <div className="flex items-center space-x-1.5 px-2.5 py-1.5 rounded-md bg-dark-800 border border-dark-700 font-mono text-slate-400">
            <span>Sync:</span>
            <span className="text-slate-200">{lastUpdated}</span>
          </div>

          {/* Manual Refresh */}
          <button
            onClick={onRefresh}
            disabled={isLoading}
            className="p-1.5 rounded-md bg-dark-800 hover:bg-dark-700 border border-dark-700 text-slate-300 hover:text-white transition disabled:opacity-50"
            title="Refresh latest state"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>
    </header>
  );
};
