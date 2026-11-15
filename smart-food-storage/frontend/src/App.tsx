import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  fetchLatest,
  fetchHistory,
  fetchAlerts,
  fetchFoodProfiles,
  fetchSessions,
  startStorageSession,
  endStorageSession,
  setSimulatorMode,
  startSimulator,
  stopSimulator,
  stepSimulator,
  acknowledgeAlert,
  setSystemMode
} from './services/api';
import {
  LatestDataResponse,
  TelemetryPoint,
  AlertItem,
  FoodProfile,
  StorageSession
} from './types';

import { Navbar } from './components/Navbar';
import { SimulatorDock } from './components/SimulatorDock';
import { RiskGaugeCard } from './components/RiskGaugeCard';
import { MetricCardCluster } from './components/MetricCardCluster';
import { HistoricalAnalytics } from './components/HistoricalAnalytics';
import { FoodProfileManager } from './components/FoodProfileManager';
import { StorageSessionManager } from './components/StorageSessionManager';
import { AlertsPanel } from './components/AlertsPanel';
import { EngineeringDisclaimer } from './components/EngineeringDisclaimer';
import { AlertCircle, RefreshCw, ServerCrash } from 'lucide-react';

export const App: React.FC = () => {
  // State
  const [latestData, setLatestData] = useState<LatestDataResponse | null>(null);
  const [historyData, setHistoryData] = useState<TelemetryPoint[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [profiles, setProfiles] = useState<FoodProfile[]>([]);
  const [sessions, setSessions] = useState<StorageSession[]>([]);
  const [timeRange, setTimeRange] = useState<'1h' | '24h' | '7d'>('24h');

  // Loading & Error States
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [isStartingSession, setIsStartingSession] = useState<boolean>(false);

  // Default fallback profile while loading
  const fallbackProfile: FoodProfile = {
    id: 'tomatoes',
    name: 'Tomatoes',
    scientific_name: 'Solanum lycopersicum',
    temp_min: 12.0,
    temp_max: 15.0,
    temp_crit: 30.0,
    temp_freeze: 0.0,
    humidity_min: 85.0,
    humidity_max: 90.0,
    ideal_shelf_life_hours: 168.0,
    gas_baseline: 180.0,
    gas_threshold: 400.0,
    weight_temp: 0.30,
    weight_humidity: 0.25,
    weight_gas: 0.25,
    weight_duration: 0.20,
    stress_multiplier_alpha: 1.5
  };

  const activeProfile: FoodProfile = latestData?.active_profile || fallbackProfile;

  // Initial load
  const loadAllData = useCallback(async () => {
    try {
      setApiError(null);
      const [latestRes, historyRes, alertsRes, profilesRes, sessionsRes] = await Promise.all([
        fetchLatest(),
        fetchHistory(timeRange),
        fetchAlerts(),
        fetchFoodProfiles(),
        fetchSessions()
      ]);

      setLatestData(latestRes);
      setHistoryData(historyRes.data);
      setAlerts(alertsRes.alerts);
      setProfiles(profilesRes.profiles);
      setSessions(sessionsRes.sessions);
    } catch (err: any) {
      console.error('Failed to load application data:', err);
      setApiError(err.message || 'Cannot reach local backend API (http://127.0.0.1:5000)');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [timeRange]);

  const pollErrorCountRef = useRef<number>(0);

  // Periodic poll for real-time telemetry updates (every 3.5 seconds)
  useEffect(() => {
    loadAllData();
    const interval = setInterval(async () => {
      try {
        const [latestRes, historyRes, alertsRes] = await Promise.all([
          fetchLatest(),
          fetchHistory(timeRange),
          fetchAlerts()
        ]);
        setLatestData(latestRes);
        setHistoryData(historyRes.data);
        setAlerts(alertsRes.alerts);
        pollErrorCountRef.current = 0;
        setApiError(null);
      } catch (err: any) {
        pollErrorCountRef.current += 1;
        // If 2 consecutive polls fail, display offline notice
        if (pollErrorCountRef.current >= 2) {
          setApiError('Backend connection offline (http://127.0.0.1:5000). Retrying...');
        }
      }
    }, 3500);

    return () => clearInterval(interval);
  }, [loadAllData, timeRange]);

  // Handlers
  const handleRangeChange = async (range: '1h' | '24h' | '7d') => {
    setTimeRange(range);
    try {
      const res = await fetchHistory(range);
      setHistoryData(res.data);
    } catch (err) {
      console.error('Failed to update range:', err);
    }
  };

  const handleSelectProfile = async (profileId: string) => {
    const prof = profiles.find((p) => p.id === profileId);
    if (latestData?.active_session && latestData.active_session.is_active) {
      const activeName = latestData.active_session.food_name || latestData.active_session.food_profile_id;
      const confirmSwitch = window.confirm(
        `A storage session for "${activeName}" is currently active. End it and start a new session for "${prof?.name || profileId}"?`
      );
      if (!confirmSwitch) return;
    }

    setIsStartingSession(true);
    try {
      const name = `${prof?.name || 'Produce'} Storage Session`;
      await startStorageSession(profileId, name);
      await loadAllData();
    } catch (err: any) {
      alert(`Failed to set profile: ${err.message}`);
    } finally {
      setIsStartingSession(false);
    }
  };

  const handleStartSession = async (profileId: string, sessionName?: string) => {
    if (latestData?.active_session && latestData.active_session.is_active) {
      const activeName = latestData.active_session.food_name || latestData.active_session.food_profile_id;
      const confirmSwitch = window.confirm(
        `A storage session for "${activeName}" is currently active. End it and start a new batch?`
      );
      if (!confirmSwitch) return;
    }

    setIsStartingSession(true);
    try {
      await startStorageSession(profileId, sessionName);
      await loadAllData();
    } catch (err: any) {
      alert(`Failed to start session: ${err.message}`);
    } finally {
      setIsStartingSession(false);
    }
  };

  const handleEndSession = async () => {
    if (!window.confirm('Are you sure you want to end the active storage session?')) return;
    try {
      await endStorageSession();
      await loadAllData();
    } catch (err: any) {
      alert(`Failed to end session: ${err.message}`);
    }
  };

  const handleAcknowledgeAlert = async (alertId: number) => {
    try {
      await acknowledgeAlert(alertId);
      setAlerts((prev) =>
        prev.map((a) => (a.id === alertId ? { ...a, acknowledged: 1 } : a))
      );
    } catch (err: any) {
      alert(`Failed to acknowledge alert: ${err.message}`);
    }
  };

  const handleSetSimulatorMode = async (mode: string) => {
    try {
      await setSimulatorMode(mode);
      const updated = await fetchLatest();
      setLatestData(updated);
    } catch (err: any) {
      alert(`Failed to update mode: ${err.message}`);
    }
  };

  const handleStartSimulator = async (intervalSeconds: number = 3.5) => {
    try {
      await startSimulator(intervalSeconds);
      const updated = await fetchLatest();
      setLatestData(updated);
    } catch (err: any) {
      alert(`Failed to start simulator: ${err.message}`);
    }
  };

  const handleStopSimulator = async () => {
    try {
      await stopSimulator();
      const updated = await fetchLatest();
      setLatestData(updated);
    } catch (err: any) {
      alert(`Failed to stop simulator: ${err.message}`);
    }
  };

  const handleStepSimulator = async () => {
    try {
      await stepSimulator();
      const [updated, hist, alr] = await Promise.all([
        fetchLatest(),
        fetchHistory(timeRange),
        fetchAlerts()
      ]);
      setLatestData(updated);
      setHistoryData(hist.data);
      setAlerts(alr.alerts);
    } catch (err: any) {
      alert(`Failed to step simulator: ${err.message}`);
    }
  };

  const handleToggleSystemMode = async (mode: 'simulation' | 'hardware') => {
    try {
      await setSystemMode(mode);
      const updated = await fetchLatest();
      setLatestData(updated);
    } catch (err: any) {
      alert(`Failed to switch mode: ${err.message}`);
    }
  };

  return (
    <div className="min-h-screen bg-dark-950 text-slate-100 flex flex-col justify-between selection:bg-cyan-500/20 selection:text-cyan-300">
      {/* Top Navbar */}
      <Navbar
        latestData={latestData}
        systemMode={latestData?.system_mode || 'simulation'}
        onToggleMode={handleToggleSystemMode}
        isLoading={isRefreshing}
        onRefresh={() => {
          setIsRefreshing(true);
          loadAllData();
        }}
      />

      {/* Main Body */}
      <main className="max-w-7xl mx-auto px-4 lg:px-8 py-6 space-y-6 flex-grow w-full">
        {/* API Error Notification if Backend Offline */}
        {apiError && (
          <div className="p-4 rounded-xl bg-red-950/40 border border-red-800 text-red-300 font-mono text-xs flex items-center justify-between gap-3 shadow-lg">
            <div className="flex items-center gap-2">
              <ServerCrash className="w-5 h-5 text-red-400 flex-shrink-0" />
              <div>
                <strong>Backend Communication Offline: </strong>
                <span>Ensure Flask API is running on http://127.0.0.1:5000 (`python app.py`).</span>
              </div>
            </div>
            <button
              onClick={() => {
                setIsRefreshing(true);
                loadAllData();
              }}
              className="px-3 py-1 rounded bg-red-900/60 hover:bg-red-800 border border-red-700 text-white font-bold transition flex items-center gap-1"
            >
              <RefreshCw className="w-3.5 h-3.5" /> Retry
            </button>
          </div>
        )}

        {/* 1. Hardware Simulator Control Console */}
        <SimulatorDock
          simulator={latestData?.simulator}
          systemMode={latestData?.system_mode || 'simulation'}
          onSetMode={handleSetSimulatorMode}
          onStart={handleStartSimulator}
          onStop={handleStopSimulator}
          onStep={handleStepSimulator}
          onSwitchToSimulation={() => handleToggleSystemMode('simulation')}
        />

        {/* 2. Spoilage-Risk Mathematical Engine Hero Card */}
        <RiskGaugeCard
          risk={latestData?.risk || null}
          profile={activeProfile}
        />

        {/* 3. Real-Time Telemetry Cluster Cards */}
        <MetricCardCluster
          reading={latestData?.reading || null}
          profile={activeProfile}
          session={latestData?.active_session || null}
          risk={latestData?.risk || null}
        />

        {/* 4. Interactive Historical Analytics Charts */}
        <HistoricalAnalytics
          data={historyData}
          profile={activeProfile}
          selectedRange={timeRange}
          onRangeChange={handleRangeChange}
          isLoading={isLoading}
        />

        {/* 5. Food Storage Profiles Management */}
        <FoodProfileManager
          profiles={profiles.length > 0 ? profiles : [fallbackProfile]}
          activeProfile={activeProfile}
          activeSession={latestData?.active_session || null}
          onSelectProfile={handleSelectProfile}
          isStartingSession={isStartingSession}
        />

        {/* 6. Storage Session Lifecycle Management */}
        <StorageSessionManager
          activeSession={latestData?.active_session || null}
          sessions={sessions}
          profiles={profiles.length > 0 ? profiles : [fallbackProfile]}
          onStartSession={handleStartSession}
          onEndSession={handleEndSession}
        />

        {/* 7. Incident Alerts Panel */}
        <AlertsPanel
          alerts={alerts}
          onAcknowledge={handleAcknowledgeAlert}
          isLoading={isLoading}
        />
      </main>

      {/* Engineering & Legal Disclaimer */}
      <EngineeringDisclaimer />
    </div>
  );
};

export default App;
