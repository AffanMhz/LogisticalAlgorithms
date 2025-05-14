// main.js - Space Station Cargo Management System

document.addEventListener('DOMContentLoaded', () => {
    // Initialize application
    initApplication();
});

// Global variables
let containersData = [];
let itemsData = [];
let containerViewer = null;

// API endpoint base URL
const API_BASE_URL = '/api';

async function initApplication() {
    setupEventListeners();
    await loadContainers();
    await loadItems();
    initVisualization();
    updateStats();
}

function setupEventListeners() {
    // Sidebar navigation buttons
    document.getElementById('homeBtn').addEventListener('click', function() {
        showTab('home-tab');
        setActiveButton(this);
    });
    
    document.getElementById('containersBtn').addEventListener('click', function() {
        showTab('container-tab');
        setActiveButton(this);
    });
    
    document.getElementById('itemsBtn').addEventListener('click', function() {
        showTab('items-tab');
        setActiveButton(this);
    });
    
    document.getElementById('searchBtn').addEventListener('click', function() {
        showTab('search-tab');
        setActiveButton(this);
    });
    
    document.getElementById('wasteBtn').addEventListener('click', function() {
        showTab('waste-tab');
        setActiveButton(this);
        // Populate undock container select
        populateUndockContainers();
    });
    
    document.getElementById('simulationBtn').addEventListener('click', function() {
        showTab('simulation-tab');
        setActiveButton(this);
    });
    
    document.getElementById('logsBtn').addEventListener('click', function() {
        showTab('logs-tab');
        setActiveButton(this);
        loadLogs(); // Load logs when tab is selected
    });
    
    document.getElementById('threeDBtn').addEventListener('click', function() {
        showTab('threeD-tab');
        setActiveButton(this);
        if (containerViewer) {
            containerViewer.handleResize(); // Ensure 3D view is properly sized
        }
    });
    
    // Quick action buttons on home tab
    const quickPlacementBtn = document.getElementById('quickPlacementBtn');
    if (quickPlacementBtn) {
        quickPlacementBtn.addEventListener('click', function() {
            document.getElementById('itemsBtn').click();
            // Scroll to placement section
            setTimeout(() => {
                const placementBtn = document.getElementById('calculatePlacementBtn');
                if (placementBtn) placementBtn.scrollIntoView({ behavior: 'smooth' });
            }, 100);
        });
    }
    
    const quickSearchBtn = document.getElementById('quickSearchBtn');
    if (quickSearchBtn) {
        quickSearchBtn.addEventListener('click', function() {
            document.getElementById('searchBtn').click();
        });
    }
    
    const quickWasteBtn = document.getElementById('quickWasteBtn');
    if (quickWasteBtn) {
        quickWasteBtn.addEventListener('click', function() {
            document.getElementById('wasteBtn').click();
        });
    }
    
    // Search functionality
    const searchItemBtn = document.getElementById('searchItemBtn');
    if (searchItemBtn) {
        searchItemBtn.addEventListener('click', handleSearchSubmit);
    }
    
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                handleSearchSubmit();
            }
        });
    }
    
    // Calculate placement button
    const calculatePlacementBtn = document.getElementById('calculatePlacementBtn');
    if (calculatePlacementBtn) {
        calculatePlacementBtn.addEventListener('click', handlePlacementCalculation);
    }
    
    // Import buttons
    const importContainersBtn = document.getElementById('importContainersBtn');
    if (importContainersBtn) {
        importContainersBtn.addEventListener('click', handleImportContainers);
    }
    
    const importItemsBtn = document.getElementById('importItemsBtn');
    if (importItemsBtn) {
        importItemsBtn.addEventListener('click', handleImportItems);
    }
    
    // Waste management buttons
    const identifyWasteBtn = document.getElementById('identifyWasteBtn');
    if (identifyWasteBtn) {
        identifyWasteBtn.addEventListener('click', handleIdentifyWaste);
    }
    
    const generateReturnPlanBtn = document.getElementById('generateReturnPlanBtn');
    if (generateReturnPlanBtn) {
        generateReturnPlanBtn.addEventListener('click', handleGenerateReturnPlan);
    }
    
    // Simulation buttons
    const simulateDaysBtn = document.getElementById('simulateDaysBtn');
    if (simulateDaysBtn) {
        simulateDaysBtn.addEventListener('click', handleSimulateDays);
    }
    
    // Logs filter form
    const logFilterForm = document.getElementById('logFilterForm');
    if (logFilterForm) {
        logFilterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            applyLogFilters();
        });
    }
    
    // Log refresh button
    const refreshLogsBtn = document.getElementById('refreshLogsBtn');
    if (refreshLogsBtn) {
        refreshLogsBtn.addEventListener('click', function() {
            loadLogs();
        });
    }
}

// Helper function to show a specific tab
function showTab(tabId) {
    // Hide all tabs
    document.querySelectorAll('[id$="-tab"]').forEach(tab => {
        tab.style.display = 'none';
    });
    
    // Show the selected tab
    const selectedTab = document.getElementById(tabId);
    if (selectedTab) {
        selectedTab.style.display = 'block';
    }
}

