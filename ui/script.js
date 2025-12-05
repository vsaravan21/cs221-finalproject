// Sample itinerary data
const sampleItinerary = {
    day: 1,
    activities: [
        {
            time: "09:40 - 12:00",
            name: "Museum of the African Diaspora",
            category: "museum",
            cost: 12.00,
            satisfaction: 5.19,
            travelMode: null,
            travelTime: null,
            cumulativeCost: 12.00
        },
        {
            time: "12:00 - 14:10",
            name: "Contemporary Jewish Museum",
            category: "museum",
            cost: 16.00,
            satisfaction: 5.14,
            travelMode: "walk",
            travelTime: "0 min",
            cumulativeCost: 28.00
        },
        {
            time: "14:15 - 16:54",
            name: "San Francisco Museum of Modern Art (SFMOMA)",
            category: "museum",
            cost: 25.00,
            satisfaction: 4.83,
            travelMode: "walk",
            travelTime: "5 min",
            cumulativeCost: 53.00
        },
        {
            time: "17:06 - 18:36",
            name: "St. Mary's Square",
            category: "park",
            cost: 0.00,
            satisfaction: 3.34,
            travelMode: "walk",
            travelTime: "12 min",
            cumulativeCost: 53.00
        },
        {
            time: "18:40 - 20:10",
            name: "Willie Woo Woo Wong Playground",
            category: "park",
            cost: 0.00,
            satisfaction: 3.34,
            travelMode: "walk",
            travelTime: "4 min",
            cumulativeCost: 53.00
        },
        {
            time: "20:11 - 20:17",
            name: "Stockton St & Sacramento St",
            category: "transport",
            cost: 0.00,
            satisfaction: 2.29,
            travelMode: "walk",
            travelTime: "1 min",
            cumulativeCost: 53.00
        }
    ],
    summary: {
        activityTime: "10.5 hours",
        transitTime: "64 min",
        bufferTime: "93 min",
        dailyCost: "$53.00 / $167.00",
        status: "✓ Feasible"
    },
    overview: {
        totalCost: "$53.00",
        iqsScore: "0.623",
        totalSatisfaction: "28.71",
        totalActivities: "8"
    }
};

// Category icons and colors
const categoryConfig = {
    museum: { icon: "🏛️", color: "#2563eb" },
    park: { icon: "🌳", color: "#10b981" },
    restaurant: { icon: "🍽️", color: "#f59e0b" },
    transport: { icon: "🚌", color: "#6b7280" },
    shopping: { icon: "🛍️", color: "#8b5cf6" },
    landmark: { icon: "📍", color: "#ef4444" }
};

const travelModeIcons = {
    walk: "🚶",
    transit: "🚌",
    Uber: "🚗"
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeSliders();
    initializeForm();
    initializeNavigation();
});

// Initialize sliders
function initializeSliders() {
    // Days slider
    const daysSlider = document.getElementById('days');
    const daysValue = document.getElementById('days-value');
    daysSlider.addEventListener('input', (e) => {
        daysValue.textContent = `${e.target.value} day${e.target.value > 1 ? 's' : ''}`;
        updateDailyBudget();
    });

    // Budget slider
    const budgetInput = document.getElementById('budget');
    budgetInput.addEventListener('input', updateDailyBudget);

    // Interest sliders
    const interestSliders = document.querySelectorAll('.interests-grid .slider');
    interestSliders.forEach(slider => {
        const valueDisplay = document.getElementById(`${slider.id}-value`);
        slider.addEventListener('input', (e) => {
            valueDisplay.textContent = parseFloat(e.target.value).toFixed(1);
        });
    });
}

function updateDailyBudget() {
    const days = parseInt(document.getElementById('days').value) || 1;
    const budget = parseFloat(document.getElementById('budget').value) || 0;
    const dailyBudget = budget / days;
    document.getElementById('daily-budget').textContent = dailyBudget.toFixed(0);
}

// Initialize form submission
function initializeForm() {
    const form = document.getElementById('profile-form');
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        generateItinerary();
    });
}

// Helper function to get API base URL
// Uses same origin in production, localhost for development
function getApiUrl() {
    // If we're on localhost, use localhost:5001, otherwise use same origin
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        return 'http://localhost:5001';
    }
    return window.location.origin;
}

