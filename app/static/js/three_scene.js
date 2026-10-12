/**
 * OmniFind AI • 3D Spatial Campus Radar & Hologram Engine
 * Powered by Three.js WebGL
 */

let campusScene, campusCamera, campusRenderer;
let buildingMeshes = [];
let beaconObjects = [];
let hoveredBuilding = null;
let selectedBuilding = null;
let isAutoRotating = true;
let isDragging = false;
let previousMousePosition = { x: 0, y: 0 };
let targetCameraPos = { x: 0, y: 75, z: 90 };
let currentCameraPos = { x: 0, y: 75, z: 90 };
let lookAtTarget = new THREE.Vector3(0, 0, 0);

// Building architectural layout and metadata
const CAMPUS_BUILDING_SPECS = [
  {
    name: "Central Library",
    x: -25, z: -20,
    width: 14, height: 18, depth: 16,
    color: 0x3b82f6,
    roofColor: 0x60a5fa,
    zone: "Academic / Quiet Zone"
  },
  {
    name: "Tech Hub / Engineering Block",
    x: 25, z: -25,
    width: 18, height: 22, depth: 14,
    color: 0x0284c7,
    roofColor: 0x38bdf8,
    zone: "Engineering / Hardware Labs"
  },
  {
    name: "Science Hall",
    x: 40, z: 10,
    width: 15, height: 16, depth: 15,
    color: 0x10b981,
    roofColor: 0x34d399,
    zone: "Sciences / Research"
  },
  {
    name: "Student Center & Union",
    x: 0, z: 0,
    width: 20, height: 14, depth: 20,
    color: 0xf59e0b,
    roofColor: 0xfbbf24,
    zone: "Central Student Life"
  },
  {
    name: "Campus Cafeteria & Food Court",
    x: -35, z: 15,
    width: 16, height: 10, depth: 18,
    color: 0xef4444,
    roofColor: 0xf87171,
    zone: "Dining & Food Court"
  },
  {
    name: "Sports Complex & Gymnasium",
    x: -20, z: 45,
    width: 24, height: 12, depth: 20,
    color: 0x06b6d4,
    roofColor: 0x22d3ee,
    zone: "Athletics & Recreation"
  },
  {
    name: "North Hostels & Dormitories",
    x: 30, z: 40,
    width: 22, height: 20, depth: 16,
    color: 0xec4899,
    roofColor: 0xf472b6,
    zone: "Residential Quads"
  }
];

function init3DCampusScene() {
  const container = document.getElementById("three-campus-container");
  if (!container) return;

  const width = container.clientWidth || 800;
  const height = container.clientHeight || 550;

  // 1. Scene
  campusScene = new THREE.Scene();
  campusScene.background = new THREE.Color(0x070a13);
  campusScene.fog = new THREE.FogExp2(0x070a13, 0.007);

  // 2. Camera
  campusCamera = new THREE.PerspectiveCamera(45, width / height, 1, 1000);
  campusCamera.position.set(currentCameraPos.x, currentCameraPos.y, currentCameraPos.z);
  campusCamera.lookAt(lookAtTarget);

  // 3. Renderer
  campusRenderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
  campusRenderer.setSize(width, height);
  campusRenderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  campusRenderer.shadowMap.enabled = true;
  campusRenderer.shadowMap.type = THREE.PCFSoftShadowMap;
  container.innerHTML = "";
  container.appendChild(campusRenderer.domElement);

  // 4. Lights
  const ambientLight = new THREE.AmbientLight(0x242d4a, 1.8);
  campusScene.add(ambientLight);

  const dirLight = new THREE.DirectionalLight(0xa5f3fc, 1.5);
  dirLight.position.set(60, 100, 40);
  dirLight.castShadow = true;
  dirLight.shadow.mapSize.width = 1024;
  dirLight.shadow.mapSize.height = 1024;
  campusScene.add(dirLight);

  // Center glowing point lights
  const pointLightCenter = new THREE.PointLight(0x06b6d4, 2.5, 120);
  pointLightCenter.position.set(0, 20, 0);
  campusScene.add(pointLightCenter);

  const pointLightSky = new THREE.PointLight(0x0284c7, 2.0, 120);
  pointLightSky.position.set(30, 25, -20);
  campusScene.add(pointLightSky);

  // 5. Ground Cyber-Grid & Terrain
  createCampusGround();

  // 6. Architectural Buildings
  createCampusBuildings();

  // 7. Mouse & Touch Controls
  setupCameraInteraction(container);

  // 8. Animation Loop
  animateScene();

  window.addEventListener("resize", onWindowResize);
}