// Helper function to set active button in sidebar
function setActiveButton(button) {
    // Remove active class from all buttons
    document.querySelectorAll('.sidebar button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Add active class to the clicked button
    button.classList.add('active');
}

async function loadContainers() {
    try {
        const response = await fetch(`${API_BASE_URL}/containers`);
        if (!response.ok) {
            throw new Error('Failed to load containers');
        }
        containersData = await response.json();
        updateContainersList();
    } catch (error) {
        console.error('Error loading containers:', error);
        showAlert('error', 'Failed to load containers. Please try again later.');
    }
}

async function loadItems() {
    try {
        const response = await fetch(`${API_BASE_URL}/items`);
        if (!response.ok) {
            throw new Error('Failed to load items');
        }
        itemsData = await response.json();
        updateItemsList();
    } catch (error) {
        console.error('Error loading items:', error);
        showAlert('error', 'Failed to load items. Please try again later.');
    }
}

async function loadLogs() {
    try {
        const response = await fetch(`${API_BASE_URL}/logs`);
        if (!response.ok) {
            throw new Error('Failed to load logs');
        }
        const logsData = await response.json();
        updateLogsList(logsData);
    } catch (error) {
        console.error('Error loading logs:', error);
        showAlert('error', 'Failed to load logs. Please try again later.');
    }
}

function updateContainersList() {
    const containersList = document.getElementById('containerGrid');
    
    if (containersList) {
        containersList.innerHTML = '';
        containersData.forEach(container => {
            const containerDiv = document.createElement('div');
            containerDiv.className = 'container-item';
            const totalVolume = (container.width * container.depth * container.height / 1000).toFixed(2);
            const occupiedVolume = (container.occupiedSpace || 0).toFixed(2);
            const percentage = (occupiedVolume / totalVolume * 100).toFixed(1);
            
            containerDiv.innerHTML = `
                <h5>${container.containerId}</h5>
                <div class="badge bg-secondary mb-2">${container.zone}</div>
                <p>${container.width.toFixed(1)} x ${container.depth.toFixed(1)} x ${container.height.toFixed(1)} cm</p>
                <div class="progress mb-2">
                    <div class="progress-bar bg-info" role="progressbar" style="width: ${percentage}%">
                        ${percentage}%
                    </div>
                </div>
                <small>${occupiedVolume}/${totalVolume} L used</small>
                <div class="mt-2">
                    <span class="badge bg-primary">${container.items ? container.items.length : 0} items</span>
                </div>
            `;
            containersList.appendChild(containerDiv);
        });
    }
}

function updateItemsList() {
    const itemsTableBody = document.getElementById('itemsTableBody');
    
    if (itemsTableBody) {
        itemsTableBody.innerHTML = '';
        itemsData.forEach(item => {
            const row = document.createElement('tr');
            const isExpired = item.isWaste || (item.expiryDate !== 'N/A' && new Date(item.expiryDate) < new Date());
            
            // Set class for priority
            let priorityClass = '';
            if (item.priority >= 80) {
                priorityClass = 'text-danger';
            } else if (item.priority >= 50) {
                priorityClass = 'text-warning';
            } else {
                priorityClass = 'text-success';
            }
            
            row.innerHTML = `
                <td>${item.itemId}</td>
                <td>${item.name}</td>
                <td class="${priorityClass}">${item.priority}</td>
                <td>${item.width.toFixed(1)} × ${item.depth.toFixed(1)} × ${item.height.toFixed(1)} cm</td>
                <td>${item.mass.toFixed(2)} kg</td>
                <td>${item.expiryDate}</td>
                <td>${item.preferredZone}</td>
                <td>
                    <button class="btn btn-sm btn-outline-info view-item-btn" data-item-id="${item.itemId}">
                        View
                    </button>
                </td>
            `;
            
            itemsTableBody.appendChild(row);
        });
        
        // Add event listeners to view buttons
        document.querySelectorAll('.view-item-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const itemId = btn.getAttribute('data-item-id');
                showItemDetails(itemId);
            });
        });
    }
}

function updateLogsList(logs) {
    const logsTableBody = document.getElementById('logsTableBody');
    
    if (logsTableBody) {
        logsTableBody.innerHTML = '';
        
        if (!logs || logs.length === 0) {
            logsTableBody.innerHTML = '<tr><td colspan="5" class="text-center">No logs found</td></tr>';
            return;
        }
        
        logs.forEach(log => {
            const row = document.createElement('tr');
            const timestamp = new Date(log.timestamp).toLocaleString();
            
            row.innerHTML = `
                <td>${timestamp}</td>
                <td>${log.user_id || 'system'}</td>
                <td>${log.action_type}</td>
                <td>${log.item_id || '-'}</td>
                <td>${formatLogDetails(log.details)}</td>
            `;
            
            logsTableBody.appendChild(row);
        });
    }
}

function formatLogDetails(details) {
    if (!details) return '-';
    
    let result = '';
    for (const [key, value] of Object.entries(details)) {
        if (typeof value === 'object') {
            result += `<strong>${key}:</strong> ${JSON.stringify(value)}<br>`;
        } else {
            result += `<strong>${key}:</strong> ${value}<br>`;
        }
    }
    
    return result;
}