// Generate itinerary (calls backend API)
async function generateItinerary() {
    // Hide profile, show loading
    document.getElementById('profile-section').classList.add('hidden');
    document.getElementById('loading-section').classList.remove('hidden');

    // Collect form data
    const formData = {
        days: parseInt(document.getElementById('days').value),
        budget: parseFloat(document.getElementById('budget').value),
        pace: document.querySelector('input[name="pace"]:checked').value,
        interests: {
            food: parseFloat(document.getElementById('interest-food').value),
            museums: parseFloat(document.getElementById('interest-museums').value),
            outdoors: parseFloat(document.getElementById('interest-outdoors').value),
            parks: parseFloat(document.getElementById('interest-outdoors').value), // Combined with outdoors in UI
            shopping: parseFloat(document.getElementById('interest-shopping').value),
            nightlife: 0.0, // Nightlife slider removed from UI, always set to 0
            culture: parseFloat(document.getElementById('interest-culture').value),
        },
        hotel_lat: 37.7749, // Default SF coordinates (Union Square)
        hotel_lon: -122.4194,
    };

    // Simulate loading steps
    const steps = document.querySelectorAll('.loading-step');
    let currentStep = 0;

    const stepInterval = setInterval(() => {
        if (currentStep > 0) {
            steps[currentStep - 1].classList.remove('active');
            steps[currentStep - 1].querySelector('.step-icon').textContent = '✓';
        }
        
        if (currentStep < steps.length) {
            steps[currentStep].classList.add('active');
            steps[currentStep].querySelector('.step-icon').textContent = '⏳';
            currentStep++;
        } else {
            clearInterval(stepInterval);
        }
    }, 800);
    
    const apiBaseUrl = getApiUrl();
    
    try {
        // Call backend API
        const response = await fetch(`${apiBaseUrl}/api/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData),
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.statusText}`);
        }

        const data = await response.json();
        
        if (data.success) {
            // Store all itinerary data (multiple days)
            window.tripData = data;
            window.currentDay = 1; // Start with day 1
            setTimeout(() => {
                showItinerary();
            }, 500);
        } else {
            throw new Error(data.error || 'Failed to generate itinerary');
        }
    } catch (error) {
        console.error('Error generating itinerary:', error);
        
        // Fallback to sample data if API is not available
        console.warn('API not available, using sample data. Make sure to start the Flask server: python -m tripcompass.api_server');
        window.currentItinerary = sampleItinerary;
        setTimeout(() => {
            showItinerary();
        }, 500);
    }
}

// Show itinerary
function showItinerary() {
    document.getElementById('loading-section').classList.add('hidden');
    document.getElementById('itinerary-section').classList.remove('hidden');
    
    // Show summary button now that itinerary is generated
    const summaryBtn = document.getElementById('summary-nav-btn');
    if (summaryBtn) {
        summaryBtn.classList.remove('hidden');
    }
    
    // Generate day tabs
    renderDayTabs();
    
    // Show current day
    renderItinerary();
    updateOverview();
    updateDaySummary();
}

