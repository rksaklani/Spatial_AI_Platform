/**
 * Camera Limits Component
 * 
 * Implements camera movement restrictions:
 * - Boundary enforcement (3D bounding box)
 * - Zoom limits (min/max distance)
 * - Axis locks (X, Y, Z)
 * - Default camera position
 * - Rotation control
 * - Boundary indicators
 * 
 * Requirements: 30.1, 30.2, 30.3, 30.4, 30.5, 30.6, 30.7, 30.8, 30.9, 30.10
 */

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import type { CameraBoundary, CameraConfiguration } from '../types/camera.types';

export type { CameraBoundary, CameraConfiguration };

export class CameraLimitsController {
  private camera: THREE.PerspectiveCamera;
  private controls: OrbitControls;
  private config: CameraConfiguration;
  private scene: THREE.Scene;
  private boundaryHelper?: THREE.Box3Helper;
  private previousPosition: THREE.Vector3;
  private previousTarget: THREE.Vector3;

  constructor(
    camera: THREE.PerspectiveCamera,
    controls: OrbitControls,
    config: CameraConfiguration,
    scene: THREE.Scene
  ) {
    this.camera = camera;
    this.controls = controls;
    this.config = config;
    this.scene = scene;
    this.previousPosition = camera.position.clone();
    this.previousTarget = controls.target.clone();

    this.applyConfiguration();
  }

  /**
   * Apply camera configuration
   * Requirements: 30.1-30.10
   */
  private applyConfiguration(): void {
    // Apply zoom limits (Requirements 30.3, 30.4)
    this.controls.minDistance = this.config.min_zoom_distance;
    this.controls.maxDistance = this.config.max_zoom_distance;

    // Apply rotation control (Requirement 30.8)
    this.controls.enableRotate = this.config.rotation_enabled;

    // Apply default camera position (Requirement 30.7)
    if (this.config.default_position) {
      this.camera.position.set(
        this.config.default_position[0],
        this.config.default_position[1],
        this.config.default_position[2]
      );
    }

    if (this.config.default_target) {
      this.controls.target.set(
        this.config.default_target[0],
        this.config.default_target[1],
        this.config.default_target[2]
      );
    }

    // Create boundary indicators (Requirement 30.10)
    if (this.config.boundary_enabled && this.config.boundary && this.config.show_boundary_indicators) {
      this.createBoundaryIndicators();
    }

    // Set up change listener for enforcement
    this.controls.addEventListener('change', () => this.enforceLimits());
  }

  /**
   * Create visual boundary indicators
   * Requirement: 30.10
   */
  private createBoundaryIndicators(): void {
    if (!this.config.boundary) return;

    const b = this.config.boundary;
    const box = new THREE.Box3(
      new THREE.Vector3(b.min_x, b.min_y, b.min_z),
      new THREE.Vector3(b.max_x, b.max_y, b.max_z)
    );

    // Remove existing helper if any
    if (this.boundaryHelper) {
      this.scene.remove(this.boundaryHelper);
    }

    // Create box helper with yellow color
    this.boundaryHelper = new THREE.Box3Helper(box, new THREE.Color(0xffff00));
    this.boundaryHelper.material.opacity = 0.3;
    this.boundaryHelper.material.transparent = true;
    this.scene.add(this.boundaryHelper);
  }