function updateStats() {
    // Update date display
    const currentDateDisplay = document.getElementById('currentDateDisplay');
    const homeDateDisplay = document.getElementById('homeDateDisplay');
    
    if (currentDateDisplay) {
        currentDateDisplay.textContent = new Date().toISOString().split('T')[0];
    }
    
    if (homeDateDisplay) {
        homeDateDisplay.textContent = new Date().toISOString().split('T')[0];
    }
    
    // Update item counts
    const totalItemsCount = document.getElementById('totalItemsCount');
    if (totalItemsCount) {
        totalItemsCount.textContent = itemsData.length;
    }
    
    // Count waste items
    const wasteItemsCount = document.getElementById('wasteItemsCount');
    if (wasteItemsCount) {
        const wasteCount = itemsData.filter(item => item.isWaste).length;
        wasteItemsCount.textContent = wasteCount;
    }
    
    // Update container utilization chart
    updateContainerUtilization();
    
    // Update recent activities
    loadRecentActivities();
}

function updateContainerUtilization() {
    const containerUtilizationChart = document.getElementById('containerUtilizationChart');
    
    if (containerUtilizationChart && containersData.length > 0) {
        // Sort containers by utilization percentage (descending)
        const sortedContainers = [...containersData].sort((a, b) => {
            const utilizationA = (a.occupiedSpace || 0) / (a.width * a.depth * a.height) * 100;
            const utilizationB = (b.occupiedSpace || 0) / (b.width * b.depth * b.height) * 100;
            return utilizationB - utilizationA;
        });
        
        // Take top 5 containers for the chart
        const topContainers = sortedContainers.slice(0, 5);
        
        let html = '';
        topContainers.forEach(container => {
            const totalVolume = container.width * container.depth * container.height / 1000;
            const occupiedVolume = container.occupiedSpace || 0;
            const percentage = (occupiedVolume / totalVolume * 100).toFixed(1);
            
            // Determine color based on utilization
            let barColor = 'bg-success';
            if (percentage > 80) {
                barColor = 'bg-danger';
            } else if (percentage > 60) {
                barColor = 'bg-warning';
            }
            
            html += `
                <div class="utilization-item">
                    <span>${container.containerId}</span>
                    <div class="bar-container">
                        <div class="bar ${barColor}" style="width: ${percentage}%"></div>
                    </div>
                    <span>${percentage}%</span>
                </div>
            `;
        });
        
        containerUtilizationChart.innerHTML = html;
    }
}

async function loadRecentActivities() {
    const recentActivities = document.getElementById('recentActivities');
    
    if (recentActivities) {
        try {
            const response = await fetch(`${API_BASE_URL}/logs?limit=5`);
            if (!response.ok) {
                throw new Error('Failed to load recent activities');
            }
            
            const logs = await response.json();
            
            if (!logs || logs.length === 0) {
                recentActivities.innerHTML = '<p class="text-muted">No recent activities found</p>';
                return;
            }
            
            let html = '<ul class="list-group">';
            logs.forEach(log => {
                const timestamp = new Date(log.timestamp).toLocaleString();
                let icon = '📝';
                
                switch (log.action_type) {
                    case 'placement':
                    case 'calculate_placement':
                        icon = '📥';
                        break;
                    case 'retrieval':
                    case 'retrieve_item':
                    case 'search_item':
                        icon = '🔍';
                        break;
                    case 'simulation':
                    case 'simulate_day':
                        icon = '⏱️';
                        break;
                    case 'waste':
                    case 'identify_waste':
                    case 'waste_return_plan':
                        icon = '♻️';
                        break;
                }
                
                html += `
                    <li class="list-group-item bg-dark text-light">
                        <div class="d-flex justify-content-between">
                            <span>${icon} ${log.action_type}</span>
                            <small>${timestamp}</small>
                        </div>
                        ${log.item_id ? `<small class="text-info">Item: ${log.item_id}</small>` : ''}
                    </li>
                `;
            });
            html += '</ul>';
            
            recentActivities.innerHTML = html;
            
        } catch (error) {
            console.error('Error loading recent activities:', error);
            recentActivities.innerHTML = '<p class="text-danger">Failed to load recent activities</p>';
        }
    }
}

function initVisualization() {
    const threeDViewer = document.getElementById('threeDViewer');
    if (threeDViewer && containersData.length > 0) {
        try {
            containerViewer = new ISSContainerViewer(threeDViewer, containersData);
            
            // Filter items that have a current location
            const placedItems = itemsData.filter(item => item.currentLocation);
            if (placedItems.length > 0) {
                containerViewer.updateItems(placedItems);
            }
            
            // Update container filter select
            updateContainerFilterSelect();
        } catch (error) {
            console.error('Error initializing 3D visualization:', error);
            threeDViewer.innerHTML = '<div class="alert alert-danger">Failed to load 3D visualization</div>';
        }
    }
}