function createCampusGround() {
  // Main ground plane
  const planeGeo = new THREE.PlaneGeometry(240, 240);
  const planeMat = new THREE.MeshStandardMaterial({
    color: 0x0c1020,
    roughness: 0.85,
    metalness: 0.2
  });
  const ground = new THREE.Mesh(planeGeo, planeMat);
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = -0.1;
  ground.receiveShadow = true;
  campusScene.add(ground);

  // Cyber Grid
  const gridHelper = new THREE.GridHelper(220, 44, 0x06b6d4, 0x1e293b);
  gridHelper.position.y = 0.05;
  campusScene.add(gridHelper);

  // Glowing connecting pathways
  const pathMat = new THREE.MeshBasicMaterial({ color: 0x0891b2, transparent: true, opacity: 0.45 });
  
  CAMPUS_BUILDING_SPECS.forEach(b => {
    // Road line from Student Center (0,0) to building
    const roadPoints = [
      new THREE.Vector3(0, 0.1, 0),
      new THREE.Vector3(b.x, 0.1, b.z)
    ];
    const roadGeo = new THREE.BufferGeometry().setFromPoints(roadPoints);
    const roadLine = new THREE.Line(roadGeo, pathMat);
    campusScene.add(roadLine);
  });
}

function createCampusBuildings() {
  buildingMeshes = [];

  CAMPUS_BUILDING_SPECS.forEach((spec, index) => {
    const buildingGroup = new THREE.Group();
    buildingGroup.position.set(spec.x, 0, spec.z);

    // Main Body Box
    const bodyGeo = new THREE.BoxGeometry(spec.width, spec.height, spec.depth);
    const bodyMat = new THREE.MeshStandardMaterial({
      color: 0x161e38,
      roughness: 0.4,
      metalness: 0.6,
      transparent: true,
      opacity: 0.95
    });
    const bodyMesh = new THREE.Mesh(bodyGeo, bodyMat);
    bodyMesh.position.y = spec.height / 2;
    bodyMesh.castShadow = true;
    bodyMesh.receiveShadow = true;
    buildingGroup.add(bodyMesh);

    // Glowing Neon Edge / Wireframe
    const edgesGeo = new THREE.EdgesGeometry(bodyGeo);
    const edgesMat = new THREE.LineBasicMaterial({ color: spec.color, linewidth: 2 });
    const wireframe = new THREE.LineSegments(edgesGeo, edgesMat);
    wireframe.position.y = spec.height / 2;
    buildingGroup.add(wireframe);

    // Roof Accent Podium
    const roofGeo = new THREE.BoxGeometry(spec.width * 0.7, 2, spec.depth * 0.7);
    const roofMat = new THREE.MeshStandardMaterial({
      color: spec.roofColor,
      roughness: 0.3,
      metalness: 0.7,
      emissive: spec.color,
      emissiveIntensity: 0.25
    });
    const roofMesh = new THREE.Mesh(roofGeo, roofMat);
    roofMesh.position.y = spec.height + 1;
    buildingGroup.add(roofMesh);

    // Interactive Pulsing Beacon Ring & Orb (Floating Radar Indicator)
    const beaconY = spec.height + 7;

    // Glowing Orb
    const orbGeo = new THREE.SphereGeometry(1.2, 16, 16);
    const orbMat = new THREE.MeshBasicMaterial({ color: spec.color });
    const orbMesh = new THREE.Mesh(orbGeo, orbMat);
    orbMesh.position.y = beaconY;
    buildingGroup.add(orbMesh);

    // Pulsing Outer Ring
    const ringGeo = new THREE.RingGeometry(1.8, 2.5, 32);
    const ringMat = new THREE.MeshBasicMaterial({
      color: spec.color,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.75
    });
    const ringMesh = new THREE.Mesh(ringGeo, ringMat);
    ringMesh.rotation.x = Math.PI / 2;
    ringMesh.position.y = beaconY;
    buildingGroup.add(ringMesh);

    // Metadata attachments for Raycasting
    buildingGroup.userData = {
      name: spec.name,
      zone: spec.zone,
      index: index,
      wireframe: wireframe,
      ringMesh: ringMesh,
      baseColor: spec.color,
      beaconY: beaconY,
      spec: spec
    };

    bodyMesh.userData = buildingGroup.userData;

    campusScene.add(buildingGroup);
    buildingMeshes.push(bodyMesh);
    beaconObjects.push({ ring: ringMesh, orb: orbMesh, group: buildingGroup });
  });
}

