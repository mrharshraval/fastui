"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";

export function HalftoneField({
  columns = 160,
  baseColor = "#555555",
  activeColor = "#c2ff00",
  stemColor = "#e6ff4d",
  hoverRadius = 150,
  jitterAmount = 30,
  colorEaseSpeed = 0.08,
  stemFraction = 0.2,
}) {
  const mountRef = useRef(null);

  useEffect(() => {
    if (!mountRef.current) return;

    // --- Setup Scene ---
    const container = mountRef.current;
    let width = container.clientWidth || window.innerWidth;
    let height = container.clientHeight || window.innerHeight;

    const scene = new THREE.Scene();
    const camera = new THREE.OrthographicCamera(0, width, height, 0, 0.1, 100);
    camera.position.z = 10;

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    // --- Generate Source Image (Offscreen Canvas) ---
    const imgCanvas = document.createElement("canvas");
    imgCanvas.width = width;
    imgCanvas.height = height;
    const imgCtx = imgCanvas.getContext("2d", { willReadFrequently: true });
    
    // Draw a butterfly/moth shape
    imgCtx.fillStyle = "black"; // Background
    imgCtx.fillRect(0, 0, width, height);

    imgCtx.save();
    imgCtx.translate(width / 2, height / 2);
    // Rotate to match the angled moth in the screenshot
    imgCtx.rotate(-Math.PI / 8); 
    // Scale up the path to fill a good portion of the screen
    const s = Math.min(width, height) / 100;
    imgCtx.scale(s, s);
    // Center the path (approximate bounds center is 43, 47)
    imgCtx.translate(-43, -47);
    
    imgCtx.fillStyle = "white"; // Foreground
    // A nice geometric butterfly/moth path
    const butterfly = new Path2D("M61.88,29.35c-2.83,5.08-16.1,16.48-24.96,21.84c-3.1,1.88-5.32,1.21-7.23-1.04C25.04,44.62,16.27,33.15,14,30.34c-2.48-3.07-3.76-7.58-1.57-11.45c3.34-5.91,12.39-4.85,17.48-1.63c3.78,2.39,8.5,8.12,11.23,12.7c1.47-4.99,6.79-11.53,10.65-14.4c5.07-3.76,14.62-5.45,18.44-0.12C73.81,20.44,71.29,26.4,61.88,29.35z M50.48,58.32c-3.09-2.02-8.35-8.49-10.22-11.47c-0.81-1.3-1.87-1.33-2.92-0.34c-5.18,4.89-14.73,15.71-17.65,20.21c-2.87,4.42-3.12,9.36-0.33,13.06c4.25,5.64,13.75,2.15,18.17-1.74c3.29-2.9,7.56-9.97,9.58-14.93c0.31,5.2,4.64,13.4,7.88,17.15c4.26,4.92,13.62,7.96,18.15,3.01C77.4,78.6,76.51,71.74,50.48,58.32z");
    imgCtx.fill(butterfly);
    imgCtx.restore();

    const imgData = imgCtx.getImageData(0, 0, width, height).data;

    // --- Calculate Grid Layout ---
    const cellSize = width / columns;
    const rows = Math.ceil(height / cellSize);
    const particleCount = columns * rows;

    // --- Initialize Data Arrays ---
    const particles = [];
    const baseColorObj = new THREE.Color(baseColor);
    const activeColorObj = new THREE.Color(activeColor);
    const stemColorObj = new THREE.Color(stemColor);

    // Three.js instances
    const dotGeometry = new THREE.CircleGeometry(cellSize * 0.4, 8); // Low poly circle
    const dotMaterial = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true });
    const dotMesh = new THREE.InstancedMesh(dotGeometry, dotMaterial, particleCount);
    
    // Stem geometry (thin vertical line)
    const stemGeometry = new THREE.CylinderGeometry(cellSize * 0.1, cellSize * 0.1, 1, 4);
    stemGeometry.translate(0, 0.5, 0); // Pivot at bottom
    const stemMaterial = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.8 });
    const stemMesh = new THREE.InstancedMesh(stemGeometry, stemMaterial, particleCount);

    const matrix = new THREE.Matrix4();
    const color = new THREE.Color();

    let i = 0;
    for (let y = 0; y < rows; y++) {
      for (let x = 0; x < columns; x++) {
        const px = x * cellSize + cellSize / 2;
        const py = y * cellSize + cellSize / 2;

        // Sample luminance from canvas (read the red channel as it's grayscale)
        const sampleX = Math.floor(px);
        const sampleY = Math.floor(py); // In canvas, Y goes down.
        const pixelIdx = (sampleY * width + sampleX) * 4;
        let luminance = 0;
        if (pixelIdx >= 0 && pixelIdx < imgData.length) {
           luminance = imgData[pixelIdx] / 255;
        }

        // Base opacity/scale based on luminance. 
        // 0.1 for empty areas (graph paper feel), 1.0 for image areas.
        const baseScale = 0.2 + luminance * 0.8;
        const baseOpacity = 0.2 + luminance * 0.8;

        // Determine if this dot can grow a stem
        const hasStem = Math.random() < stemFraction;

        particles.push({
          x: px,
          y: height - py, // Three.js Y goes up, so flip Y for rendering
          baseScale,
          baseOpacity,
          luminance,
          hasStem,
          currentR: baseColorObj.r,
          currentG: baseColorObj.g,
          currentB: baseColorObj.b,
          currentStemHeight: 0,
          targetStemHeight: 0,
          jitterRadius: hoverRadius + (Math.random() - 0.5) * jitterAmount,
          stemMaxHeight: (20 + Math.random() * 50) * luminance + 10,
        });

        // Set initial positions
        matrix.makeTranslation(px, height - py, 0);
        matrix.scale(new THREE.Vector3(baseScale, baseScale, 1));
        dotMesh.setMatrixAt(i, matrix);
        dotMesh.setColorAt(i, baseColorObj);
        
        // Initial stem (invisible)
        matrix.makeTranslation(px, height - py, -0.1); // slightly behind
        matrix.scale(new THREE.Vector3(1, 0.001, 1));
        stemMesh.setMatrixAt(i, matrix);
        stemMesh.setColorAt(i, stemColorObj);

        i++;
      }
    }

    dotMesh.instanceMatrix.needsUpdate = true;
    dotMesh.instanceColor.needsUpdate = true;
    stemMesh.instanceMatrix.needsUpdate = true;
    stemMesh.instanceColor.needsUpdate = true;

    scene.add(dotMesh);
    scene.add(stemMesh);

    // --- Interaction ---
    const mouse = { x: -1000, y: -1000 };
    let hasMoved = false;
    const handleMouseMove = (e) => {
      // Don't activate on absolute window move, only when over hero
      const rect = container.getBoundingClientRect();
      if (e.clientX >= rect.left && e.clientX <= rect.right && e.clientY >= rect.top && e.clientY <= rect.bottom) {
        mouse.x = e.clientX - rect.left;
        mouse.y = height - (e.clientY - rect.top); // Flip Y to match Three.js
        hasMoved = true;
      } else {
        mouse.x = -1000;
        mouse.y = -1000;
      }
    };
    window.addEventListener("mousemove", handleMouseMove);

    // --- Animation Loop ---
    let animationFrameId;
    const animate = () => {
      let needsDotUpdate = false;
      let needsStemUpdate = false;

      // Only iterate if we need to ease (or if mouse is active) to save perf, 
      // but easing requires continuous updates until target is reached.
      for (let j = 0; j < particleCount; j++) {
        const p = particles[j];
        
        // Calculate distance to mouse
        const dx = mouse.x - p.x;
        const dy = mouse.y - p.y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        const isActive = dist < p.jitterRadius;
        const targetColor = isActive ? activeColorObj : baseColorObj;

        // Lerp color
        if (Math.abs(p.currentR - targetColor.r) > 0.01 || Math.abs(p.currentG - targetColor.g) > 0.01 || Math.abs(p.currentB - targetColor.b) > 0.01) {
            p.currentR += (targetColor.r - p.currentR) * colorEaseSpeed;
            p.currentG += (targetColor.g - p.currentG) * colorEaseSpeed;
            p.currentB += (targetColor.b - p.currentB) * colorEaseSpeed;

            color.setRGB(p.currentR, p.currentG, p.currentB);
            dotMesh.setColorAt(j, color);
            needsDotUpdate = true;
        }

        // Lerp stems
        if (p.hasStem) {
           p.targetStemHeight = isActive ? p.stemMaxHeight : 0.001;
           const heightDiff = p.targetStemHeight - p.currentStemHeight;
           
           if (Math.abs(heightDiff) > 0.1) {
             p.currentStemHeight += heightDiff * colorEaseSpeed;
             matrix.makeTranslation(p.x, p.y, -0.1);
             // Rotate slightly based on mouse pos? No, just vertical for now
             matrix.scale(new THREE.Vector3(1, p.currentStemHeight, 1));
             stemMesh.setMatrixAt(j, matrix);
             needsStemUpdate = true;
           }
        }
      }

      if (needsDotUpdate) dotMesh.instanceColor.needsUpdate = true;
      if (needsStemUpdate) stemMesh.instanceMatrix.needsUpdate = true;

      renderer.render(scene, camera);
      animationFrameId = requestAnimationFrame(animate);
    };
    animate();

    // --- Resize Handler ---
    const handleResize = () => {
      const newWidth = container.clientWidth;
      const newHeight = container.clientHeight;
      camera.right = newWidth;
      camera.top = newHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(newWidth, newHeight);
      height = newHeight; 
    };
    window.addEventListener("resize", handleResize);

    // --- Cleanup ---
    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("resize", handleResize);
      container.removeChild(renderer.domElement);
      renderer.dispose();
      dotGeometry.dispose();
      dotMaterial.dispose();
      stemGeometry.dispose();
      stemMaterial.dispose();
    };
  }, [columns, baseColor, activeColor, stemColor, hoverRadius, jitterAmount, colorEaseSpeed, stemFraction]);

  // Remove pointer events so it doesn't block buttons overlaid on top
  return <div ref={mountRef} className="w-full h-full absolute inset-0 z-0 overflow-hidden pointer-events-none" />;
}
