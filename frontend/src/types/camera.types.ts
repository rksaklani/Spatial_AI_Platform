/**
 * Camera Configuration Types
 */

export interface CameraBoundary {
  min_x: number;
  min_y: number;
  min_z: number;
  max_x: number;
  max_y: number;
  max_z: number;
}

export interface CameraConfiguration {
  // Boundary limits
  boundary?: CameraBoundary;
  boundary_enabled: boolean;
  
  // Zoom limits
  min_zoom_distance: number;
  max_zoom_distance: number;
  
  // Axis locks
  lock_x_axis: boolean;
  lock_y_axis: boolean;
  lock_z_axis: boolean;
  
  // Default camera position
  default_position?: [number, number, number];
  default_target?: [number, number, number];
  
  // Rotation control
  rotation_enabled: boolean;
  
  // Boundary indicators
  show_boundary_indicators: boolean;
}