function setupCameraInteraction(container) {
  const raycaster = new THREE.Raycaster();
  const mouse = new THREE.Vector2();
  let dragDistance = 0;

  container.addEventListener("mousedown", (e) => {
    isDragging = true;
    dragDistance = 0;
    previousMousePosition = { x: e.clientX, y: e.clientY };
  });

  window.addEventListener("mouseup", () => {
    isDragging = false;
  });

  container.addEventListener("mousemove", (e) => {
    const rect = container.getBoundingClientRect();
    mouse.x = ((e.clientX - rect.left) / container.clientWidth) * 2 - 1;
    mouse.y = -((e.clientY - rect.top) / container.clientHeight) * 2 + 1;

    // Orbit Camera Dragging
    if (isDragging) {
      isAutoRotating = false;
      const deltaX = e.clientX - previousMousePosition.x;
      const deltaY = e.clientY - previousMousePosition.y;
      dragDistance += Math.hypot(deltaX, deltaY);

      const radius = Math.sqrt(currentCameraPos.x ** 2 + currentCameraPos.z ** 2);
      let theta = Math.atan2(currentCameraPos.z, currentCameraPos.x);

      theta -= deltaX * 0.008;
      currentCameraPos.x = radius * Math.cos(theta);
      currentCameraPos.z = radius * Math.sin(theta);

      currentCameraPos.y = Math.max(25, Math.min(130, currentCameraPos.y - deltaY * 0.3));

      targetCameraPos.x = currentCameraPos.x;
      targetCameraPos.y = currentCameraPos.y;
      targetCameraPos.z = currentCameraPos.z;

      previousMousePosition = { x: e.clientX, y: e.clientY };
    }

    // Raycast building hover
    raycaster.setFromCamera(mouse, campusCamera);
    const intersects = raycaster.intersectObjects(buildingMeshes, false);

    if (intersects.length > 0) {
      const hit = intersects[0].object;
      const data = hit.userData;
      if (hoveredBuilding !== data.name) {
        hoveredBuilding = data.name;
        container.style.cursor = "pointer";
        updateBuildingHUD(data.name, data.zone);
        highlightBuildingWireframe(data.name);
      }
    } else {
      if (hoveredBuilding) {
        resetBuildingWireframes();
        hoveredBuilding = null;
        container.style.cursor = "default";
      }
    }
  });

  container.addEventListener("click", (e) => {
    // If user dragged to orbit camera, ignore click
    if (dragDistance > 6) return;
    const rect = container.getBoundingClientRect();
    mouse.x = ((e.clientX - rect.left) / container.clientWidth) * 2 - 1;
    mouse.y = -((e.clientY - rect.top) / container.clientHeight) * 2 + 1;

    raycaster.setFromCamera(mouse, campusCamera);
    const intersects = raycaster.intersectObjects(buildingMeshes, false);

    if (intersects.length > 0) {
      const data = intersects[0].object.userData;
      focusBuilding(data.name);
      // Filter items in the feed
      if (window.selectLocationFilter) {
        window.selectLocationFilter(data.name);
      }
    }
  });

  // Touch Support for mobile / touch screens
  container.addEventListener("touchstart", (e) => {
    if (e.touches.length === 1) {
      isDragging = true;
      dragDistance = 0;
      const t = e.touches[0];
      previousMousePosition = { x: t.clientX, y: t.clientY };
    }
  }, { passive: true });

  container.addEventListener("touchmove", (e) => {
    if (isDragging && e.touches.length === 1) {
      isAutoRotating = false;
      const t = e.touches[0];
      const deltaX = t.clientX - previousMousePosition.x;
      const deltaY = t.clientY - previousMousePosition.y;
      dragDistance += Math.hypot(deltaX, deltaY);

      const radius = Math.sqrt(currentCameraPos.x ** 2 + currentCameraPos.z ** 2);
      let theta = Math.atan2(currentCameraPos.z, currentCameraPos.x);

      theta -= deltaX * 0.008;
      currentCameraPos.x = radius * Math.cos(theta);
      currentCameraPos.z = radius * Math.sin(theta);
      currentCameraPos.y = Math.max(25, Math.min(130, currentCameraPos.y - deltaY * 0.3));

      targetCameraPos.x = currentCameraPos.x;
      targetCameraPos.y = currentCameraPos.y;
      targetCameraPos.z = currentCameraPos.z;

      previousMousePosition = { x: t.clientX, y: t.clientY };
    }
  }, { passive: true });

  window.addEventListener("touchend", () => {
    isDragging = false;
  });

  // Wheel Zoom
  container.addEventListener("wheel", (e) => {
    e.preventDefault();
    const factor = e.deltaY > 0 ? 1.08 : 0.92;
    currentCameraPos.x *= factor;
    currentCameraPos.y *= factor;
    currentCameraPos.z *= factor;

    // Clamping
    currentCameraPos.y = Math.max(30, Math.min(150, currentCameraPos.y));
    targetCameraPos.x = currentCameraPos.x;
    targetCameraPos.y = currentCameraPos.y;
    targetCameraPos.z = currentCameraPos.z;
  });
}

