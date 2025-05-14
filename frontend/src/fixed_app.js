document.addEventListener('DOMContentLoaded', () => {
  console.log('Space Station Cargo Management System initialized');
  
  // Initialize date display
  const currentDateDisplay = document.getElementById('currentDateDisplay');
  if (currentDateDisplay) {
    currentDateDisplay.textContent = new Date().toISOString().split('T')[0];
  }
  
  // Tab navigation
  const tabs = {
    'homeBtn': 'home-tab',
    'containersBtn': 'container-tab',
    'itemsBtn': 'items-tab',
    'searchBtn': 'search-tab',
    'wasteBtn': 'waste-tab',
    'simulationBtn': 'simulation-tab',
    'logsBtn': 'logs-tab',
    'threeDBtn': 'threeD-tab'
  };
  
  Object.keys(tabs).forEach(btnId => {
    const btn = document.getElementById(btnId);
    if (btn) {
      btn.addEventListener('click', () => {
        // Hide all tabs
        Object.values(tabs).forEach(tabId => {
          const tabElement = document.getElementById(tabId);
          if (tabElement) {
            tabElement.style.display = 'none';
          }
        });
        
        // Show selected tab
        const tabToShow = document.getElementById(tabs[btnId]);
        if (tabToShow) {
          tabToShow.style.display = 'block';
        }
        
        // Update active button
        Object.keys(tabs).forEach(id => {
          const button = document.getElementById(id);
          if (button) {
            button.classList.remove('active');
          }
        });
        btn.classList.add('active');
      });
    }
  });
  
  // Initialize container viewers
  const threeDViewer = document.getElementById('threeDViewer');
  const itemLocationViewer = document.getElementById('itemLocationViewer');
  
  let threeDViewerInstance = null;
  let itemLocationViewerInstance = null;
  
  if (threeDViewer) {
    threeDViewerInstance = new ISSContainerViewer(threeDViewer);
  }
  
  if (itemLocationViewer) {
    itemLocationViewerInstance = new ISSContainerViewer(itemLocationViewer);
  }
  
  // Data loading functions
  async function loadContainers() {
    try {
      const response = await fetch('/api/containers');
      if (response.ok) {
        const containers = await response.json();
        displayContainers(containers);
        // Remove container utilization bar function call
        return containers;
      } else {
        console.error('Failed to load containers:', response.statusText);
        return [];
      }
    } catch (error) {
      console.error('Error loading containers:', error);
      return [];
    }
  }
  
  async function loadItems() {
    try {
      const response = await fetch('/api/items');
      if (response.ok) {
        const items = await response.json();
        displayItems(items);
        return items;
      } else {
        console.error('Failed to load items:', response.statusText);
        return [];
      }
    } catch (error) {
      console.error('Error loading items:', error);
      return [];
    }
  }
  
  async function loadLogs() {
    try {
      const response = await fetch('/api/logs');
      if (response.ok) {
        const logs = await response.json();
        displayLogs(logs);
        
        // Update current date from the most recent log if available
        if (logs.length > 0 && logs[0].currentDate) {
          const currentDate = new Date(logs[0].currentDate);
          if (currentDateDisplay) {
            currentDateDisplay.textContent = currentDate.toISOString().split('T')[0];
          }
          
          const currentDateValue = document.getElementById('currentDateValue');
          if (currentDateValue) {
            currentDateValue.textContent = currentDate.toLocaleDateString('en-US', {
              weekday: 'long',
              year: 'numeric', 
              month: 'long', 
              day: 'numeric'
            });
          }
        }
        
        return logs;
      } else {
        console.error('Failed to load logs:', response.statusText);
        return [];
      }
    } catch (error) {
      console.error('Error loading logs:', error);
      return [];
    }
  }
  
  // Display functions
  function displayContainers(containers) {
    const containerGrid = document.getElementById('containerGrid');
    if (!containerGrid) return;
    
    containerGrid.innerHTML = '';
    
    if (containers.length === 0) {
      containerGrid.innerHTML = '<p class="text-center">No containers available. Import containers first.</p>';
      return;
    }
    
    containers.forEach(container => {
      const containerDiv = document.createElement('div');
      containerDiv.className = 'container-item';
      containerDiv.style.backgroundColor = getZoneColor(container.zone);
      
      const totalVolume = container.width * container.depth * container.height;
      const usagePercent = container.occupiedSpace > 0 
        ? Math.round((container.occupiedSpace / totalVolume) * 100) 
        : 0;
      
      containerDiv.innerHTML = `
        <h4>${container.containerId}</h4>
        <p>Zone: ${container.zone}</p>
        <p>${container.width}cm × ${container.depth}cm × ${container.height}cm</p>
        <div class="progress mb-2">
          <div class="progress-bar ${usagePercent > 80 ? 'bg-danger' : 'bg-success'}" 
               role="progressbar" 
               style="width: ${usagePercent}%" 
               aria-valuenow="${usagePercent}" 
               aria-valuemin="0" 
               aria-valuemax="100">
            ${usagePercent}%
          </div>
        </div>
        <p>${container.items.length} items</p>
      `;
      
      containerDiv.addEventListener('click', () => {
        // Show in 3D viewer
        if (threeDViewerInstance) {
          threeDViewerInstance.createContainers([container]);
        }
      });
      
      containerGrid.appendChild(containerDiv);
    });
  }
  
  // Container utilization bar has been removed
  function updateContainerUtilization(containers) {
    // Function disabled - container utilization bar has been removed
    return;
  }
  
  function displayItems(items) {
    const itemsTableBody = document.getElementById('itemsTableBody');
    if (!itemsTableBody) return;
    
    itemsTableBody.innerHTML = '';
    
    if (items.length === 0) {
      itemsTableBody.innerHTML = '<tr><td colspan="8" class="text-center">No items available. Import items first.</td></tr>';
      return;
    }
    
    items.forEach(item => {
      const priorityClass = item.priority > 80 ? 'priority-high' : 
                           item.priority > 50 ? 'priority-medium' : 'priority-low';
      
      const row = document.createElement('tr');
      row.innerHTML = `
        <td>${item.itemId}</td>
        <td>${item.name}</td>
        <td class="${priorityClass}">${item.priority}</td>
        <td>${item.width}cm × ${item.depth}cm × ${item.height}cm</td>
        <td>${item.mass} kg</td>
        <td>${item.expiryDate}</td>
        <td>${item.preferredZone}</td>
        <td>
          <button class="btn btn-sm btn-primary search-item-btn" data-item-id="${item.itemId}">
            Find
          </button>
        </td>
      `;
      
      // Add event listener to search button
      row.querySelector('.search-item-btn').addEventListener('click', () => {
        // Switch to search tab and search for this item
        document.getElementById('searchBtn').click();
        document.getElementById('searchInput').value = item.itemId;
        document.getElementById('searchItemBtn').click();
      });
      
      itemsTableBody.appendChild(row);
    });
  }
  
  function displayLogs(logs) {
    const systemLogs = document.getElementById('systemLogs');
    if (!systemLogs) return;
    
    systemLogs.innerHTML = '';
    
    if (logs.length === 0) {
      systemLogs.innerHTML = '<p class="text-center">No system logs available.</p>';
      return;
    }
    
    logs.forEach(log => {
      const logEntry = document.createElement('div');
      logEntry.className = 'log-entry';
      
      const timestamp = new Date(log.timestamp);
      const formattedTime = timestamp.toLocaleString();
      
      logEntry.innerHTML = `
        <span class="timestamp">[${formattedTime}]</span>
        <span class="user">${log.user}:</span>
        <span class="action">${log.action}</span>
        ${log.details ? `<div class="small text-muted mt-1">${JSON.stringify(log.details)}</div>` : ''}
      `;
      
      systemLogs.appendChild(logEntry);
    });
  }
  
  // Helper functions
  function getZoneColor(zone) {
    const colors = {
      'Crew_Quarters': 'rgba(165, 216, 255, 0.3)',
      'Sanitation_Bay': 'rgba(255, 216, 168, 0.3)',
      'Command_Center': 'rgba(216, 245, 162, 0.3)',
      'Engineering_Bay': 'rgba(248, 249, 250, 0.3)',
      'Medical_Bay': 'rgba(255, 193, 193, 0.3)',
      'Storage_Bay': 'rgba(216, 216, 255, 0.3)',
      'Life_Support': 'rgba(200, 255, 200, 0.3)',
      'Airlock': 'rgba(240, 200, 255, 0.3)',
      'Maintenance_Bay': 'rgba(255, 255, 200, 0.3)',
      'External_Storage': 'rgba(200, 200, 200, 0.3)'
    };
    
    return colors[zone] || 'rgba(200, 200, 200, 0.3)';
  }
  
  // Event handlers for file imports
  const setupFileImport = (fileInputId, importBtnId, uploadEndpoint, onSuccess) => {
    const fileInput = document.getElementById(fileInputId);
    const importBtn = document.getElementById(importBtnId);
    
    if (fileInput && importBtn) {
      importBtn.addEventListener('click', () => {
        fileInput.click();
      });
      
      fileInput.addEventListener('change', async (e) => {
        if (e.target.files.length === 0) return;
        
        const file = e.target.files[0];
        const formData = new FormData();
        formData.append('file', file);
        
        try {
          const response = await fetch(uploadEndpoint, {
            method: 'POST',
            body: formData
          });
          
          if (response.ok) {
            const result = await response.json();
            alert(`Import successful: ${result.importedCount || 'unknown'} items imported.`);
            
            if (typeof onSuccess === 'function') {
              onSuccess();
            }
          } else {
            alert(`Import failed: ${response.statusText}`);
          }
        } catch (error) {
          console.error('Import error:', error);
          alert(`Import error: ${error.message}`);
        }
      });
    }
  };
  
  // Setup all import buttons
  setupFileImport('containerFileInput', 'importContainersBtn', '/api/containers/import', loadContainers);
  setupFileImport('itemFileInput', 'importItemsBtn', '/api/items/import', loadItems);
  
  // Calculate placement button
  const calculatePlacementBtn = document.getElementById('calculatePlacementBtn');
  if (calculatePlacementBtn) {
    calculatePlacementBtn.addEventListener('click', async () => {
      try {
        // Show loading state
        calculatePlacementBtn.disabled = true;
        calculatePlacementBtn.textContent = 'Calculating...';
        
        // Get items and containers
        const itemsResponse = await fetch('/items');
        const containersResponse = await fetch('/containers');
        
        if (!itemsResponse.ok || !containersResponse.ok) {
          throw new Error('Failed to fetch data');
        }
        
        const items = await itemsResponse.json();
        const containers = await containersResponse.json();
        
        // Filter unplaced items
        const unplacedItems = items.filter(item => !item.currentLocation);
        
        if (unplacedItems.length === 0) {
          alert('No items need placement');
          return;
        }
        
        // Call placement API
        const placementResponse = await fetch('/calculate-placement', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            items: unplacedItems,
            containers: containers
          })
        });
        
        if (!placementResponse.ok) {
          throw new Error('Placement calculation failed');
        }
        
        const placementResult = await placementResponse.json();
        
        // Show results
        alert(`Placement calculated: ${placementResult.placements.length} items placed with ${placementResult.rearrangements.length} rearrangements needed.`);
        
        // Reload data
        loadItems();
        loadContainers();
      } catch (error) {
        console.error('Placement error:', error);
        alert(`Placement error: ${error.message}`);
      } finally {
        // Reset button state
        calculatePlacementBtn.disabled = false;
        calculatePlacementBtn.textContent = 'Calculate Optimal Placement';
      }
    });
  }
  
  // Search functionality
  const searchItemBtn = document.getElementById('searchItemBtn');
  const searchInput = document.getElementById('searchInput');
  
  if (searchItemBtn && searchInput) {
    searchItemBtn.addEventListener('click', async () => {
      const searchTerm = searchInput.value.trim();
      if (!searchTerm) return;
      
      try {
        // Call search API
        const searchResponse = await fetch(`/search-item?${searchTerm.match(/^\d+$/) ? 'itemId' : 'itemName'}=${encodeURIComponent(searchTerm)}`);
        
        if (!searchResponse.ok) {
          throw new Error('Search failed');
        }
        
        const searchResults = await searchResponse.json();
        displaySearchResults(searchResults);
      } catch (error) {
        console.error('Search error:', error);
        alert(`Search error: ${error.message}`);
      }
    });
    
    // Also search on Enter key
    searchInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        searchItemBtn.click();
      }
    });
  }
  
  function displaySearchResults(results) {
    const searchResultsElement = document.getElementById('searchResults');
    if (!searchResultsElement) return;
    
    searchResultsElement.innerHTML = '';
    
    if (results.length === 0) {
      searchResultsElement.innerHTML = '<p class="text-center">No items found</p>';
      return;
    }
    
    results.forEach(result => {
      const resultItem = document.createElement('button');
      resultItem.className = 'list-group-item list-group-item-action d-flex justify-content-between align-items-center';
      resultItem.innerHTML = `
        <div>
          <strong>${result.itemId}</strong>: ${result.name}
          <small class="d-block text-muted">Location: ${result.containerId || 'Not placed'}</small>
        </div>
        <span class="badge bg-primary rounded-pill">${result.retrievalSteps || 0} steps</span>
      `;
      
      resultItem.addEventListener('click', () => {
        displayItemLocation(result);
      });
      
      searchResultsElement.appendChild(resultItem);
    });
  }
  
  function displayItemLocation(itemLocation) {
    // Show the item in 3D viewer
    if (itemLocationViewerInstance) {
      // Clear previous container and items
      itemLocationViewerInstance.cleanup();
      
      // Get container data
      fetch(`/api/containers?containerId=${itemLocation.containerId}`)
        .then(response => response.json())
        .then(containers => {
          if (containers.length > 0) {
            const container = containers[0];
            
            // Create container in viewer
            itemLocationViewerInstance.createContainers([container]);
            
            // Add the item to viewer
            itemLocationViewerInstance.updateItems([{
              id: itemLocation.itemId,
              name: itemLocation.name,
              position: itemLocation.position,
              dimensions: itemLocation.rotation,
              priority: 100, // Highlight the item
              containerId: itemLocation.containerId
            }]);
          }
        })
        .catch(error => console.error('Error loading container for item location:', error));
    }
    
    // Display retrieval steps
    const retrievalStepsElement = document.getElementById('retrievalSteps');
    if (retrievalStepsElement) {
      // Get retrieval steps from API
      fetch(`/api/items/retrieve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          itemId: itemLocation.itemId
        })
      })
      .then(response => response.json())
      .then(data => {
        if (data.error) {
          retrievalStepsElement.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
          return;
        }
        
        const steps = data.retrievalSteps || [];
        
        if (steps.length === 0) {
          retrievalStepsElement.innerHTML = '<p class="text-success">This item can be retrieved directly.</p>';
          return;
        }
        
        let stepsHTML = '<ol class="list-group list-group-numbered">';
        
        steps.forEach(step => {
          stepsHTML += `
            <li class="list-group-item d-flex justify-content-between align-items-start">
              <div class="ms-2 me-auto">
                ${step.action} item ${step.itemId}
                ${step.fromContainer ? `<div class="small text-muted">From: ${step.fromContainer}</div>` : ''}
                ${step.toContainer ? `<div class="small text-muted">To: ${step.toContainer}</div>` : ''}
              </div>
            </li>
          `;
        });
        
        stepsHTML += '</ol>';
        retrievalStepsElement.innerHTML = stepsHTML;
      })
      .catch(error => {
        console.error('Error retrieving item steps:', error);
        retrievalStepsElement.innerHTML = `<div class="alert alert-danger">Error retrieving steps: ${error.message}</div>`;
      });
    }
  }
  
  // Waste management
  const identifyWasteBtn = document.getElementById('identifyWasteBtn');
  const wasteList = document.getElementById('wasteList');
  const wasteStats = document.getElementById('wasteStats');
  const wasteReturnSteps = document.getElementById('wasteReturnSteps');
  
  if (identifyWasteBtn) {
    identifyWasteBtn.addEventListener('click', async () => {
      try {
        // Show loading state
        identifyWasteBtn.disabled = true;
        identifyWasteBtn.textContent = 'Identifying...';
        
        // Call waste identification API
        const response = await fetch('/api/waste/identify');
        
        if (!response.ok) {
          throw new Error('Failed to identify waste');
        }
        
        const result = await response.json();
        
        // Display waste items
        if (wasteList) {
          if (result.wasteItems?.length > 0) {
            let wasteHTML = '<ul class="list-group">';
            
            result.wasteItems.forEach(wasteItem => {
              wasteHTML += `
                <li class="list-group-item d-flex justify-content-between align-items-center">
                  <div>
                    <strong>${wasteItem.itemId}</strong>: ${wasteItem.name}
                    <div class="small text-muted">
                      ${wasteItem.isExpired ? '<span class="badge bg-danger">Expired</span>' : ''}
                      ${wasteItem.isUsedUp ? '<span class="badge bg-warning">Used Up</span>' : ''}
                      Location: ${wasteItem.containerId || 'Not placed'}
                    </div>
                  </div>
                  <span>${wasteItem.mass} kg</span>
                </li>
              `;
            });
            
            wasteHTML += '</ul>';
            wasteList.innerHTML = wasteHTML;
          } else {
            wasteList.innerHTML = '<p class="text-center">No waste items found</p>';
          }
        }
        
        // Display waste statistics
        if (wasteStats) {
          if (result.totalMass && result.wasteItems?.length > 0) {
            wasteStats.innerHTML = `
              <div>
                <p><strong>Total waste items:</strong> ${result.wasteItems.length}</p>
                <p><strong>Total waste mass:</strong> ${result.totalMass.toFixed(2)} kg</p>
                <button id="generateReturnPlanBtn" class="btn btn-warning">Generate Return Plan</button>
              </div>
            `;
            
            // Add event listener to generate return plan button
            const generateReturnPlanBtn = document.getElementById('generateReturnPlanBtn');
            if (generateReturnPlanBtn) {
              generateReturnPlanBtn.addEventListener('click', () => generateWasteReturnPlan(result.wasteItems));
            }
          } else {
            wasteStats.innerHTML = '<p class="text-center">No waste statistics available</p>';
          }
        }
        
      } catch (error) {
        console.error('Waste identification error:', error);
        alert(`Error identifying waste: ${error.message}`);
        
        if (wasteList) {
          wasteList.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
        }
      } finally {
        // Reset button state
        identifyWasteBtn.disabled = false;
        identifyWasteBtn.textContent = 'Identify Waste Items';
      }
    });
  }
  
  async function generateWasteReturnPlan(wasteItems) {
    if (!wasteReturnSteps) return;
    
    try {
      wasteReturnSteps.innerHTML = '<p class="text-center">Generating return plan...</p>';
      
      // Call waste return plan API
      const response = await fetch('/api/waste/return-plan', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          maxWeight: 100 // Default max weight for return container
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to generate return plan');
      }
      
      const result = await response.json();
      
      if (result.steps?.length > 0) {
        let stepsHTML = '<ol class="list-group list-group-numbered">';
        
        result.steps.forEach(step => {
          stepsHTML += `
            <li class="list-group-item">
              <div>
                <strong>${step.action}</strong> ${step.itemId || ''}
                ${step.fromContainer ? `<div class="small text-muted">From: ${step.fromContainer}</div>` : ''}
                ${step.toContainer ? `<div class="small text-muted">To: ${step.toContainer}</div>` : ''}
              </div>
            </li>
          `;
        });
        
        stepsHTML += '</ol>';
        stepsHTML += `
          <div class="mt-3">
            <button id="completeUndockingBtn" class="btn btn-danger">Complete Undocking</button>
          </div>
        `;
        
        wasteReturnSteps.innerHTML = stepsHTML;
        
        // Add event listener to complete undocking button
        const completeUndockingBtn = document.getElementById('completeUndockingBtn');
        if (completeUndockingBtn) {
          completeUndockingBtn.addEventListener('click', completeUndocking);
        }
      } else {
        wasteReturnSteps.innerHTML = '<p class="text-center">No return steps generated</p>';
      }
    } catch (error) {
      console.error('Return plan error:', error);
      wasteReturnSteps.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
    }
  }
  
  async function completeUndocking() {
    try {
      // Call complete undocking API
      const response = await fetch('/api/waste/complete-undocking', {
        method: 'POST'
      });
      
      if (!response.ok) {
        throw new Error('Failed to complete undocking');
      }
      
      alert('Undocking completed. Waste items have been removed from the system.');
      
      // Refresh waste data
      identifyWasteBtn.click();
      
      // Reload items data
      loadItems();
    } catch (error) {
      console.error('Undocking error:', error);
      alert(`Error completing undocking: ${error.message}`);
    }
  }
  
  // Time simulation
  const simulateDaysBtn = document.getElementById('simulateDaysBtn');
  const daysInput = document.getElementById('daysInput');
  const simulationResults = document.getElementById('simulationResults');
  
  if (simulateDaysBtn && daysInput) {
    simulateDaysBtn.addEventListener('click', async () => {
      const days = parseInt(daysInput.value, 10);
      if (isNaN(days) || days < 1) {
        alert('Please enter a valid number of days (minimum 1)');
        return;
      }
      
      try {
        // Show loading state
        simulateDaysBtn.disabled = true;
        simulateDaysBtn.textContent = 'Simulating...';
        
        // Call simulation API
        const response = await fetch('/api/simulate/day', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            numOfDays: days
          })
        });
        
        if (!response.ok) {
          throw new Error('Simulation failed');
        }
        
        const simulationResult = await response.json();
        
        // Update displayed date
        if (simulationResult.newDate) {
          if (currentDateDisplay) {
            currentDateDisplay.textContent = simulationResult.newDate;
          }
          
          const currentDateValue = document.getElementById('currentDateValue');
          if (currentDateValue) {
            const date = new Date(simulationResult.newDate);
            currentDateValue.textContent = date.toLocaleDateString('en-US', {
              weekday: 'long',
              year: 'numeric', 
              month: 'long', 
              day: 'numeric'
            });
          }
        }
        
        // Display simulation results
        displaySimulationResults(simulationResult);
        
        // Reload data
        loadItems();
      } catch (error) {
        console.error('Simulation error:', error);
        alert(`Simulation error: ${error.message}`);
        
        if (simulationResults) {
          simulationResults.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
        }
      } finally {
        // Reset button state
        simulateDaysBtn.disabled = false;
        simulateDaysBtn.textContent = 'Simulate Time Passage';
      }
    });
  }
  
  function displaySimulationResults(results) {
    if (!simulationResults) return;
    
    if (!results) {
      simulationResults.innerHTML = '<p class="text-center">No changes occurred during simulation</p>';
      return;
    }
    
    const changes = results.changes || {};
    
    let resultsHTML = '<div class="mb-3">';
    
    // Display date change
    resultsHTML += `<p class="text-success">Simulated ${results.daysSimulated} days to ${results.newDate}</p>`;
    
    // Display expired items
    if (changes.itemsExpired?.length > 0) {
      resultsHTML += `
        <div class="alert alert-danger">
          <h5 class="alert-heading">Items Expired (${changes.itemsExpired.length})</h5>
          <ul>
            ${changes.itemsExpired.map(item => `<li>Item ID: ${item.itemId}</li>`).join('')}
          </ul>
        </div>
      `;
    }
    
    // Display used items
    if (changes.itemsUsed?.length > 0) {
      resultsHTML += `
        <div class="alert alert-warning">
          <h5 class="alert-heading">Items Used (${changes.itemsUsed.length})</h5>
          <ul>
            ${changes.itemsUsed.map(item => `<li>Item ID: ${item.itemId}</li>`).join('')}
          </ul>
        </div>
      `;
    }
    
    // Display depleted items
    if (changes.itemsDepleted?.length > 0) {
      resultsHTML += `
        <div class="alert alert-info">
          <h5 class="alert-heading">Items Depleted (${changes.itemsDepleted.length})</h5>
          <ul>
            ${changes.itemsDepleted.map(item => `<li>Item ID: ${item.itemId}</li>`).join('')}
          </ul>
        </div>
      `;
    }
    
    if (!changes.itemsExpired?.length && !changes.itemsUsed?.length && !changes.itemsDepleted?.length) {
      resultsHTML += '<p class="text-center">No significant changes occurred during simulation</p>';
    }
    
    resultsHTML += '</div>';
    simulationResults.innerHTML = resultsHTML;
  }
  
  // Home tab functionality
  function updateHomeTab(items, containers, logs) {
    const totalItemsCount = document.getElementById("totalItemsCount");
    const wasteItemsCount = document.getElementById("wasteItemsCount");
    const homeDateDisplay = document.getElementById("homeDateDisplay");
    const containerUtilizationChart = document.getElementById("containerUtilizationChart");
    const recentActivities = document.getElementById("recentActivities");

    if (items && totalItemsCount) {
      totalItemsCount.textContent = items.length;
      
      // Count waste items
      const wasteItems = items.filter(item => item.isWaste);
      if (wasteItemsCount) {
        wasteItemsCount.textContent = wasteItems.length;
      }
    }
    
    // Update current date
    if (homeDateDisplay && currentDateDisplay) {
      homeDateDisplay.textContent = currentDateDisplay.textContent;
    }
    
    // Display container utilization
    if (containerUtilizationChart && containers && containers.length > 0) {
      let utilizationHTML = "";
      
      containers.forEach(container => {
        const totalVolume = container.width * container.depth * container.height;
        const usagePercent = container.occupiedSpace > 0 
          ? Math.round((container.occupiedSpace / totalVolume) * 100) 
          : 0;
        
        utilizationHTML += `
          <div class="utilization-item">
            <span>${container.containerId}</span>
            <div class="bar-container">
              <div class="bar bg-info" style="width: ${usagePercent}%"></div>
            </div>
            <span>${usagePercent}%</span>
          </div>
        `;
      });
      
      containerUtilizationChart.innerHTML = utilizationHTML || '<p class="text-muted">No container data available</p>';
    }
    
    // Display recent activities
    if (recentActivities && logs && logs.length > 0) {
      const recentLogs = logs.slice(0, 5); // Get 5 most recent logs
      
      let logsHTML = '<div class="list-group">';
      
      recentLogs.forEach(log => {
        const timestamp = new Date(log.timestamp);
        const formattedTime = timestamp.toLocaleTimeString();
        
        logsHTML += `
          <div class="list-group-item list-group-item-action">
            <div class="d-flex w-100 justify-content-between">
              <h6 class="mb-1">${log.action}</h6>
              <small>${formattedTime}</small>
            </div>
            <small>User: ${log.user}</small>
          </div>
        `;
      });
      
      logsHTML += '</div>';
      recentActivities.innerHTML = logsHTML;
    }
  }

  // Set up quick action buttons
  const quickPlacementBtn = document.getElementById("quickPlacementBtn");
  const quickSearchBtn = document.getElementById("quickSearchBtn");
  const quickWasteBtn = document.getElementById("quickWasteBtn");

  if (quickPlacementBtn) {
    quickPlacementBtn.addEventListener("click", () => {
      document.getElementById("itemsBtn").click();
      setTimeout(() => {
        const placementBtn = document.getElementById("calculatePlacementBtn");
        if (placementBtn) placementBtn.click();
      }, 100);
    });
  }

  if (quickSearchBtn) {
    quickSearchBtn.addEventListener("click", () => {
      document.getElementById("searchBtn").click();
      setTimeout(() => {
        const searchInput = document.getElementById("searchInput");
        if (searchInput) searchInput.focus();
      }, 100);
    });
  }

  if (quickWasteBtn) {
    quickWasteBtn.addEventListener("click", () => {
      document.getElementById("wasteBtn").click();
      setTimeout(() => {
        const wasteBtn = document.getElementById("identifyWasteBtn");
        if (wasteBtn) wasteBtn.click();
      }, 100);
    });
  }

  // Update home tab when data is loaded
  const originalLoadContainers = loadContainers;
  loadContainers = async function() {
    const containers = await originalLoadContainers();
    updateHomeTab(null, containers, null);
    return containers;
  };

  const originalLoadItems = loadItems;
  loadItems = async function() {
    const items = await originalLoadItems();
    updateHomeTab(items, null, null);
    return items;
  };

  const originalLoadLogs = loadLogs;
  loadLogs = async function() {
    const logs = await originalLoadLogs();
    updateHomeTab(null, null, logs);
    return logs;
  };
  
  // Initial data load
  loadContainers();
  loadItems();
  loadLogs();
});