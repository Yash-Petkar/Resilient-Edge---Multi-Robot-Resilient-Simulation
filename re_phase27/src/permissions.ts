import { UserRole } from './types';

export type Permission =
  | 'read'
  | 'simulation_control'
  | 'task_dispatch'
  | 'fault_injection'
  | 'recovery'
  | 'experiments'
  | 'settings'
  | 'database_admin'
  | 'user_admin'
  | 'destructive'
  | 'audit_read';

const ROLE_PERMISSIONS: Record<UserRole, ReadonlySet<Permission>> = {
  OBSERVER: new Set(['read', 'audit_read']),
  VIEWER: new Set(['read']),
  OPERATOR: new Set([
    'read',
    'simulation_control',
    'task_dispatch',
    'fault_injection',
    'recovery',
    'experiments',
  ]),
  ADMIN: new Set([
    'read',
    'simulation_control',
    'task_dispatch',
    'fault_injection',
    'recovery',
    'experiments',
    'settings',
    'database_admin',
    'user_admin',
    'destructive',
    'audit_read',
  ]),
};

export function roleAllows(role: UserRole, permission: Permission): boolean {
  return ROLE_PERMISSIONS[role].has(permission);
}

export function isUserRole(value: unknown): value is UserRole {
  return value === 'ADMIN' || value === 'OPERATOR' || value === 'OBSERVER' || value === 'VIEWER';
}