function updateContainerFilterSelect() {
    const containerFilterSelect = document.getElementById('containerFilterSelect');
    if (containerFilterSelect && containersData.length > 0) {
        // Clear existing options
        containerFilterSelect.innerHTML = '<option value="">All Zones</option>';
        
        // Get unique zones
        const zones = [...new Set(containersData.map(container => container.zone))];
        
        // Add options for each zone
        zones.forEach(zone => {
            const option = document.createElement('option');
            option.value = zone;
            option.textContent = zone;
            containerFilterSelect.appendChild(option);
        });
        
        // Add event listener for filter changes
        containerFilterSelect.addEventListener('change', function() {
            filterContainersByZone(this.value);
        });
    }
}

function filterContainersByZone(zone) {
    if (!containerViewer) return;
    
    if (!zone) {
        // Show all containers
        containerViewer.createContainers(containersData);
    } else {
        // Filter containers by zone
        const filteredContainers = containersData.filter(container => container.zone === zone);
        containerViewer.createContainers(filteredContainers);
    }
    
    // Update items
    const placedItems = itemsData.filter(item => item.currentLocation);
    if (placedItems.length > 0) {
        containerViewer.updateItems(placedItems);
    }
}

async function handleSearchSubmit() {
    const searchInput = document.getElementById('searchInput');
    const searchQuery = searchInput ? searchInput.value.trim() : '';
    
    if (!searchQuery) {
        showAlert('warning', 'Please enter an item ID or name to search for');
        return;
    }
    
    const searchResults = document.getElementById('searchResults');
    if (searchResults) {
        searchResults.innerHTML = '<p class="text-center"><div class="spinner-border text-primary" role="status"></div></p>';
    }
    
    try {
        // Determine if the search query is an item ID or name
        const isItemId = /^[0-9]+$/.test(searchQuery);
        const searchParams = new URLSearchParams();
        
        if (isItemId) {
            searchParams.append('itemId', searchQuery);
        } else {
            searchParams.append('itemName', searchQuery);
        }
        
        const response = await fetch(`${API_BASE_URL}/items/search?${searchParams.toString()}`);
        if (!response.ok) {
            throw new Error('Search failed');
        }
        
        const result = await response.json();
        
        if (!result.items || result.items.length === 0) {
            searchResults.innerHTML = '<p class="text-muted">No items found matching your search</p>';
            return;
        }
        
        // Display search results
        displaySearchResults(result.items);
        
    } catch (error) {
        console.error('Error searching for items:', error);
        showAlert('error', 'Failed to search for items. Please try again later.');
        
        if (searchResults) {
            searchResults.innerHTML = '<p class="text-danger">Search failed. Please try again.</p>';
        }
    }
}

function displaySearchResults(items) {
    const searchResults = document.getElementById('searchResults');
    if (!searchResults) return;
    
    searchResults.innerHTML = '';
    
    items.forEach(item => {
        const resultItem = document.createElement('button');
        resultItem.className = 'list-group-item list-group-item-action';
        resultItem.setAttribute('data-item-id', item.itemId);
        
        // Determine priority class
        let priorityBadgeClass = 'bg-success';
        if (item.priority >= 80) {
            priorityBadgeClass = 'bg-danger';
        } else if (item.priority >= 50) {
            priorityBadgeClass = 'bg-warning';
        }
        
        resultItem.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <h6 class="mb-1">${item.name}</h6>
                    <small class="text-muted">ID: ${item.itemId}</small>
                </div>
                <span class="badge ${priorityBadgeClass}">Priority: ${item.priority}</span>
            </div>
        `;
        
        // Add event listener to load item details when clicked
        resultItem.addEventListener('click', function() {
            // Get item ID from data attribute
            const itemId = this.getAttribute('data-item-id');
            
            // Set all items to inactive
            document.querySelectorAll('#searchResults .list-group-item').forEach(item => {
                item.classList.remove('active');
            });
            
            // Set this item as active
            this.classList.add('active');
            
            // Retrieve the item details
            retrieveItemDetails(itemId);
        });
        
        searchResults.appendChild(resultItem);
    });
}

async function retrieveItemDetails(itemId) {
    const retrievalSteps = document.getElementById('retrievalSteps');
    const itemLocationViewer = document.getElementById('itemLocationViewer');
    
    if (retrievalSteps) {
        retrievalSteps.innerHTML = '<p class="text-center"><div class="spinner-border text-primary" role="status"></div></p>';
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/items/retrieve`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                itemId: itemId,
                userId: "system"
            })
        });
        
        if (!response.ok) {
            throw new Error("Failed to retrieve item details");
        }
        
        const result = await response.json();
                userId: 'system'
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to retrieve item details');
        }
        
        const result = await response.json();
        
        if (!result.location) {
            retrievalSteps.innerHTML = '<p class="text-danger">Item location information is not available</p>';
            return;
        }
        
        // Display item location
        displayItemLocation(result.location, itemLocationViewer);
        
        // Display retrieval steps
        displayRetrievalSteps(result.steps, retrievalSteps);
        
    } catch (error) {
        console.error('Error retrieving item details:', error);
        showAlert('error', 'Failed to retrieve item details. Please try again later.');
        
        if (retrievalSteps) {
            retrievalSteps.innerHTML = '<p class="text-danger">Failed to retrieve item details. Please try again.</p>';
        }
    }
}