// Render day tabs dynamically
function renderDayTabs() {
    const dayTabsContainer = document.getElementById('day-tabs');
    if (!dayTabsContainer || !window.tripData) return;
    
    dayTabsContainer.innerHTML = '';
    
    for (let day = 1; day <= window.tripData.days; day++) {
        const tab = document.createElement('button');
        tab.className = `day-tab ${day === window.currentDay ? 'active' : ''}`;
        tab.dataset.day = day;
        tab.textContent = `Day ${day}`;
        tab.addEventListener('click', () => {
            window.currentDay = day;
            // Update active tab
            document.querySelectorAll('.day-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            // Re-render itinerary for selected day
            renderItinerary();
            updateDaySummary();
        });
        dayTabsContainer.appendChild(tab);
    }
}

// Render itinerary timeline
function renderItinerary() {
    const timeline = document.getElementById('timeline');
    timeline.innerHTML = '';

    // Get current day's itinerary
    let activities = [];
    if (window.tripData && window.tripData.itineraries) {
        const currentDayItinerary = window.tripData.itineraries.find(d => d.day === window.currentDay);
        if (currentDayItinerary) {
            activities = currentDayItinerary.activities || [];
        }
    } else if (window.currentItinerary) {
        // Fallback to old format
        activities = window.currentItinerary.activities || [];
    } else {
        // Fallback to sample
        activities = sampleItinerary.activities || [];
    }

    // Filter out transport activities first to get correct indices
    const filteredActivities = activities.filter(a => a.category !== 'transport');
    
    filteredActivities.forEach((activity, index) => {
        const category = categoryConfig[activity.category] || { icon: "📍", color: "#6b7280" };
        
        const activityCard = document.createElement('div');
        activityCard.className = 'activity-card';
        activityCard.onclick = () => showActivityDetails(activity, index);
        
        activityCard.innerHTML = `
            <div class="activity-header">
                <div>
                    <div class="activity-time">${activity.time}</div>
                    <div class="activity-title">${activity.name}</div>
                    <span class="activity-category" style="background: ${category.color}20; color: ${category.color}">
                        ${category.icon} ${activity.category}
                    </span>
                </div>
            </div>
            
            ${index > 0 && activity.travel_mode && activity.travel_time ? `
                <div class="travel-leg">
                    <span class="travel-mode-icon">${travelModeIcons[activity.travel_mode] || '🚶'}</span>
                    <span>${activity.travel_mode} ${activity.travel_time} from ${filteredActivities[index - 1].name}</span>
                </div>
            ` : index > 0 && activity.travelMode && activity.travelTime ? `
                <div class="travel-leg">
                    <span class="travel-mode-icon">${travelModeIcons[activity.travelMode]}</span>
                    <span>${activity.travelMode} ${activity.travelTime} from ${filteredActivities[index - 1].name}</span>
                </div>
            ` : index === 0 && (activity.travel_mode || activity.travelMode) ? `
                <div class="travel-leg">
                    <span class="travel-mode-icon">${travelModeIcons[activity.travel_mode || activity.travelMode] || '🚶'}</span>
                    <span>${activity.travel_mode || activity.travelMode} ${activity.travel_time || activity.travelTime || '0 min'} from hotel</span>
                </div>
            ` : ''}
            
            <div class="activity-details">
                <div class="activity-detail-item">
                    <strong>Cost:</strong> $${(activity.cost || 0).toFixed(2)}
                </div>
                <div class="activity-detail-item">
                    <strong>Cumulative:</strong> $${(activity.cumulative_cost || activity.cumulativeCost || 0).toFixed(2)}
                </div>
            </div>
        `;
        
        timeline.appendChild(activityCard);
    });
}

// Update overview stats (customer-facing only)
function updateOverview() {
    if (window.tripData) {
        document.getElementById('total-cost').textContent = `$${window.tripData.total_cost.toFixed(2)}`;
        document.getElementById('total-budget-label').textContent = `of $${window.tripData.total_budget.toFixed(2)} budget`;
        document.getElementById('total-days').textContent = window.tripData.days || '0';
        document.getElementById('total-activities').textContent = window.tripData.total_activities || '0';
    } else if (window.currentItinerary) {
        // Fallback to old format
        const overview = window.currentItinerary.overview || {};
        document.getElementById('total-cost').textContent = overview.total_cost || overview.totalCost || '$0.00';
        document.getElementById('total-activities').textContent = overview.total_activities || overview.totalActivities || '0';
    } else {
        document.getElementById('total-cost').textContent = '$0.00';
        document.getElementById('total-days').textContent = '0';
        document.getElementById('total-activities').textContent = '0';
    }
}

// Update day summary
function updateDaySummary() {
    let summary = {};
    
    if (window.tripData && window.tripData.itineraries) {
        const currentDayItinerary = window.tripData.itineraries.find(d => d.day === window.currentDay);
        if (currentDayItinerary) {
            summary = currentDayItinerary.summary || {};
        }
    } else if (window.currentItinerary) {
        summary = window.currentItinerary.summary || {};
    } else {
        summary = sampleItinerary.summary || {};
    }
    
    // Update summary card if it exists
    const summaryCard = document.querySelector('.summary-card');
    if (summaryCard && summary) {
        const items = summaryCard.querySelectorAll('.summary-item');
        if (items.length >= 3) {
            items[0].querySelector('.summary-value').textContent = summary.activity_time || summary.activityTime || '0 hours';
            items[1].querySelector('.summary-value').textContent = summary.transit_time || summary.transitTime || '0 min';
            items[2].querySelector('.summary-value').textContent = summary.daily_cost || summary.dailyCost || '$0.00 / $0.00';
            if (items.length >= 4) {
                items[3].querySelector('.summary-value').textContent = summary.status || summary.status || 'Unknown';
            }
        }
    }
}

// Store current activity being viewed
let currentActivityIndex = -1;
let currentActivityDay = 1;

// Show activity details modal
function showActivityDetails(activity, index) {
    const modal = document.getElementById('activity-modal');
    const details = document.getElementById('activity-details');
    const category = categoryConfig[activity.category] || { icon: "📍", color: "#6b7280" };
    
    // Store current activity info
    currentActivityIndex = index;
    currentActivityDay = window.currentDay || 1;
    
    details.innerHTML = `
        <h2 style="margin-bottom: 1rem;">${activity.name}</h2>
        <div style="margin-bottom: 1.5rem;">
            <span class="activity-category" style="background: ${category.color}20; color: ${category.color}">
                ${category.icon} ${activity.category}
            </span>
        </div>
        
        <div style="display: grid; gap: 1rem; margin-bottom: 1.5rem;">
            <div>
                <strong>Time:</strong> ${activity.time}
            </div>
            <div>
                <strong>Cost:</strong> $${(activity.cost || 0).toFixed(2)}
            </div>
            ${activity.travel_mode || activity.travelMode ? `
                <div>
                    <strong>Travel:</strong> ${travelModeIcons[activity.travel_mode || activity.travelMode] || '🚶'} ${activity.travel_mode || activity.travelMode} ${activity.travel_time || activity.travelTime || '0 min'}
                </div>
            ` : ''}
        </div>
        
        <div style="display: flex; gap: 1rem;">
            <button class="btn btn-secondary" onclick="closeModal()">Close</button>
            <button class="btn btn-secondary" onclick="removeActivity()">Remove from Itinerary</button>
            <button class="btn btn-secondary" onclick="swapActivity()">Swap with Similar</button>
        </div>
    `;
    
    modal.classList.remove('hidden');
}

// Close modal
function closeModal() {
    document.getElementById('activity-modal').classList.add('hidden');
}

// Initialize navigation
function initializeNavigation() {
    const navButtons = document.querySelectorAll('.nav-btn');
    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const view = btn.dataset.view;
            
            // Update active state
            navButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Show/hide sections
            if (view === 'itinerary') {
                document.getElementById('itinerary-section').classList.remove('hidden');
                document.getElementById('summary-section').classList.add('hidden');
            } else if (view === 'summary') {
                document.getElementById('itinerary-section').classList.add('hidden');
                document.getElementById('summary-section').classList.remove('hidden');
                // Render dynamic summary when switching to summary view
                renderSummary();
            }
        });
    });

    // Close modal on overlay click
    document.querySelector('.modal-overlay')?.addEventListener('click', closeModal);
    document.querySelector('.modal-close')?.addEventListener('click', closeModal);

    // New trip button
    document.getElementById('new-trip-btn')?.addEventListener('click', () => {
        document.getElementById('itinerary-section').classList.add('hidden');
        document.getElementById('summary-section').classList.add('hidden');
        document.getElementById('profile-section').classList.remove('hidden');
        // Hide summary button when starting new trip
        const summaryBtn = document.getElementById('summary-nav-btn');
        if (summaryBtn) {
            summaryBtn.classList.add('hidden');
        }
    });

    // Export button
    document.getElementById('export-btn')?.addEventListener('click', () => {
        exportToPDF();
    });
}