  /**
   * Enforce camera limits on every frame
   * Requirements: 30.1, 30.2, 30.3, 30.4, 30.5, 30.6
   */
  private enforceLimits(): void {
    let positionChanged = false;
    let targetChanged = false;

    // Enforce boundary limits (Requirements 30.1, 30.2)
    if (this.config.boundary_enabled && this.config.boundary) {
      const b = this.config.boundary;
      const pos = this.camera.position;

      // Clamp camera position to boundary
      if (pos.x < b.min_x || pos.x > b.max_x ||
          pos.y < b.min_y || pos.y > b.max_y ||
          pos.z < b.min_z || pos.z > b.max_z) {
        
        pos.x = Math.max(b.min_x, Math.min(b.max_x, pos.x));
        pos.y = Math.max(b.min_y, Math.min(b.max_y, pos.y));
        pos.z = Math.max(b.min_z, Math.min(b.max_z, pos.z));
        positionChanged = true;
      }

      // Also clamp target to boundary
      const target = this.controls.target;
      if (target.x < b.min_x || target.x > b.max_x ||
          target.y < b.min_y || target.y > b.max_y ||
          target.z < b.min_z || target.z > b.max_z) {
        
        target.x = Math.max(b.min_x, Math.min(b.max_x, target.x));
        target.y = Math.max(b.min_y, Math.min(b.max_y, target.y));
        target.z = Math.max(b.min_z, Math.min(b.max_z, target.z));
        targetChanged = true;
      }
    }

    // Enforce axis locks (Requirements 30.5, 30.6)
    if (this.config.lock_x_axis || this.config.lock_y_axis || this.config.lock_z_axis) {
      const pos = this.camera.position;
      const prevPos = this.previousPosition;

      if (this.config.lock_x_axis && pos.x !== prevPos.x) {
        pos.x = prevPos.x;
        positionChanged = true;
      }

      if (this.config.lock_y_axis && pos.y !== prevPos.y) {
        pos.y = prevPos.y;
        positionChanged = true;
      }

      if (this.config.lock_z_axis && pos.z !== prevPos.z) {
        pos.z = prevPos.z;
        positionChanged = true;
      }

      // Also lock target movement on locked axes
      const target = this.controls.target;
      const prevTarget = this.previousTarget;

      if (this.config.lock_x_axis && target.x !== prevTarget.x) {
        target.x = prevTarget.x;
        targetChanged = true;
      }

      if (this.config.lock_y_axis && target.y !== prevTarget.y) {
        target.y = prevTarget.y;
        targetChanged = true;
      }

      if (this.config.lock_z_axis && target.z !== prevTarget.z) {
        target.z = prevTarget.z;
        targetChanged = true;
      }
    }

    // Update controls if position or target changed
    if (positionChanged || targetChanged) {
      this.controls.update();
    }

    // Store current position and target for next frame
    this.previousPosition.copy(this.camera.position);
    this.previousTarget.copy(this.controls.target);
  }

  /**
   * Update camera configuration
   * Requirement: 30.9
   */
  updateConfiguration(config: CameraConfiguration): void {
    this.config = config;
    
    // Remove old boundary helper
    if (this.boundaryHelper) {
      this.scene.remove(this.boundaryHelper);
      this.boundaryHelper = undefined;
    }

    // Reapply configuration
    this.applyConfiguration();
  }

  /**
   * Get current configuration
   */
  getConfiguration(): CameraConfiguration {
    return this.config;
  }

  /**
   * Reset camera to default position
   * Requirement: 30.7
   */
  resetToDefault(): void {
    if (this.config.default_position) {
      this.camera.position.set(
        this.config.default_position[0],
        this.config.default_position[1],
        this.config.default_position[2]
      );
    }

    if (this.config.default_target) {
      this.controls.target.set(
        this.config.default_target[0],
        this.config.default_target[1],
        this.config.default_target[2]
      );
    }

    this.controls.update();
  }

  /**
   * Check if camera is approaching boundary
   * Requirement: 30.10
   */
  isApproachingBoundary(threshold: number = 1.0): boolean {
    if (!this.config.boundary_enabled || !this.config.boundary) {
      return false;
    }

    const b = this.config.boundary;
    const pos = this.camera.position;

    // Check distance to each boundary face
    const distToMinX = Math.abs(pos.x - b.min_x);
    const distToMaxX = Math.abs(pos.x - b.max_x);
    const distToMinY = Math.abs(pos.y - b.min_y);
    const distToMaxY = Math.abs(pos.y - b.max_y);
    const distToMinZ = Math.abs(pos.z - b.min_z);
    const distToMaxZ = Math.abs(pos.z - b.max_z);

    const minDist = Math.min(
      distToMinX, distToMaxX,
      distToMinY, distToMaxY,
      distToMinZ, distToMaxZ
    );

    return minDist < threshold;
  }

  /**
   * Cleanup
   */
  dispose(): void {
    if (this.boundaryHelper) {
      this.scene.remove(this.boundaryHelper);
    }
  }
}