function displayItemLocation(location, containerElement) {
    if (!containerElement) return;
    
    try {
        // Clear existing visualization
        while (containerElement.firstChild) {
            containerElement.removeChild(containerElement.firstChild);
        }
        
        // Create a mini version of container viewer for just this container
        const container = containersData.find(c => c.containerId === location.containerId);
        if (!container) {
            containerElement.innerHTML = '<p class="text-danger">Container information not available</p>';
            return;
        }
        
        // Initialize 3D viewer with this container
        const miniViewer = new ISSContainerViewer(containerElement, [container]);
        
        // Add the item to the visualization
        const item = itemsData.find(i => i.itemId === location.itemId);
        if (item && item.currentLocation) {
            miniViewer.updateItems([item]);
        }
        
    } catch (error) {
        console.error('Error displaying item location:', error);
        containerElement.innerHTML = '<p class="text-danger">Failed to display item location</p>';
    }
}

function displayRetrievalSteps(steps, containerElement) {
    if (!containerElement) return;
    
    if (!steps || steps.length === 0) {
        containerElement.innerHTML = '<p class="text-info">This item is directly accessible. No additional steps required.</p>';
        return;
    }
    
    let html = '<ol class="list-group list-group-numbered">';
    steps.forEach(step => {
        html += `
            <li class="list-group-item d-flex justify-content-between align-items-start">
                <div class="ms-2 me-auto">
                    <div class="fw-bold">${step.action}</div>
                    ${step.itemId ? `Item: ${step.itemId}` : ''}
                    ${step.direction ? `<br>Direction: ${step.direction}` : ''}
                </div>
            </li>
        `;
    });
    html += '</ol>';
    
    containerElement.innerHTML = html;
}

async function handlePlacementCalculation() {
    try {
        // Show loading indicator
        const calculateBtn = document.getElementById("calculatePlacementBtn");
        if (calculateBtn) {
            calculateBtn.disabled = true;
            calculateBtn.innerHTML = "<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Calculating...";
        }
        
        const response = await fetch(`${API_BASE_URL}/placement/recommend`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                items: itemsData.filter(item => !item.currentLocation && !item.isWaste).map(item => item.itemId)
            })
        });
        
        // Reset button state
        if (calculateBtn) {
            calculateBtn.disabled = false;
            calculateBtn.innerHTML = "Calculate Optimal Placement";
        }
        
        if (!response.ok) {
            throw new Error("Failed to calculate placement");
        }
                items: itemsData.filter(item => !item.currentLocation && !item.isWaste).map(item => item.itemId)
            })
        });
        
        // Reset button state
        if (calculateBtn) {
            calculateBtn.disabled = false;
            calculateBtn.innerHTML = 'Calculate Optimal Placement';
        }
        
        if (!response.ok) {
            throw new Error('Failed to calculate placement');
        }
        
        const result = await response.json();
        
        if (!result.placements || result.placements.length === 0) {
            showAlert('warning', 'No items to place or no suitable containers available');
            return;
        }
        
        // Display placement results
        displayPlacementResults(result);
        
        // Refresh data
        await loadItems();
        await loadContainers();
        updateStats();
        
    } catch (error) {
        console.error('Error calculating placement:', error);
        showAlert('error', 'Failed to calculate item placement. Please try again later.');
    }
}

