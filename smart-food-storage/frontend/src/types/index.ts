export interface FoodProfile {
  id: string;
  name: string;
  scientific_name?: string;
  category?: string;
  temp_min: number;
  temp_max: number;
  temp_crit: number;
  temp_freeze: number;
  humidity_min: number;
  humidity_max: number;
  ideal_shelf_life_hours: number;
  gas_baseline: number;
  gas_threshold: number;
  weight_temp: number;
  weight_humidity: number;
  weight_gas: number;
  weight_duration: number;
  stress_multiplier_alpha: number;
  description?: string;
  icon?: string;
}

export interface StorageSession {
  id: number;
  session_name: string;
  food_profile_id: string;
  food_name?: string;
  start_time: string;
  end_time?: string | null;
  is_active: number;
  last_reading_time?: string | null;
  accumulated_effective_hours: number;
  total_readings_count: number;
}

export interface SensorReading {
  id?: number;
  temperature: number;
  humidity: number;
  gas: number;
  device_id: string;
  source: string;
  timestamp: string;
}

export interface RiskComponents {
  temp_score: number;
  humidity_score: number;
  gas_score: number;
  duration_score: number;
}

export interface RiskAssessment {
  composite_score: number;
  category: 'Low' | 'Moderate' | 'High' | 'Critical';
  color: 'green' | 'yellow' | 'orange' | 'red';
  components: RiskComponents;
  recommendation: string;
  effective_exposure_hours: number;
  ideal_shelf_life_hours: number;
}

export interface SimulatorState {
  is_running: boolean;
  current_mode: string;
  mode_label: string;
  available_modes?: Record<string, string>;
}

export interface HardwareStatus {
  status: 'online' | 'standby' | 'offline';
  is_connected: boolean;
  device_id: string | null;
  last_seen: string | null;
  seconds_ago: number | null;
  lan_ip: string;
  lan_endpoint: string;
}

export interface LatestDataResponse {
  has_data: boolean;
  reading: SensorReading | null;
  risk: RiskAssessment | null;
  active_session: StorageSession | null;
  active_profile: FoodProfile;
  simulator: SimulatorState;
  system_mode?: 'simulation' | 'hardware';
  hardware?: HardwareStatus;
}

export interface TelemetryPoint {
  id: number;
  timestamp: string;
  temperature: number;
  humidity: number;
  gas: number;
  source: string;
  composite_risk: number;
  temp_score: number;
  humidity_score: number;
  gas_score: number;
  duration_score: number;
  risk_category: string;
  food_name?: string;
}

export interface AlertItem {
  id: number;
  session_id: number | null;
  severity: 'Low' | 'Moderate' | 'High' | 'Critical';
  message: string;
  risk_score: number;
  previous_severity: string | null;
  timestamp: string;
  acknowledged: number;
}
