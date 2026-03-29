/**
 * Device Capability Detection Service
 * Determines if client device can handle 3D rendering or needs server-side rendering
 */

interface DeviceCapability {
  webgl2: boolean;
  webgpu: boolean;
  maxTextureSize: number;
  gpuTier: 'high' | 'medium' | 'low' | 'none';
  recommendation: 'client-side' | 'server-side';
  reason: string;
}

interface PerformanceMetrics {
  fps: number;
  frameTime: number;
  memoryUsage?: number;
}

export class DeviceCapabilityService {
  private capability: DeviceCapability | null = null;
  private performanceHistory: PerformanceMetrics[] = [];

  /**
   * Detect device capabilities
   */
  async detectCapability(): Promise<DeviceCapability> {
    if (this.capability) {
      return this.capability;
    }

    const webgl2 = this.checkWebGL2Support();
    const webgpu = await this.checkWebGPUSupport();
    const maxTextureSize = this.getMaxTextureSize();
    const gpuTier = this.estimateGPUTier(webgl2, webgpu, maxTextureSize);
    
    const recommendation = this.getRecommendation(gpuTier, webgl2, webgpu);
    const reason = this.getRecommendationReason(gpuTier, webgl2, webgpu);

    this.capability = {
      webgl2,
      webgpu,
      maxTextureSize,
      gpuTier,
      recommendation,
      reason,
    };

    return this.capability;
  }

  /**
   * Check WebGL2 support
   */
  private checkWebGL2Support(): boolean {
    try {
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl2');
      return gl !== null;
    } catch {
      return false;
    }
  }

  /**
   * Check WebGPU support
   */
  private async checkWebGPUSupport(): Promise<boolean> {
    if (!navigator.gpu) {
      return false;
    }

    try {
      const adapter = await navigator.gpu.requestAdapter();
      return adapter !== null;
    } catch {
      return false;
    }
  }

  /**
   * Get maximum texture size
   */
  private getMaxTextureSize(): number {
    try {
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
      if (!gl) return 0;
      return gl.getParameter(gl.MAX_TEXTURE_SIZE);
    } catch {
      return 0;
    }
  }

  /**
   * Estimate GPU tier based on capabilities
   */
  private estimateGPUTier(
    webgl2: boolean,
    webgpu: boolean,
    maxTextureSize: number
  ): 'high' | 'medium' | 'low' | 'none' {
    if (!webgl2 && !webgpu) {
      return 'none';
    }

    if (webgpu && maxTextureSize >= 16384) {
      return 'high';
    }

    if (webgl2 && maxTextureSize >= 8192) {
      return 'medium';
    }

    return 'low';
  }

  /**
   * Get rendering recommendation
   */
  private getRecommendation(
    gpuTier: 'high' | 'medium' | 'low' | 'none',
    webgl2: boolean,
    webgpu: boolean
  ): 'client-side' | 'server-side' {
    if (gpuTier === 'none' || (!webgl2 && !webgpu)) {
      return 'server-side';
    }

    if (gpuTier === 'low') {
      return 'server-side';
    }

    return 'client-side';
  }

  /**
   * Get recommendation reason
   */
  private getRecommendationReason(
    gpuTier: 'high' | 'medium' | 'low' | 'none',
    webgl2: boolean,
    webgpu: boolean
  ): string {
    if (gpuTier === 'none') {
      return 'No GPU acceleration available';
    }

    if (!webgl2 && !webgpu) {
      return 'WebGL2 and WebGPU not supported';
    }

    if (gpuTier === 'low') {
      return 'Limited GPU capabilities detected';
    }

    if (gpuTier === 'medium') {
      return 'Moderate GPU capabilities - client-side rendering recommended';
    }

    return 'High-performance GPU detected - optimal for client-side rendering';
  }

  /**
   * Track performance metrics
   */
  trackPerformance(metrics: PerformanceMetrics): void {
    this.performanceHistory.push(metrics);

    // Keep only last 100 samples
    if (this.performanceHistory.length > 100) {
      this.performanceHistory.shift();
    }
  }

  /**
   * Get average FPS from recent performance
   */
  getAverageFPS(): number {
    if (this.performanceHistory.length === 0) return 0;

    const sum = this.performanceHistory.reduce((acc, m) => acc + m.fps, 0);
    return sum / this.performanceHistory.length;
  }

  /**
   * Check if performance is degrading
   */
  isPerformanceDegrading(): boolean {
    if (this.performanceHistory.length < 10) return false;

    const recentFPS = this.performanceHistory.slice(-10);
    const avgFPS = recentFPS.reduce((acc, m) => acc + m.fps, 0) / recentFPS.length;

    // If FPS drops below 20, performance is degrading
    return avgFPS < 20;
  }

  /**
   * Should switch to server-side rendering based on performance
   */
  shouldSwitchToServerRendering(): boolean {
    if (!this.capability) return false;

    // If already recommended server-side, no need to switch
    if (this.capability.recommendation === 'server-side') {
      return false;
    }

    // If performance is degrading, recommend switch
    return this.isPerformanceDegrading();
  }

  /**
   * Get current capability
   */
  getCapability(): DeviceCapability | null {
    return this.capability;
  }

  /**
   * Reset capability detection (for testing)
   */
  reset(): void {
    this.capability = null;
    this.performanceHistory = [];
  }
}

// Singleton instance
let deviceCapabilityInstance: DeviceCapabilityService | null = null;

export function getDeviceCapabilityService(): DeviceCapabilityService {
  if (!deviceCapabilityInstance) {
    deviceCapabilityInstance = new DeviceCapabilityService();
  }
  return deviceCapabilityInstance;
}
