// Authentication types
export interface User {
  id: string;
  email: string;
  fullName: string;
  organizationId: string;
  organizationName: string;
  role: 'admin' | 'member' | 'viewer';
}

export interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
}
