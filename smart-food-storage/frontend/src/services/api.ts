import {
  LatestDataResponse,
  TelemetryPoint,
  AlertItem,
  FoodProfile,
  StorageSession
} from '../types';

const BASE_URL = '/api';

export async function fetchLatest(): Promise<LatestDataResponse> {
  const res = await fetch(`${BASE_URL}/latest`);
  if (!res.ok) throw new Error(`Failed to fetch latest data: ${res.statusText}`);
  return res.json();
}

export async function fetchHistory(range: '1h' | '24h' | '7d' = '24h'): Promise<{ range: string; count: number; data: TelemetryPoint[] }> {
  const res = await fetch(`${BASE_URL}/history?range=${range}&limit=250`);
  if (!res.ok) throw new Error(`Failed to fetch history: ${res.statusText}`);
  return res.json();
}

export async function fetchAlerts(): Promise<{ count: number; alerts: AlertItem[] }> {
  const res = await fetch(`${BASE_URL}/alerts?limit=50`);
  if (!res.ok) throw new Error(`Failed to fetch alerts: ${res.statusText}`);
  return res.json();
}

export async function acknowledgeAlert(alertId: number): Promise<{ success: boolean }> {
  const res = await fetch(`${BASE_URL}/alerts/acknowledge`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ alert_id: alertId })
  });
  if (!res.ok) throw new Error(`Failed to acknowledge alert: ${res.statusText}`);
  return res.json();
}

export async function fetchFoodProfiles(): Promise<{ count: number; profiles: FoodProfile[] }> {
  const res = await fetch(`${BASE_URL}/food-profiles`);
  if (!res.ok) throw new Error(`Failed to fetch food profiles: ${res.statusText}`);
  return res.json();
}

export async function fetchSessions(): Promise<{ active_session: StorageSession | null; sessions: StorageSession[] }> {
  const res = await fetch(`${BASE_URL}/sessions`);
  if (!res.ok) throw new Error(`Failed to fetch sessions: ${res.statusText}`);
  return res.json();
}

export async function startStorageSession(foodProfileId: string, sessionName?: string): Promise<{ status: string; session: StorageSession }> {
  const res = await fetch(`${BASE_URL}/sessions/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ food_profile_id: foodProfileId, session_name: sessionName })
  });
  if (!res.ok) throw new Error(`Failed to start session: ${res.statusText}`);
  return res.json();
}

export async function endStorageSession(): Promise<{ status: string; session: StorageSession }> {
  const res = await fetch(`${BASE_URL}/sessions/end`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  });
  if (!res.ok) throw new Error(`Failed to end session: ${res.statusText}`);
  return res.json();
}

export async function setSimulatorMode(mode: string): Promise<{ mode: string; label: string }> {
  const res = await fetch(`${BASE_URL}/simulator/mode`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mode })
  });
  if (!res.ok) throw new Error(`Failed to set mode: ${res.statusText}`);
  return res.json();
}

export async function startSimulator(intervalSeconds: number = 3.0): Promise<{ status: string; mode: string }> {
  const res = await fetch(`${BASE_URL}/simulator/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ interval_seconds: intervalSeconds })
  });
  if (!res.ok) throw new Error(`Failed to start simulator: ${res.statusText}`);
  return res.json();
}

export async function stopSimulator(): Promise<{ status: string }> {
  const res = await fetch(`${BASE_URL}/simulator/stop`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  });
  if (!res.ok) throw new Error(`Failed to stop simulator: ${res.statusText}`);
  return res.json();
}

export async function stepSimulator(): Promise<any> {
  const res = await fetch(`${BASE_URL}/simulator/step`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  });
  if (!res.ok) throw new Error(`Failed to step simulator: ${res.statusText}`);
  return res.json();
}

export async function postSensorData(payload: {
  temperature: number;
  humidity: number;
  gas: number;
  device_id: string;
  source?: string;
}): Promise<any> {
  const res = await fetch(`${BASE_URL}/sensor-data`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error(`Failed to post sensor data: ${res.statusText}`);
  return res.json();
}

export async function fetchSystemMode(): Promise<{
  status: string;
  system_mode: 'simulation' | 'hardware';
  hardware: any;
  simulator: any;
}> {
  const res = await fetch(`${BASE_URL}/system/mode`);
  if (!res.ok) throw new Error(`Failed to fetch system mode: ${res.statusText}`);
  return res.json();
}

export async function setSystemMode(mode: 'simulation' | 'hardware'): Promise<{
  status: string;
  system_mode: 'simulation' | 'hardware';
  hardware: any;
  simulator: any;
}> {
  const res = await fetch(`${BASE_URL}/system/mode`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mode })
  });
  if (!res.ok) throw new Error(`Failed to set system mode: ${res.statusText}`);
  return res.json();
}