// Render dynamic summary view
function renderSummary() {
    const summaryContent = document.getElementById('summary-content');
    if (!summaryContent || !window.tripData || !window.tripData.itineraries) {
        summaryContent.innerHTML = '<p>No trip data available.</p>';
        return;
    }
    
    const itineraries = window.tripData.itineraries;
    const totalBudget = window.tripData.total_budget || 0;
    
    // Calculate totals across all days
    let totalCost = 0;
    let totalActivities = 0;
    let categoryCounts = {};
    let totalTransitTime = 0;
    let daySummaries = [];
    
    itineraries.forEach(dayItinerary => {
        let dayCost = 0;
        let dayActivities = 0;
        let dayTransitTime = 0;
        
        dayItinerary.activities.forEach(activity => {
            if (activity.category !== 'transport') {
                dayCost += activity.cost || 0;
                dayActivities++;
                
                // Count categories
                const category = activity.category || 'unknown';
                categoryCounts[category] = (categoryCounts[category] || 0) + 1;
                
                // Sum transit time
                dayTransitTime += activity.travel_time_hours || 0;
            }
        });
        
        totalCost += dayCost;
        totalActivities += dayActivities;
        totalTransitTime += dayTransitTime;
        
        daySummaries.push({
            day: dayItinerary.day,
            cost: dayCost,
            activities: dayActivities,
            transitTime: dayTransitTime,
            summary: dayItinerary.summary || {}
        });
    });
    
    const budgetUsedPercent = totalBudget > 0 ? (totalCost / totalBudget) * 100 : 0;
    const avgTransitPerActivity = totalActivities > 0 ? totalTransitTime / totalActivities : 0;
    
    // Build HTML
    let html = `
        <div class="dashboard-grid">
            <div class="dashboard-card">
                <h3>Budget Breakdown</h3>
                <div class="budget-chart">
                    <div class="budget-bar">
                        <div class="budget-fill" style="width: ${Math.min(100, budgetUsedPercent)}%"></div>
                    </div>
                    <div class="budget-labels">
                        <span>Used: $${totalCost.toFixed(2)}</span>
                        <span>Remaining: $${(totalBudget - totalCost).toFixed(2)}</span>
                    </div>
                </div>
            </div>
            <div class="dashboard-card">
                <h3>Category Distribution</h3>
                <div class="category-list">
    `;
    
    // Sort categories by count and show top 6
    const categoryIcons = {
        'museum': '🏛️',
        'park': '🌳',
        'restaurant': '🍽️',
        'shopping': '🛍️',
        'landmark': '📍',
        'culture': '🎭'
    };
    
    const sortedCategories = Object.entries(categoryCounts)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 6);
    
    sortedCategories.forEach(([category, count]) => {
        html += `
            <div class="category-item">
                <span class="category-name">${categoryIcons[category] || '📍'} ${category.charAt(0).toUpperCase() + category.slice(1)}</span>
                <span class="category-count">${count}</span>
            </div>
        `;
    });
    
    html += `
                </div>
            </div>
            <div class="dashboard-card">
                <h3>Travel Efficiency</h3>
                <div class="efficiency-metric">
                    <span class="metric-value">${avgTransitPerActivity.toFixed(2)}</span>
                    <span class="metric-unit">h/activity</span>
                </div>
                <p class="metric-desc">Average travel time per activity</p>
            </div>
        </div>
        
        <div class="day-breakdown-section" style="margin-top: 2rem;">
            <h3 style="margin-bottom: 1.5rem;">Day-by-Day Breakdown</h3>
            <div class="day-breakdown-grid">
    `;
    
    daySummaries.forEach(daySummary => {
        const summary = daySummary.summary;
        html += `
            <div class="day-breakdown-card">
                <h4>Day ${daySummary.day}</h4>
                <div class="day-breakdown-stats">
                    <div class="breakdown-stat">
                        <span class="breakdown-label">Activities</span>
                        <span class="breakdown-value">${daySummary.activities}</span>
                    </div>
                    <div class="breakdown-stat">
                        <span class="breakdown-label">Cost</span>
                        <span class="breakdown-value">$${daySummary.cost.toFixed(2)}</span>
                    </div>
                    <div class="breakdown-stat">
                        <span class="breakdown-label">Activity Time</span>
                        <span class="breakdown-value">${summary.activity_time || '0 hours'}</span>
                    </div>
                    <div class="breakdown-stat">
                        <span class="breakdown-label">Transit Time</span>
                        <span class="breakdown-value">${summary.transit_time || '0 min'}</span>
                    </div>
                    <div class="breakdown-stat">
                        <span class="breakdown-label">Status</span>
                        <span class="breakdown-value ${summary.is_feasible ? 'status-feasible' : 'status-violation'}">${summary.status || 'Unknown'}</span>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += `
            </div>
        </div>
    `;
    
    summaryContent.innerHTML = html;
}

// Export to PDF function
function exportToPDF() {
    if (!window.tripData || !window.tripData.itineraries) {
        alert('No itinerary data available to export.');
        return;
    }
    
    // Create a printable version of the itinerary
    let printContent = `
        <html>
        <head>
            <title>TripCompass Itinerary</title>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; }
                h1 { color: #1f2937; }
                h2 { color: #374151; margin-top: 30px; }
                .day-section { margin-bottom: 40px; page-break-inside: avoid; }
                .activity { margin: 15px 0; padding: 10px; border-left: 3px solid #3b82f6; }
                .activity-time { font-weight: bold; color: #6b7280; }
                .activity-name { font-size: 18px; font-weight: bold; margin: 5px 0; }
                .activity-details { color: #6b7280; margin-top: 5px; }
                .summary { background: #f9fafb; padding: 15px; border-radius: 8px; margin-top: 20px; }
                @media print {
                    body { padding: 10px; }
                    .day-section { page-break-after: auto; }
                }
            </style>
        </head>
        <body>
            <h1>Your TripCompass Itinerary</h1>
            <p><strong>Total Budget:</strong> $${window.tripData.total_budget.toFixed(2)}</p>
            <p><strong>Total Cost:</strong> $${window.tripData.total_cost.toFixed(2)}</p>
            <p><strong>Days:</strong> ${window.tripData.days}</p>
            <p><strong>Total Activities:</strong> ${window.tripData.total_activities}</p>
            <hr style="margin: 30px 0;">
    `;
    
    window.tripData.itineraries.forEach(dayItinerary => {
        printContent += `
            <div class="day-section">
                <h2>Day ${dayItinerary.day}</h2>
        `;
        
        dayItinerary.activities.forEach(activity => {
            if (activity.category !== 'transport') {
                printContent += `
                    <div class="activity">
                        <div class="activity-time">${activity.time}</div>
                        <div class="activity-name">${activity.name}</div>
                        <div class="activity-details">
                            Category: ${activity.category} | Cost: $${(activity.cost || 0).toFixed(2)}
                            ${activity.travel_mode && activity.travel_time ? ` | Travel: ${activity.travel_mode} ${activity.travel_time}` : ''}
                        </div>
                    </div>
                `;
            }
        });
        
        const summary = dayItinerary.summary || {};
        printContent += `
                <div class="summary">
                    <strong>Day Summary:</strong><br>
                    Activity Time: ${summary.activity_time || '0 hours'}<br>
                    Transit Time: ${summary.transit_time || '0 min'}<br>
                    Daily Cost: ${summary.daily_cost || '$0.00'}<br>
                    Status: ${summary.status || 'Unknown'}
                </div>
            </div>
        `;
    });
    
    printContent += `
        </body>
        </html>
    `;
    
    // Open print window
    const printWindow = window.open('', '_blank');
    printWindow.document.write(printContent);
    printWindow.document.close();
    printWindow.focus();
    
    // Wait for content to load, then print
    setTimeout(() => {
        printWindow.print();
    }, 250);
}

// Remove activity from itinerary
function removeActivity() {
    if (currentActivityIndex < 0 || !window.tripData || !window.tripData.itineraries) {
        alert('No activity selected to remove.');
        return;
    }
    
    const dayItinerary = window.tripData.itineraries.find(d => d.day === currentActivityDay);
    if (!dayItinerary || !dayItinerary.activities) {
        alert('Activity not found.');
        return;
    }
    
    // Filter out transport activities to get the correct index
    const filteredActivities = dayItinerary.activities.filter(a => a.category !== 'transport');
    if (currentActivityIndex >= filteredActivities.length) {
        alert('Activity not found.');
        return;
    }
    
    // Find the actual activity in the full activities array
    const activityToRemove = filteredActivities[currentActivityIndex];
    const actualIndex = dayItinerary.activities.findIndex(a => 
        a.id === activityToRemove.id && a.name === activityToRemove.name
    );
    
    if (actualIndex < 0) {
        alert('Activity not found.');
        return;
    }
    
    const activityCost = activityToRemove.cost || 0;
    const activityDuration = (activityToRemove.end_time || 0) - (activityToRemove.start_time || 0);
    const travelTime = activityToRemove.travel_time_hours || 0;
    
    // Remove the activity
    dayItinerary.activities.splice(actualIndex, 1);
    
    // Re-filter to get new indices
    const newFilteredActivities = dayItinerary.activities.filter(a => a.category !== 'transport');
    
    // Recalculate timeline - adjust start times for subsequent activities
    let currentTime = 9.0; // Day start time
    
    // Find the index in filtered activities for recalculation
    const recalcStartIndex = currentActivityIndex;
    
    // If this wasn't the first activity, use the previous activity's end time
    if (recalcStartIndex > 0 && newFilteredActivities.length > 0) {
        const prevActivity = newFilteredActivities[recalcStartIndex - 1];
        currentTime = prevActivity.end_time || currentTime;
    }
    
    // Recalculate times and cumulative costs for remaining activities
    let cumulativeCost = 0;
    if (recalcStartIndex > 0 && newFilteredActivities.length > 0) {
        const prevActivity = newFilteredActivities[recalcStartIndex - 1];
        cumulativeCost = prevActivity.cumulative_cost || 0;
    }
    
    // Recalculate from the removal point forward
    for (let i = recalcStartIndex; i < newFilteredActivities.length; i++) {
        const activityToUpdate = newFilteredActivities[i];
        
        // Calculate travel time from previous activity (or hotel if first)
        let travelTimeFromPrev = 0;
        if (i === 0) {
            // First activity - travel from hotel
            const userProfile = window.tripData.user_profile || {};
            const hotelLat = userProfile.hotel_lat || 37.7749;
            const hotelLon = userProfile.hotel_lon || -122.4194;
            const actLat = activityToUpdate.lat || 37.7749;
            const actLon = activityToUpdate.lon || -122.4194;
            
            // Select travel mode based on distance
            const distance = calculateDistance(hotelLat, hotelLon, actLat, actLon);
            let travelMode = 'walk';
            if (distance < 0.8) travelMode = 'walk';
            else if (distance < 3.0) travelMode = 'transit';
            else travelMode = 'Uber';
            
            travelTimeFromPrev = calculateTravelTime(hotelLat, hotelLon, actLat, actLon, travelMode);
            activityToUpdate.travel_mode = travelMode;
        } else {
            const prevActivity = newFilteredActivities[i - 1];
            const prevLat = prevActivity.lat || 37.7749;
            const prevLon = prevActivity.lon || -122.4194;
            const actLat = activityToUpdate.lat || 37.7749;
            const actLon = activityToUpdate.lon || -122.4194;
            
            // Select travel mode based on distance
            const distance = calculateDistance(prevLat, prevLon, actLat, actLon);
            let travelMode = 'walk';
            if (distance < 0.8) travelMode = 'walk';
            else if (distance < 3.0) travelMode = 'transit';
            else travelMode = 'Uber';
            
            travelTimeFromPrev = calculateTravelTime(prevLat, prevLon, actLat, actLon, travelMode);
            activityToUpdate.travel_mode = travelMode;
        }
        
        // Update times
        activityToUpdate.start_time = currentTime + travelTimeFromPrev;
        activityToUpdate.end_time = activityToUpdate.start_time + (activityToUpdate.duration_hours || 0);
        activityToUpdate.travel_time_from_prev = travelTimeFromPrev;
        activityToUpdate.travel_time_hours = travelTimeFromPrev;
        
        // Update cumulative cost
        cumulativeCost += activityToUpdate.cost || 0;
        activityToUpdate.cumulative_cost = cumulativeCost;
        
        // Update time string
        activityToUpdate.time = formatTimeRange(activityToUpdate.start_time, activityToUpdate.end_time);
        if (travelTimeFromPrev > 0) {
            activityToUpdate.travel_time = formatTimeMinutes(travelTimeFromPrev);
        }
        
        currentTime = activityToUpdate.end_time;
    }
    
    // Recalculate day summary
    recalculateDaySummary(currentActivityDay);
    
    // Recalculate totals
    recalculateTotals();
    
    // Re-render the itinerary
    renderItinerary();
    updateDaySummary();
    updateOverview();
    
    // Close modal
    closeModal();
}

// Swap activity with a similar one
async function swapActivity() {
    if (currentActivityIndex < 0 || !window.tripData || !window.tripData.itineraries) {
        alert('No activity selected to swap.');
        return;
    }
    
    const dayItinerary = window.tripData.itineraries.find(d => d.day === currentActivityDay);
    if (!dayItinerary || !dayItinerary.activities) {
        alert('Activity not found.');
        return;
    }
    
    // Filter out transport activities to get the correct index
    const filteredActivities = dayItinerary.activities.filter(a => a.category !== 'transport');
    if (currentActivityIndex >= filteredActivities.length) {
        alert('Activity not found.');
        return;
    }
    
    // Find the actual activity in the full activities array
    const currentActivity = filteredActivities[currentActivityIndex];
    const actualIndex = dayItinerary.activities.findIndex(a => 
        a.id === currentActivity.id && a.name === currentActivity.name
    );
    
    if (actualIndex < 0) {
        alert('Activity not found.');
        return;
    }
    
    const category = currentActivity.category;
    
    // Get all POIs from the backend to find similar activities
    const apiBaseUrl = getApiUrl();
    
    try {
        const response = await fetch(`${apiBaseUrl}/api/similar-activities`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                category: category,
                exclude_id: currentActivity.id || currentActivity.name,
                current_lat: currentActivity.lat || 37.7749,
                current_lon: currentActivity.lon || -122.4194,
            }),
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch similar activities');
        }
        
        const data = await response.json();
        const similarActivities = data.activities || [];
        
        if (similarActivities.length === 0) {
            alert(`No similar ${category} activities found to swap with.`);
            return;
        }
        
        // Pick the first similar activity (you could add a selection UI here)
        const replacement = similarActivities[0];
        
        // Replace the activity
        const oldCost = currentActivity.cost || 0;
        const newCost = replacement.cost || 0;
        const costDiff = newCost - oldCost;
        
        // Update the activity
        Object.assign(currentActivity, {
            id: replacement.id,
            name: replacement.name,
            category: replacement.category,
            cost: replacement.cost,
            duration_hours: replacement.duration_hours || currentActivity.duration_hours,
            lat: replacement.lat,
            lon: replacement.lon,
            open_start: replacement.open_start,
            open_end: replacement.open_end,
        });
        
        // Recalculate end time
        currentActivity.end_time = currentActivity.start_time + (currentActivity.duration_hours || 0);
        currentActivity.time = formatTimeRange(currentActivity.start_time, currentActivity.end_time);
        
        // Update cumulative costs for this and subsequent activities
        let cumulativeCost = currentActivity.cumulative_cost - oldCost;
        for (let i = actualIndex; i < dayItinerary.activities.length; i++) {
            const activityItem = dayItinerary.activities[i];
            if (activityItem.category !== 'transport') {
                cumulativeCost += activityItem.cost || 0;
                activityItem.cumulative_cost = cumulativeCost;
            }
        }
        
        // Recalculate day summary
        recalculateDaySummary(currentActivityDay);
        
        // Recalculate totals
        recalculateTotals();
        
        // Re-render
        renderItinerary();
        updateDaySummary();
        updateOverview();
        
        // Close modal
        closeModal();
        
    } catch (error) {
        console.error('Error swapping activity:', error);
        // Fallback: just show an alert
        alert(`Could not find similar ${category} activities. Please try again later.`);
    }
}

// Helper function to calculate distance in km
function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371; // Earth's radius in km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c; // Distance in km
}

// Helper function to calculate travel time
function calculateTravelTime(lat1, lon1, lat2, lon2, mode) {
    const distance = calculateDistance(lat1, lon1, lat2, lon2);
    
    // Speed based on mode (km/h)
    let speed = 4.0; // walk
    if (mode === 'transit') speed = 12.0;
    else if (mode === 'Uber' || mode === 'car') speed = 25.0;
    
    // Add wait time
    let waitTime = 0;
    if (mode === 'transit') waitTime = 0.08; // ~5 min
    else if (mode === 'Uber' || mode === 'car') waitTime = 0.13; // ~8 min
    
    return (distance / speed) + waitTime; // Return in hours
}

// Helper function to format time range
function formatTimeRange(startTime, endTime) {
    const start = formatTime(startTime);
    const end = formatTime(endTime);
    return `${start} - ${end}`;
}

// Helper function to format time
function formatTime(hours) {
    const h = Math.floor(hours);
    const m = Math.round((hours - h) * 60);
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}

// Helper function to format time in minutes
function formatTimeMinutes(hours) {
    const minutes = Math.round(hours * 60);
    return `${minutes} min`;
}

// Recalculate day summary
function recalculateDaySummary(day) {
    const dayItinerary = window.tripData.itineraries.find(d => d.day === day);
    if (!dayItinerary) return;
    
    const activities = dayItinerary.activities.filter(a => a.category !== 'transport');
    
    // Calculate activity time
    let activityTime = 0;
    activities.forEach(act => {
        activityTime += (act.end_time || 0) - (act.start_time || 0);
    });
    
    // Calculate transit time
    let transitTime = 0;
    activities.forEach(act => {
        transitTime += act.travel_time_hours || 0;
    });
    
    // Calculate daily cost
    let dailyCost = 0;
    activities.forEach(act => {
        dailyCost += act.cost || 0;
    });
    
    const dailyBudget = (window.tripData.total_budget || 0) / (window.tripData.days || 1);
    
    // Update summary
    dayItinerary.summary = {
        activity_time_hours: activityTime,
        activity_time: `${activityTime.toFixed(1)} hours`,
        transit_time_hours: transitTime,
        transit_time: formatTimeMinutes(transitTime),
        daily_cost: `$${dailyCost.toFixed(2)} / $${dailyBudget.toFixed(2)}`,
        cost_used: dailyCost,
        cost_remaining: dailyBudget - dailyCost,
        status: '✓ Feasible',
        is_feasible: true,
    };
}

// Recalculate totals
function recalculateTotals() {
    if (!window.tripData || !window.tripData.itineraries) return;
    
    let totalCost = 0;
    let totalActivities = 0;
    
    window.tripData.itineraries.forEach(dayItinerary => {
        dayItinerary.activities.forEach(activity => {
            if (activity.category !== 'transport') {
                totalCost += activity.cost || 0;
                totalActivities++;
            }
        });
    });
    
    window.tripData.total_cost = totalCost;
    window.tripData.total_activities = totalActivities;
}

// Export functions for global access
window.showActivityDetails = showActivityDetails;
window.closeModal = closeModal;
window.removeActivity = removeActivity;
window.swapActivity = swapActivity;

