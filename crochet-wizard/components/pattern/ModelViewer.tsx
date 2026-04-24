import React from 'react';
import { GLView } from 'expo-gl';
import { Renderer } from 'expo-three';
import * as THREE from 'three';

export default function ModelViewer() {
  let timeout: any;

  const onContextCreate = async (gl: any) => {
    // 1. Setup Scene & Camera
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(
      75, 
      gl.drawingBufferWidth / gl.drawingBufferHeight, 
      0.1, 
      1000
    );
    camera.position.z = 3;

    // 2. Setup Renderer (Use the expo-three wrapper)
    const renderer = new Renderer({ gl });
    renderer.setSize(gl.drawingBufferWidth, gl.drawingBufferHeight);

    // 3. Setup Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);
    
    const pointLight = new THREE.PointLight(0xffffff, 1);
    pointLight.position.set(10, 10, 10);
    scene.add(pointLight);

    // 4. Create Placeholder Crochet "Stitch" (Torus)
    const geometry = new THREE.TorusGeometry(1, 0.4, 16, 100);
    const material = new THREE.MeshStandardMaterial({ 
      color: '#52a4b5', // Pacific Blue
      roughness: 0.7,
      metalness: 0.2
    });
    const stitch = new THREE.Mesh(geometry, material);
    scene.add(stitch);

    // 5. Setup Animation Loop
    const render = () => {
      timeout = requestAnimationFrame(render);
      
      // Add some slow rotation for the demo
      stitch.rotation.y += 0.01;
      stitch.rotation.x += 0.005;

      renderer.render(scene, camera);

      // Clean up frame
      gl.endFrameEXP();
    };

    render();
  };

  // Clean up animation if component unmounts
  React.useEffect(() => {
    return () => clearTimeout(timeout);
  }, []);

  return (
    <GLView
      style={{ flex: 1 }}
      onContextCreate={onContextCreate}
    />
  );
}