function focusBuilding(name) {
  selectedBuilding = name;
  const spec = CAMPUS_BUILDING_SPECS.find(b => b.name === name);
  if (!spec) return;

  targetCameraPos = {
    x: spec.x + 30,
    y: 35,
    z: spec.z + 40
  };
  lookAtTarget = new THREE.Vector3(spec.x, 10, spec.z);
  updateBuildingHUD(spec.name, spec.zone);
  highlightBuildingWireframe(name);
}

function highlightBuildingWireframe(name) {
  CAMPUS_BUILDING_SPECS.forEach(spec => {
    const mesh = buildingMeshes.find(m => m.userData.name === spec.name);
    if (!mesh) return;
    const wire = mesh.parent.userData.wireframe;
    if (spec.name === name) {
      wire.material.color.setHex(0x00f2fe);
      wire.material.linewidth = 4;
    } else {
      wire.material.color.setHex(spec.color);
      wire.material.linewidth = 1;
    }
  });
}

function resetBuildingWireframes() {
  CAMPUS_BUILDING_SPECS.forEach(spec => {
    const mesh = buildingMeshes.find(m => m.userData.name === spec.name);
    if (mesh && mesh.parent) {
      mesh.parent.userData.wireframe.material.color.setHex(spec.color);
    }
  });
}

function updateBuildingHUD(name, zone) {
  const nameEl = document.getElementById("hud-building-name");
  const zoneEl = document.getElementById("hud-building-zone");
  const lostEl = document.getElementById("hud-lost-count");
  const foundEl = document.getElementById("hud-found-count");
  const rateEl = document.getElementById("hud-recovery-rate");

  if (nameEl) nameEl.textContent = name;
  if (zoneEl) zoneEl.textContent = zone;

  if (window.campusStatsData && window.campusStatsData.location_hotspots) {
    const stat = window.campusStatsData.location_hotspots.find(h => h.location === name);
    if (stat) {
      if (lostEl) lostEl.textContent = stat.lost_count;
      if (foundEl) foundEl.textContent = stat.found_count;
      if (rateEl) rateEl.textContent = `${stat.recovery_rate}%`;
    }
  }
}

function reset3DCamera() {
  targetCameraPos = { x: 0, y: 75, z: 90 };
  lookAtTarget = new THREE.Vector3(0, 0, 0);
  selectedBuilding = null;
  resetBuildingWireframes();
}

function toggle3DAutoRotate() {
  isAutoRotating = !isAutoRotating;
  const btn = document.getElementById("rotate-toggle-btn");
  if (btn) {
    btn.textContent = isAutoRotating ? "Pause Orbit" : "Resume Orbit";
  }
}

function onWindowResize() {
  const container = document.getElementById("three-campus-container");
  if (!container || !campusCamera || !campusRenderer) return;

  const width = container.clientWidth;
  const height = container.clientHeight;

  campusCamera.aspect = width / height;
  campusCamera.updateProjectionMatrix();
  campusRenderer.setSize(width, height);
}

let clock = new THREE.Clock();

function animateScene() {
  requestAnimationFrame(animateScene);

  const time = clock.getElapsedTime();

  // Smooth camera interpolation (inertial damping)
  campusCamera.position.x += (targetCameraPos.x - campusCamera.position.x) * 0.05;
  campusCamera.position.y += (targetCameraPos.y - campusCamera.position.y) * 0.05;
  campusCamera.position.z += (targetCameraPos.z - campusCamera.position.z) * 0.05;
  campusCamera.lookAt(lookAtTarget);

  // Auto orbit
  if (isAutoRotating && !isDragging) {
    const angle = 0.0015;
    const x = targetCameraPos.x;
    const z = targetCameraPos.z;
    targetCameraPos.x = x * Math.cos(angle) - z * Math.sin(angle);
    targetCameraPos.z = x * Math.sin(angle) + z * Math.cos(angle);
  }

  // Pulsing Beacons
  beaconObjects.forEach((b, idx) => {
    const pulse = 1 + 0.3 * Math.sin(time * 3 + idx);
    b.ring.scale.set(pulse, pulse, 1);
    b.ring.material.opacity = 0.4 + 0.3 * Math.sin(time * 3 + idx);
    b.orb.position.y = b.group.userData.beaconY + 0.5 * Math.sin(time * 2 + idx);
  });

  campusRenderer.render(campusScene, campusCamera);
}

