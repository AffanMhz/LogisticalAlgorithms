// ISSContainerViewer.js
// Non-modular version for direct browser use

class ISSContainerViewer {
  constructor(containerRef, containers = []) {
    // Handle both React ref objects and direct DOM elements
    this.containerRef = containerRef.current ? containerRef.current : containerRef;
    
    // Initialize Three.js components
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(
      75, 
      this.containerRef.clientWidth / this.containerRef.clientHeight, 
      0.1, 
      1000
    );
    this.camera.position.set(5, 5, 5);
    this.camera.lookAt(0, 0, 0);

    // Initialize renderer with proper dimensions
    this.renderer = new THREE.WebGLRenderer({ antialias: true });
    this.renderer.setSize(
      this.containerRef.clientWidth, 
      this.containerRef.clientHeight
    );
    this.renderer.setClearColor(0x111111);
    this.containerRef.appendChild(this.renderer.domElement);

    // Add lights
    this.initLights();
    
    // Add axes helper
    this.scene.add(new THREE.AxesHelper(5));

    // Store items and containers
    this.items = [];
    this.containers = [];
    
    // Initialize with provided containers
    this.createContainers(containers);

    // Set up event listeners
    this.handleResize = this.handleResize.bind(this);
    window.addEventListener('resize', this.handleResize);

    // Start animation loop
    this.animate = this.animate.bind(this);
    this.animationFrameId = requestAnimationFrame(this.animate);
  }

  initLights() {
    const ambientLight = new THREE.AmbientLight(0x404040);
    this.scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
    directionalLight.position.set(1, 1, 1);
    this.scene.add(directionalLight);
  }

  createContainers(containers) {
    // Clear existing containers
    this.containers.forEach(container => this.scene.remove(container));
    this.containers = [];
    
    // Calculate camera position based on containers
    if (containers.length > 0) {
      // Adjust camera to view all containers
      const totalWidth = containers.length * 3; // Approximate width needed
      this.camera.position.set(totalWidth / 2, totalWidth / 2, totalWidth / 2);
      this.camera.lookAt(totalWidth / 4, 0, 0);
    }

    // Spacing between containers (in units)
    const SPACING = 2; // 2 units = 200cm spacing between containers
    let currentX = 0;
    
    return containers.map((container, index) => {
      // Create container wireframe
      const geometry = new THREE.BoxGeometry(
        container.width / 100,
        container.depth / 100,
        container.height / 100
      );
      const edges = new THREE.EdgesGeometry(geometry);
      const containerObj = new THREE.LineSegments(
        edges,
        new THREE.LineBasicMaterial({ color: 0xaaaaaa })
      );
      
      // Position containers side by side with spacing
      // Each container has its own coordinate system where (0,0,0) is at the bottom left corner of the open face
      containerObj.position.set(currentX, 0, 0);
      
      // Update position for next container (current width + spacing)
      currentX += (container.width / 100) + SPACING;
      
      // Store container metadata
      containerObj.userData = { 
        containerId: container.containerId,
        zone: container.zone, 
        width: container.width,
        depth: container.depth,
        height: container.height
      };
      
      // Add coordinate system arrows for this container
      const axesHelper = new THREE.AxesHelper(0.5);
      axesHelper.position.copy(containerObj.position);
      this.scene.add(axesHelper);
      
      // Add to scene and tracking array
      this.scene.add(containerObj);
      this.containers.push(containerObj);
      return containerObj;
    });
  }

  updateItems(items = []) {
    // Clear existing items
    this.items.forEach(item => this.scene.remove(item));
    this.items = [];

    // Add new items
    items.forEach(item => {
      if (!item.position) return;

      const dimensions = item.rotation || [item.width, item.depth, item.height];
      const geometry = new THREE.BoxGeometry(
        dimensions[0] / 100,
        dimensions[1] / 100,
        dimensions[2] / 100
      );

      const color = this.getPriorityColor(item.priority);
      const material = new THREE.MeshBasicMaterial({
        color,
        transparent: true,
        opacity: 0.7,
      });

      const cube = new THREE.Mesh(geometry, material);
      
      // Check if position is an array (the new format) or an object (old format)
      if (Array.isArray(item.position)) {
        cube.position.set(
          item.position[0] / 100,
          item.position[1] / 100,
          item.position[2] / 100
        );
      } else if (item.position.startCoordinates) {
        cube.position.set(
          item.position.startCoordinates.width / 100,
          item.position.startCoordinates.depth / 100,
          item.position.startCoordinates.height / 100
        );
      }

      cube.userData = {
        itemId: item.itemId,
        priority: item.priority,
        expiry: item.expiryDate,
      };

      this.scene.add(cube);
      this.items.push(cube);

      // Add label for high priority items
      if (item.priority > 70) {
        const label = this.createLabel(item);
        cube.add(label);
      }
    });
  }

  getPriorityColor(priority) {
    const priorityColors = {
      high: 0xff0000,
      medium: 0xffa500,
      low: 0x00ff00,
    };
    
    if (priority >= 80) return priorityColors.high;
    if (priority >= 50) return priorityColors.medium;
    return priorityColors.low;
  }

  createLabel(item) {
    const canvas = document.createElement('canvas');
    canvas.width = 256;
    canvas.height = 128;
    const context = canvas.getContext('2d');
    
    // Draw label background
    context.fillStyle = 'rgba(0, 0, 0, 0.7)';
    context.fillRect(0, 0, canvas.width, canvas.height);
    
    // Draw text
    context.font = 'Bold 20px Arial';
    context.fillStyle = 'white';
    context.textAlign = 'center';
    context.fillText(item.itemId, canvas.width / 2, 30);
    context.fillText(`Priority: ${item.priority}`, canvas.width / 2, 60);
    
    const texture = new THREE.CanvasTexture(canvas);
    const material = new THREE.SpriteMaterial({ map: texture });
    const sprite = new THREE.Sprite(material);
    sprite.scale.set(1, 0.5, 1);
    sprite.position.set(0, 0, 0.6);
    return sprite;
  }

  handleResize() {
    const width = this.containerRef.clientWidth;
    const height = this.containerRef.clientHeight;
    
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
  }

  animate() {
    this.animationFrameId = requestAnimationFrame(this.animate);
    this.renderer.render(this.scene, this.camera);
  }

  cleanup() {
    // Stop animation loop
    cancelAnimationFrame(this.animationFrameId);
    
    // Remove event listeners
    window.removeEventListener('resize', this.handleResize);
    
    // Clean up Three.js resources
    if (this.renderer) {
      this.renderer.dispose();
    }
    
    // Remove DOM elements
    if (this.containerRef && this.renderer?.domElement) {
      this.containerRef.removeChild(this.renderer.domElement);
    }
  }
}
