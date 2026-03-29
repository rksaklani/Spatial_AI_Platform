import * as THREE from 'three';
import type { SceneTile } from '../types/scene.types';

interface TileRequest {
  sceneId: string;
  camera: {
    position: [number, number, number];
    direction: [number, number, number];
    fov: number;
    near: number;
    far: number;
  };
  bandwidth_mbps?: number;
  max_tiles?: number;
}

interface TileManagerConfig {
  maxCachedTiles?: number;
  bandwidthMbps?: number;
  maxTilesPerFrame?: number;
  frustumCullingEnabled?: boolean;
}

export class TileManager {
  private cache: Map<string, SceneTile> = new Map();
  private loadingTiles: Set<string> = new Set();
  private config: Required<TileManagerConfig>;
  private bandwidthEstimate: number;

  constructor(config: TileManagerConfig = {}) {
    this.config = {
      maxCachedTiles: config.maxCachedTiles || 100,
      bandwidthMbps: config.bandwidthMbps || 10,
      maxTilesPerFrame: config.maxTilesPerFrame || 50,
      frustumCullingEnabled: config.frustumCullingEnabled ?? true,
    };
    this.bandwidthEstimate = this.config.bandwidthMbps;
  }

  /**
   * Calculate frustum planes from camera
   */
  private calculateFrustum(camera: THREE.Camera): THREE.Frustum {
    const frustum = new THREE.Frustum();
    const projScreenMatrix = new THREE.Matrix4();
    
    if (camera instanceof THREE.PerspectiveCamera || camera instanceof THREE.OrthographicCamera) {
      projScreenMatrix.multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse);
      frustum.setFromProjectionMatrix(projScreenMatrix);
    }
    
    return frustum;
  }

  /**
   * Check if a tile's bounding box intersects with the camera frustum
   */
  private isTileInFrustum(tile: SceneTile, frustum: THREE.Frustum): boolean {
    if (!this.config.frustumCullingEnabled || !tile.bounds) {
      return true;
    }

    const box = new THREE.Box3(
      new THREE.Vector3(tile.bounds.min[0], tile.bounds.min[1], tile.bounds.min[2]),
      new THREE.Vector3(tile.bounds.max[0], tile.bounds.max[1], tile.bounds.max[2])
    );

    return frustum.intersectsBox(box);
  }

  /**
   * Calculate distance from camera to tile center
   */
  private calculateTileDistance(tile: SceneTile, cameraPosition: THREE.Vector3): number {
    if (!tile.bounds) return 0;

    const center = new THREE.Vector3(
      (tile.bounds.min[0] + tile.bounds.max[0]) / 2,
      (tile.bounds.min[1] + tile.bounds.max[1]) / 2,
      (tile.bounds.min[2] + tile.bounds.max[2]) / 2
    );

    return cameraPosition.distanceTo(center);
  }

  /**
   * Sort tiles by priority (distance and LOD)
   */
  private sortTilesByPriority(
    tiles: SceneTile[],
    cameraPosition: THREE.Vector3,
    frustum: THREE.Frustum
  ): SceneTile[] {
    return tiles
      .filter(tile => this.isTileInFrustum(tile, frustum))
      .sort((a, b) => {
        // Prioritize by LOD first (lower LOD = higher priority)
        const lodOrder = { high: 0, medium: 1, low: 2 };
        if (a.lod !== b.lod) {
          return lodOrder[a.lod] - lodOrder[b.lod];
        }
        
        // Then by distance (closer = higher priority)
        const distA = this.calculateTileDistance(a, cameraPosition);
        const distB = this.calculateTileDistance(b, cameraPosition);
        return distA - distB;
      });
  }

  /**
   * Get tiles that should be loaded for the current camera view
   */
  async requestTiles(
    sceneId: string,
    camera: THREE.Camera,
    apiClient: (request: TileRequest) => Promise<{ tiles: SceneTile[] }>
  ): Promise<SceneTile[]> {
    const cameraPosition = camera.position.clone();
    const cameraDirection = new THREE.Vector3();
    camera.getWorldDirection(cameraDirection);

    const fov = camera instanceof THREE.PerspectiveCamera ? camera.fov : 60;
    const near = camera instanceof THREE.PerspectiveCamera || camera instanceof THREE.OrthographicCamera ? camera.near : 0.1;
    const far = camera instanceof THREE.PerspectiveCamera || camera instanceof THREE.OrthographicCamera ? camera.far : 1000;

    // Request tiles from API
    const response = await apiClient({
      sceneId,
      camera: {
        position: [cameraPosition.x, cameraPosition.y, cameraPosition.z],
        direction: [cameraDirection.x, cameraDirection.y, cameraDirection.z],
        fov,
        near,
        far,
      },
      bandwidth_mbps: this.bandwidthEstimate,
      max_tiles: this.config.maxTilesPerFrame,
    });

    const tiles = response.tiles;

    // Calculate frustum for culling
    const frustum = this.calculateFrustum(camera);

    // Sort tiles by priority
    const sortedTiles = this.sortTilesByPriority(tiles, cameraPosition, frustum);

    // Limit to max tiles per frame
    const tilesToLoad = sortedTiles.slice(0, this.config.maxTilesPerFrame);

    // Update cache
    tilesToLoad.forEach(tile => {
      this.cache.set(tile.tileId, tile);
    });

    // Evict old tiles if cache is too large
    if (this.cache.size > this.config.maxCachedTiles) {
      const tilesToRemove = Array.from(this.cache.keys()).slice(
        0,
        this.cache.size - this.config.maxCachedTiles
      );
      tilesToRemove.forEach(tileId => this.cache.delete(tileId));
    }

    return tilesToLoad;
  }

  /**
   * Estimate bandwidth based on download speed
   */
  updateBandwidthEstimate(bytesDownloaded: number, timeMs: number): void {
    const mbps = (bytesDownloaded * 8) / (timeMs * 1000);
    // Exponential moving average
    this.bandwidthEstimate = this.bandwidthEstimate * 0.7 + mbps * 0.3;
  }

  /**
   * Get cached tile
   */
  getCachedTile(tileId: string): SceneTile | undefined {
    return this.cache.get(tileId);
  }

  /**
   * Check if tile is currently loading
   */
  isTileLoading(tileId: string): boolean {
    return this.loadingTiles.has(tileId);
  }

  /**
   * Mark tile as loading
   */
  markTileLoading(tileId: string): void {
    this.loadingTiles.add(tileId);
  }

  /**
   * Mark tile as loaded
   */
  markTileLoaded(tileId: string): void {
    this.loadingTiles.delete(tileId);
  }

  /**
   * Clear all cached tiles
   */
  clearCache(): void {
    this.cache.clear();
    this.loadingTiles.clear();
  }

  /**
   * Get cache statistics
   */
  getCacheStats() {
    return {
      cachedTiles: this.cache.size,
      loadingTiles: this.loadingTiles.size,
      bandwidthEstimate: this.bandwidthEstimate,
      maxCachedTiles: this.config.maxCachedTiles,
    };
  }
}

// Singleton instance
let tileManagerInstance: TileManager | null = null;

export function getTileManager(config?: TileManagerConfig): TileManager {
  if (!tileManagerInstance) {
    tileManagerInstance = new TileManager(config);
  }
  return tileManagerInstance;
}