// ==================== 3D HOLOGRAPHIC ITEM INSPECTOR ====================
let hologramRenderer = null;
let hologramAnimId = null;

function cleanup3DHologram() {
  if (hologramAnimId) {
    cancelAnimationFrame(hologramAnimId);
    hologramAnimId = null;
  }
  if (hologramRenderer) {
    try {
      hologramRenderer.dispose();
      if (hologramRenderer.domElement && hologramRenderer.domElement.parentNode) {
        hologramRenderer.domElement.parentNode.removeChild(hologramRenderer.domElement);
      }
    } catch (e) {
      console.warn("Hologram cleanup exception:", e);
    }
    hologramRenderer = null;
  }
}

function render3DItemHologram(containerId, category, brand, primaryColor) {
  cleanup3DHologram();

  const container = document.getElementById(containerId);
  if (!container) return;

  container.innerHTML = "";
  const width = container.clientWidth || 300;
  const height = container.clientHeight || 200;

  const hScene = new THREE.Scene();
  const hCamera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
  hCamera.position.set(0, 2, 4);
  hCamera.lookAt(0, 0, 0);

  const hRenderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  hRenderer.setSize(width, height);
  hRenderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  hologramRenderer = hRenderer;
  container.appendChild(hRenderer.domElement);

  // Lighting
  const light = new THREE.PointLight(0x06b6d4, 3, 20);
  light.position.set(2, 3, 2);
  hScene.add(light);
  hScene.add(new THREE.AmbientLight(0xffffff, 0.8));

  // Determine geometry by category
  let meshGeo;
  if (category && category.includes("Electronics")) {
    meshGeo = new THREE.BoxGeometry(1.8, 0.2, 1.2); // Laptop/Tablet
  } else if (category && category.includes("Bottles")) {
    meshGeo = new THREE.CylinderGeometry(0.5, 0.5, 1.8, 16);
  } else if (category && category.includes("ID Cards")) {
    meshGeo = new THREE.BoxGeometry(1.4, 0.05, 0.9);
  } else if (category && category.includes("Bags")) {
    meshGeo = new THREE.DodecahedronGeometry(0.9);
  } else {
    meshGeo = new THREE.TorusGeometry(0.7, 0.25, 16, 32);
  }

  // Holographic Wireframe + Shaded Core
  const coreMat = new THREE.MeshStandardMaterial({
    color: 0x06b6d4,
    wireframe: false,
    transparent: true,
    opacity: 0.35,
    roughness: 0.1,
    metalness: 0.9
  });
  const coreMesh = new THREE.Mesh(meshGeo, coreMat);
  hScene.add(coreMesh);

  const wireGeo = new THREE.EdgesGeometry(meshGeo);
  const wireMat = new THREE.LineBasicMaterial({ color: 0x00f2fe, linewidth: 2 });
  const wireMesh = new THREE.LineSegments(wireGeo, wireMat);
  hScene.add(wireMesh);

  // Scanner grid ring
  const gridRingGeo = new THREE.RingGeometry(1.2, 1.3, 32);
  const gridRingMat = new THREE.MeshBasicMaterial({ color: 0x06b6d4, side: THREE.DoubleSide });
  const gridRing = new THREE.Mesh(gridRingGeo, gridRingMat);
  gridRing.rotation.x = Math.PI / 2;
  hScene.add(gridRing);

  let hClock = new THREE.Clock();

  function animateHolo() {
    if (!document.getElementById(containerId) || !hologramRenderer) return;
    hologramAnimId = requestAnimationFrame(animateHolo);

    const t = hClock.getElapsedTime();
    coreMesh.rotation.y = t * 0.8;
    coreMesh.rotation.x = 0.2 * Math.sin(t);
    wireMesh.rotation.y = t * 0.8;
    wireMesh.rotation.x = 0.2 * Math.sin(t);

    gridRing.position.y = 0.6 * Math.sin(t * 2);

    hRenderer.render(hScene, hCamera);
  }
  animateHolo();
}

window.init3DCampusScene = init3DCampusScene;
window.reset3DCamera = reset3DCamera;
window.toggle3DAutoRotate = toggle3DAutoRotate;
window.render3DItemHologram = render3DItemHologram;
window.cleanup3DHologram = cleanup3DHologram;
window.focusBuilding = focusBuilding;