function displayPlacementResults(result) {
    const placements = result.placements || [];
    const rearrangements = result.rearrangements || [];
    
    // Create modal with results
    const modalHtml = `
        <div class="modal fade" id="placementResultsModal" tabindex="-1" aria-labelledby="placementResultsModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="placementResultsModalLabel">Placement Results</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="alert alert-success">
                            Successfully placed ${placements.length} items
                            ${rearrangements.length > 0 ? ` (with ${rearrangements.length} rearrangements)` : ''}
                        </div>
                        
                        <h6>Placement Details</h6>
                        <div class="table-responsive">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>Item ID</th>
                                        <th>Container</th>
                                        <th>Position</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${placements.map(p => `
                                        <tr>
                                            <td>${p.itemId}</td>
                                            <td>${p.containerId}</td>
                                            <td>
                                                ${p.position ? `
                                                    Start: (${p.position.startCoordinates.width}, ${p.position.startCoordinates.depth}, ${p.position.startCoordinates.height})
                                                    <br>
                                                    End: (${p.position.endCoordinates.width}, ${p.position.endCoordinates.depth}, ${p.position.endCoordinates.height})
                                                ` : 'N/A'}
                                            </td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                        
                        ${rearrangements.length > 0 ? `
                            <h6 class="mt-4">Rearrangements</h6>
                            <div class="table-responsive">
                                <table class="table table-striped">
                                    <thead>
                                        <tr>
                                            <th>Item ID</th>
                                            <th>From Container</th>
                                            <th>To Container</th>
                                            <th>New Position</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${rearrangements.map(r => `
                                            <tr>
                                                <td>${r.itemId}</td>
                                                <td>${r.fromContainerId}</td>
                                                <td>${r.toContainerId}</td>
                                                <td>
                                                    ${r.newPosition ? `
                                                        Start: (${r.newPosition.startCoordinates.width}, ${r.newPosition.startCoordinates.depth}, ${r.newPosition.startCoordinates.height})
                                                        <br>
                                                        End: (${r.newPosition.endCoordinates.width}, ${r.newPosition.endCoordinates.depth}, ${r.newPosition.endCoordinates.height})
                                                    ` : 'N/A'}
                                                </td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                        ` : ''}
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        <button type="button" class="btn btn-primary" id="view3DPlacementBtn">View in 3D</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove any existing modal
    const existingModal = document.getElementById('placementResultsModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to DOM
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show the modal
    const modal = new bootstrap.Modal(document.getElementById('placementResultsModal'));
    modal.show();
    
    // Add event listener for 3D view button
    const view3DBtn = document.getElementById('view3DPlacementBtn');
    if (view3DBtn) {
        view3DBtn.addEventListener('click', function() {
            modal.hide();
            document.getElementById('threeDBtn').click();
        });
    }
}

function showAlert(type, message) {
    // Create toast notification
    const toastId = 'toast-' + Date.now();
    const toastHTML = `
        <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header bg-${type === 'error' ? 'danger' : type === 'warning' ? 'warning' : 'info'} text-white">
                <strong class="me-auto">${type === 'error' ? 'Error' : type === 'warning' ? 'Warning' : 'Info'}</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    // Check if toast container exists, if not create it
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Add toast to container
    toastContainer.insertAdjacentHTML('beforeend', toastHTML);
    
    // Initialize and show the toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { autohide: true, delay: 5000 });
    toast.show();
    
    // Log to console as well
    if (type === 'error') {
        console.error(message);
    } else if (type === 'warning') {
        console.warn(message);
    } else {
        console.log(message);
    }
}

async function handleImportContainers() {
    const fileInput = document.getElementById('containerFileInput');
    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        showAlert('warning', 'Please select a CSV file to import');
        return;
    }
    
    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch(`${API_BASE_URL}/containers/import`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Container import failed');
        }
        
        const result = await response.json();
        
        showAlert('info', `Successfully imported ${result.count} containers`);
        
        // Refresh data
        await loadContainers();
        updateStats();
        
        // Reset file input
        fileInput.value = '';
        
    } catch (error) {
        console.error('Error importing containers:', error);
        showAlert('error', 'Failed to import containers. Please check file format and try again.');
    }
}

async function handleImportItems() {
    const fileInput = document.getElementById('itemFileInput');
    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        showAlert('warning', 'Please select a CSV file to import');
        return;
    }
    
    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch(`${API_BASE_URL}/items/import`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Item import failed');
        }
        
        const result = await response.json();
        
        showAlert('info', `Successfully imported ${result.count} items`);
        
        // Refresh data
        await loadItems();
        updateStats();
        
        // Reset file input
        fileInput.value = '';
        
    } catch (error) {
        console.error('Error importing items:', error);
        showAlert('error', 'Failed to import items. Please check file format and try again.');
    }
}

// Function to populate the undock container select
function populateUndockContainers() {
    const undockContainerSelect = document.getElementById('undockContainerSelect');
    if (undockContainerSelect && containersData.length > 0) {
        // Clear existing options
        undockContainerSelect.innerHTML = '<option value="">Select return container</option>';
        
        // Add options for each container
        containersData.forEach(container => {
            const option = document.createElement('option');
            option.value = container.containerId;
            option.textContent = `${container.containerId} (${container.zone})`;
            undockContainerSelect.appendChild(option);
        });
    }
}

