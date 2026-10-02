export type UserRole = 'ADMIN' | 'OPERATOR' | 'OBSERVER' | 'VIEWER';

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  avatar: string;
}

export interface RobotTelemetry {
  robot_id: string;
  position: [number, number];
  orientation: number;
  velocity: number;
  state: 'IDLE' | 'PLANNING' | 'MOVING' | 'WAITING' | 'PAUSED' | 'TASK_EXECUTION' | 'DEGRADED' | 'LOCAL_AUTONOMY' | 'RECOVERING' | 'CHARGING' | 'FAILED';
  battery: number;
  health: number;
  current_task: string | null;
  current_path: [number, number][];
  path_progress: number;
  network_status: 'CONNECTED' | 'DEGRADED' | 'PARTITIONED' | 'DISCONNECTED';
  last_heartbeat: number;
}

export interface TaskTelemetry {
  task_id: string;
  pickup: [number, number];
  delivery: [number, number];
  priority: number;
  deadline: number;
  status: 'CREATED' | 'AVAILABLE' | 'ASSIGNED' | 'IN_PROGRESS' | 'BLOCKED' | 'REASSIGNED' | 'COMPLETED' | 'FAILED' | 'CANCELLED';
  assigned_robot: string | null;
  creation_time: number;
  start_time: number | null;
  completion_time: number | null;
  phase: string;
}

export interface FaultTelemetry {
  fault_id: string;
  fault_type: string;
  target: string;
  start_time: number;
  duration: number;
  parameters: Record<string, any>;
  status: string;
}

export interface IncidentTelemetry {
  incident_id: string;
  timestamp: number;
  entity: string;
  fault: string | null;
  severity: 'INFO' | 'WARNING' | 'CRITICAL';
  state: string;
  message: string;
}

export interface SimulationWorld {
  width: number;
  height: number;
  shelves: [number, number][];
  pickup_stations: Record<string, [number, number]>;
  delivery_stations: Record<string, [number, number]>;
  charging_bays: Record<string, [number, number]>;
  blocked_aisles: [number, number][];
  dynamic_obstacles: [number, number][];
}

export interface SimulationMetrics {
  total_tasks: number;
  completed_tasks: number;
  task_completion_rate: number;
  makespan: number;
  average_waiting_time: number;
  average_route_length: number;
  conflict_count: number;
  collision_count: number;
  deadlock_count: number;
  deadlock_recovery_time: number;
  failure_detection_time: number;
  task_reassignment_time: number;
  messages_sent: number;
  messages_dropped: number;
  stale_messages: number;
  degraded_duration: number;
  local_autonomy_duration: number;
  resync_duration: number;
}

export interface TelemetryData {
  timestamp: number;
  clock: {
    current_time: number;
    tick_count: number;
    is_paused: boolean;
    time_step: number;
    time_scale: number;
  };
  world: SimulationWorld;
  robots: RobotTelemetry[];
  tasks: TaskTelemetry[];
  faults: FaultTelemetry[];
  incidents: IncidentTelemetry[];
  resilience: {
    current_state: string;
    state_durations: Record<string, number>;
    recent_transitions?: any[];
  };
  metrics: SimulationMetrics;
  network?: {
    latency_ms: number;
    packet_loss_rate: number;
    jitter_ms: number;
    messages_sent: number;
    messages_dropped: number;
    messages_delivered: number;
    messages_duplicated: number;
    messages_reordered: number;
    in_flight_count: number;
    is_partitioned: boolean;
    partition_groups: string[][];
  };
}
