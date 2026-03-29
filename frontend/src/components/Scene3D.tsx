/**
 * Basic 3D Scene component using React Three Fiber
 * This demonstrates the Three.js integration setup
 */

import { Canvas } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';

export function Scene3D() {
  return (
    <div className="w-full h-screen">
      <Canvas camera={{ position: [0, 0, 5], fov: 75 }}>
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} />
        <mesh>
          <boxGeometry args={[1, 1, 1]} />
          <meshStandardMaterial color="orange" />
        </mesh>
        <OrbitControls />
      </Canvas>
    </div>
  );
}