// Handle waste identification
async function handleIdentifyWaste() {
    const wasteResults = document.getElementById('wasteResults');
    
    if (wasteResults) {
        wasteResults.innerHTML = '<div class="text-center"><div class="spinner-border text-warning" role="status"></div></div>';
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/waste/identify`);
        if (!response.ok) {
            throw new Error('Failed to identify waste items');
        }
        
        const result = await response.json();
        
        if (!result.wasteItems || result.wasteItems.length === 0) {
            wasteResults.innerHTML = '<div class="alert alert-info">No waste items identified at this time.</div>';
            return;
        }
        
        // Display waste items
        displayWasteItems(result.wasteItems);
        
        // Refresh data
        await loadItems();
        updateStats();
        
    } catch (error) {
        console.error('Error identifying waste:', error);
        showAlert('error', 'Failed to identify waste items. Please try again later.');
        
        if (wasteResults) {
            wasteResults.innerHTML = '<div class="alert alert-danger">Failed to identify waste items.</div>';
        }
    }
}

// Display waste items
function displayWasteItems(wasteItems) {
    const wasteResults = document.getElementById('wasteResults');
    if (!wasteResults) return;
    
    let html = `
        <div class="alert alert-warning">
            <h5>Waste Items Identified: ${wasteItems.length}</h5>
            <p>These items have expired or reached their usage limit and should be returned to Earth.</p>
        </div>
        
        <div class="table-responsive">
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>Item ID</th>
                        <th>Name</th>
                        <th>Reason</th>
                        <th>Location</th>
                        <th>Mass</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    wasteItems.forEach(item => {
        html += `
            <tr>
                <td>${item.itemId}</td>
                <td>${item.name}</td>
                <td>${item.reason || 'Marked as waste'}</td>
                <td>${item.containerId || 'Not placed'}</td>
                <td>${item.mass ? item.mass.toFixed(2) + ' kg' : 'N/A'}</td>
            </tr>
        `;
    });
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    wasteResults.innerHTML = html;
}

// Handle return plan generation
async function handleGenerateReturnPlan() {
    const wasteResults = document.getElementById('wasteResults');
    const undockContainerId = document.getElementById('undockContainerSelect').value;
    const maxWeight = document.getElementById('maxWeightInput').value;
    
    if (!undockContainerId) {
        showAlert('warning', 'Please select a return container');
        return;
    }
    
    if (!maxWeight || maxWeight <= 0) {
        showAlert('warning', 'Please enter a valid maximum weight');
        return;
    }
    
    if (wasteResults) {
        wasteResults.innerHTML = '<div class="text-center"><div class="spinner-border text-info" role="status"></div></div>';
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/waste/return-plan`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                undockingContainerId: undockContainerId,
                maxWeight: parseFloat(maxWeight)
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to generate return plan');
        }
        
        const result = await response.json();
        
        if (!result.returnItems || result.returnItems.length === 0) {
            wasteResults.innerHTML = '<div class="alert alert-info">No waste items to return at this time.</div>';
            return;
        }
        
        // Display return plan
        displayReturnPlan(result, undockContainerId);
        
    } catch (error) {
        console.error('Error generating return plan:', error);
        showAlert('error', 'Failed to generate return plan. Please try again later.');
        
        if (wasteResults) {
            wasteResults.innerHTML = '<div class="alert alert-danger">Failed to generate return plan.</div>';
        }
    }
}

// Display return plan
function displayReturnPlan(result, containerId) {
    const wasteResults = document.getElementById('wasteResults');
    if (!wasteResults) return;
    
    const returnItems = result.returnItems || [];
    const remainingItems = result.remainingWaste || [];
    const totalMass = returnItems.reduce((sum, item) => sum + (item.mass || 0), 0).toFixed(2);
    const totalItems = returnItems.length;
    
    let html = `
        <div class="alert alert-success">
            <h5>Return Plan Generated</h5>
            <p>Container: ${containerId} | Total Items: ${totalItems} | Total Mass: ${totalMass} kg</p>
        </div>
        
        <div class="card mb-4">
            <div class="card-header">
                Items to Return
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>Item ID</th>
                                <th>Name</th>
                                <th>Mass</th>
                                <th>Current Location</th>
                            </tr>
                        </thead>
                        <tbody>
    `;
    
    returnItems.forEach(item => {
        html += `
            <tr>
                <td>${item.itemId}</td>
                <td>${item.name}</td>
                <td>${item.mass ? item.mass.toFixed(2) + ' kg' : 'N/A'}</td>
                <td>${item.currentLocation ? item.currentLocation.containerId : 'Not placed'}</td>
            </tr>
        `;
    });
    
    html += `
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;
    
    if (remainingItems.length > 0) {
        html += `
            <div class="card">
                <div class="card-header">
                    Remaining Waste Items (${remainingItems.length})
                </div>
                <div class="card-body">
                    <p class="card-text">These items could not be included in the current return plan due to weight constraints.</p>
                    <div class="table-responsive">
                        <table class="table table-striped">
                            <thead>
                                <tr>
                                    <th>Item ID</th>
                                    <th>Name</th>
                                    <th>Mass</th>
                                </tr>
                            </thead>
                            <tbody>
        `;
        
        remainingItems.forEach(item => {
            html += `
                <tr>
                    <td>${item.itemId}</td>
                    <td>${item.name}</td>
                    <td>${item.mass ? item.mass.toFixed(2) + ' kg' : 'N/A'}</td>
                </tr>
            `;
        });
        
        html += `
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
    }
    
    html += `
        <div class="mt-4">
            <button id="completeUndockingBtn" class="btn btn-primary">Complete Undocking</button>
            <button id="cancelUndockingBtn" class="btn btn-outline-secondary">Cancel</button>
        </div>
    `;
    
    wasteResults.innerHTML = html;
    
    // Add event listener for complete undocking button
    document.getElementById('completeUndockingBtn').addEventListener('click', () => {
        handleCompleteUndocking(containerId, returnItems);
    });
    
    // Add event listener for cancel button
    document.getElementById('cancelUndockingBtn').addEventListener('click', () => {
        wasteResults.innerHTML = '';
    });
}

// Handle complete undocking
async function handleCompleteUndocking(containerId, returnItems) {
    const wasteResults = document.getElementById('wasteResults');
    
    try {
        const response = await fetch(`${API_BASE_URL}/waste/complete-undocking`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                undockingContainerId: containerId,
                returnItemIds: returnItems.map(item => item.itemId)
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to complete undocking');
        }
        
        const result = await response.json();
        
        showAlert('success', `Successfully completed undocking. ${result.removedItems || 0} items have been removed from the system.`);
        
        // Refresh data
        await loadItems();
        await loadContainers();
        updateStats();
        
        // Clear waste results
        if (wasteResults) {
            wasteResults.innerHTML = '<div class="alert alert-success">Undocking successfully completed.</div>';
        }
        
    } catch (error) {
        console.error('Error completing undocking:', error);
        showAlert('error', 'Failed to complete undocking. Please try again later.');
    }
}

// Handle simulation of days
async function handleSimulateDays() {
    const simulationDays = document.getElementById('simulationDaysInput').value;
    const simulationResults = document.getElementById('simulationResults');
    
    if (!simulationDays || simulationDays <= 0) {
        showAlert('warning', 'Please enter a valid number of days to simulate');
        return;
    }
    
    if (simulationResults) {
        simulationResults.innerHTML = '<div class="text-center"><div class="spinner-border text-primary" role="status"></div></div>';
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/simulate/day`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                days: parseInt(simulationDays)
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to simulate days');
        }
        
        const result = await response.json();
        
        // Display simulation results
        displaySimulationResults(result, simulationDays);
        
        // Refresh data
        await loadItems();
        updateStats();
        
    } catch (error) {
        console.error('Error simulating days:', error);
        showAlert('error', 'Failed to simulate days. Please try again later.');
        
        if (simulationResults) {
            simulationResults.innerHTML = '<div class="alert alert-danger">Failed to simulate days.</div>';
        }
    }
}

// Display simulation results
function displaySimulationResults(result, days) {
    const simulationResults = document.getElementById('simulationResults');
    if (!simulationResults) return;
    
    const expiredItems = result.expiredItems || [];
    const usedItems = result.usedItems || [];
    
    let html = `
        <div class="alert alert-info">
            <h5>Simulation Results</h5>
            <p>Simulated ${days} day${days > 1 ? 's' : ''} of operation</p>
        </div>
        
        <div class="row">
            <div class="col-md-6">
                <div class="card mb-4">
                    <div class="card-header">
                        Expired Items (${expiredItems.length})
                    </div>
                    <div class="card-body">
    `;
    
    if (expiredItems.length === 0) {
        html += '<p class="card-text">No items expired during this period.</p>';
    } else {
        html += `
            <div class="table-responsive">
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>Item ID</th>
                            <th>Name</th>
                            <th>Expiry Date</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        expiredItems.forEach(item => {
            html += `
                <tr>
                    <td>${item.itemId}</td>
                    <td>${item.name}</td>
                    <td>${item.expiryDate}</td>
                </tr>
            `;
        });
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
    }
    
    html += `
                    </div>
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="card mb-4">
                    <div class="card-header">
                        Used Items (${usedItems.length})
                    </div>
                    <div class="card-body">
    `;
    
    if (usedItems.length === 0) {
        html += '<p class="card-text">No items were used during this period.</p>';
    } else {
        html += `
            <div class="table-responsive">
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>Item ID</th>
                            <th>Name</th>
                            <th>Remaining Uses</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        usedItems.forEach(item => {
            html += `
                <tr>
                    <td>${item.itemId}</td>
                    <td>${item.name}</td>
                    <td>${item.remainingUses || 0}</td>
                </tr>
            `;
        });
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
    }
    
    html += `
                    </div>
                </div>
            </div>
        </div>
    `;
    
    if (expiredItems.length > 0 || usedItems.length > 0) {
        html += `
            <div class="mt-3">
                <a href="#" id="checkWasteAfterSimulation" class="btn btn-warning">Identify Waste Items</a>
            </div>
        `;
    }
    
    simulationResults.innerHTML = html;
    
    // Add event listener for waste check button
    const checkWasteBtn = document.getElementById('checkWasteAfterSimulation');
    if (checkWasteBtn) {
        checkWasteBtn.addEventListener('click', function(e) {
            e.preventDefault();
            document.getElementById('wasteBtn').click();
            setTimeout(() => {
                const identifyWasteBtn = document.getElementById('identifyWasteBtn');
                if (identifyWasteBtn) identifyWasteBtn.click();
            }, 100);
        });
    }
}

// Apply log filters
function applyLogFilters() {
    const startDate = document.getElementById('startDateFilter').value;
    const endDate = document.getElementById('endDateFilter').value;
    const actionType = document.getElementById('actionTypeFilter').value;
    const itemId = document.getElementById('itemIdFilter').value;
    
    let url = `${API_BASE_URL}/logs?`;
    const params = new URLSearchParams();
    
    if (startDate) params.append('startDate', startDate);
    if (endDate) params.append('endDate', endDate);
    if (actionType) params.append('actionType', actionType);
    if (itemId) params.append('itemId', itemId);
    
    url += params.toString();
    
    // Fetch logs with filters
    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load filtered logs');
            }
            return response.json();
        })
        .then(logs => {
            updateLogsList(logs);
        })
        .catch(error => {
            console.error('Error applying log filters:', error);
            showAlert('error', 'Failed to apply log filters. Please try again later.');
        });
}
