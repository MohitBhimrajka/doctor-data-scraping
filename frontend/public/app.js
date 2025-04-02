// Constants and data
const BACKEND_API_URL = "http://localhost:8000";

// City tiers for India
const INDIA_CITIES = {
    tier1: [
        "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", 
        "Kolkata", "Pune", "Ahmedabad", "Surat", "Jaipur"
    ],
    tier2: [
        "Lucknow", "Kanpur", "Nagpur", "Indore", "Thane", "Bhopal", 
        "Visakhapatnam", "Pimpri-Chinchwad", "Patna", "Vadodara", 
        "Ghaziabad", "Ludhiana", "Agra", "Nashik", "Faridabad", 
        "Meerut", "Rajkot", "Kalyan-Dombivli", "Vasai-Virar", 
        "Varanasi", "Srinagar", "Aurangabad", "Dhanbad", "Amritsar", 
        "Navi Mumbai", "Allahabad", "Ranchi", "Howrah", "Coimbatore", 
        "Jabalpur", "Gwalior", "Vijayawada", "Jodhpur", "Madurai", "Raipur",
        "Amravati", "Solapur", "Bhilai", "Jamnagar", "Warangal", "Guntur",
        "Cuttack", "Udaipur", "Malegaon", "Kochi", "Gorakhpur", "Bhavnagar",
        "Dehradun", "Jhansi", "Nellore", "Mangalore", "Tirupur", "Tirunelveli",
        "Ujjain", "Bijapur", "Mathura", "Bilaspur", "Shahjahanpur"
    ],
    tier3: [
        "Kota", "Chandigarh", "Guwahati", "Solapur", "Hubli-Dharwad", 
        "Bareilly", "Moradabad", "Mysore", "Gurgaon", "Aligarh", 
        "Jalandhar", "Tiruchirappalli", "Bhubaneswar", "Salem", "Mira-Bhayandar", 
        "Warangal", "Jalgaon", "Guntur", "Thiruvananthapuram", "Bhiwandi", 
        "Saharanpur", "Gorakhpur", "Bikaner", "Amravati", "Noida", 
        "Jamshedpur", "Bhilai", "Cuttack", "Firozabad", "Kochi", 
        "Nellore", "Bhavnagar", "Dehradun", "Durgapur", "Asansol", 
        "Rourkela", "Nanded", "Kolhapur", "Ajmer", "Akola", "Gulbarga", 
        "Jamnagar", "Ujjain", "Loni", "Siliguri", "Jhansi", 
        "Ulhasnagar", "Jammu", "Sangli-Miraj", "Mangalore", "Erode",
        "Belgaum", "Ambattur", "Tirunelveli", "Malegaon", "Gaya", 
        "Jalgaon", "Udaipur", "Maheshtala", "Davanagere", "Kozhikode",
        "Kurnool", "Rajpur Sonarpur", "Rajahmundry", "Yamuna Nagar",
        "Korba", "Kamarhati", "Nagercoil", "Kakinada", "Pali", "Mandsaur",
        "Ichalkaranji", "Jalna", "Thoothukudi", "Santipur", "Alwar", 
        "Bidar", "Barddhaman", "Nazira", "Ramgarh", "Ongole", "Gandhinagar"
    ]
};

// Define popular specializations
const POPULAR_SPECIALIZATIONS = [
    'Cardiologist',
    'Dermatologist',
    'Pediatrician',
    'Orthopedist',
    'Dentist',
    'General Physician',
    'Gynecologist',
    'ENT Specialist',
    'Ophthalmologist',
    'Psychiatrist',
    'Neurologist',
    'Gastroenterologist',
    'Urologist',
    'Endocrinologist',
    'Sports Medicine',
    'Diabetologist',
    'Pulmonologist',
    'Physiotherapist',
    'Nutritionist'
];

// Tier descriptions for UI
const TIER_DESCRIPTIONS = {
    tier1: "Includes major metropolitan areas like Mumbai, Delhi, Bangalore",
    tier2: "Includes significant urban centers like Lucknow, Nagpur, Indore",
    tier3: "Includes smaller but important cities like Kota, Mysore, Dehradun"
};

// Quick city selections
const QUICK_CITY_SELECTIONS = {
    metro: ["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad"],
    south: ["Bangalore", "Chennai", "Hyderabad", "Kochi", "Coimbatore", "Mysore", "Mangalore", "Thiruvananthapuram"],
    north: ["Delhi", "Chandigarh", "Jaipur", "Lucknow", "Amritsar", "Kanpur", "Agra", "Dehradun"]
};

// State variable to track application state
let appState = {
    activeTab: "single-city",
    wizardStep: 1,
    selectedCities: [],
    selectedSpecialization: "",
    searchResults: null,
    searchInProgress: false
};

// Add search progress simulation
let searchProgressInterval;
let searchProgressValue = 0;

// Function to simulate search progress
function simulateSearchProgress() {
    // Reset progress
    searchProgressValue = 0;
    updateSearchProgress(0, "Initializing search...");
    
    // Clear any existing interval
    if (searchProgressInterval) {
        clearInterval(searchProgressInterval);
    }
    
    // Start progress simulation
    searchProgressInterval = setInterval(() => {
        // Simulate non-linear progress
        // Progress faster at the beginning, slower towards the end
        if (searchProgressValue < 90) {
            // Increments get smaller as we approach 90%
            const increment = (90 - searchProgressValue) / 20;
            searchProgressValue += increment;
            
            // Update progress messages based on current value
            let progressMessage = "Searching for doctors...";
            if (searchProgressValue < 20) {
                progressMessage = "Initializing sources...";
            } else if (searchProgressValue < 40) {
                progressMessage = "Searching Practo database...";
            } else if (searchProgressValue < 60) {
                progressMessage = "Searching JustDial listings...";
            } else if (searchProgressValue < 80) {
                progressMessage = "Collecting hospital data...";
            } else {
                progressMessage = "Finalizing results...";
            }
            
            updateSearchProgress(searchProgressValue, progressMessage);
        }
    }, 200);
}

// Function to update progress UI
function updateSearchProgress(value, message) {
    const progressBar = document.getElementById('search-progress-bar');
    const progressText = document.getElementById('search-progress-text');
    
    if (progressBar && progressText) {
        progressBar.style.width = `${value}%`;
        progressText.textContent = message;
        
        // Add smooth transition effect
        progressBar.style.transition = 'width 0.5s ease-in-out';
        
        // Change color based on progress
        if (value < 30) {
            progressBar.style.backgroundColor = '#42A5F5'; // Light blue
        } else if (value < 70) {
            progressBar.style.backgroundColor = '#1976D2'; // Medium blue
        } else {
            progressBar.style.backgroundColor = '#0D47A1'; // Dark blue
        }
    }
}

// Function to complete search progress
function completeSearchProgress() {
    // Clear the interval
    if (searchProgressInterval) {
        clearInterval(searchProgressInterval);
    }
    
    // Set to 100%
    updateSearchProgress(100, "Search complete!");
}

// DOM Ready function
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// Main initialization function
function initializeApp() {
    console.log('Initializing app...');
    
    populateUIElements();
    console.log('UI elements populated');
    
    setupEventListeners();
    console.log('Event listeners set up');
    
    setupExportButton();
    console.log('Export button configured');
    
    setupBackToSearchButton();
    console.log('Back to search button configured');
    
    addTooltips();
    console.log('Tooltips added');
    
    // Add page load animation
    document.body.style.opacity = '0';
    setTimeout(() => {
        document.body.style.transition = 'opacity 0.5s ease';
        document.body.style.opacity = '1';
    }, 100);
    
    // Add new UI enhancements
    addBackToTopButton();
    addTableLoadingEffects();
    
    // Double-check that critical search button event listeners are attached
    const searchButtons = [
        { id: 'single-city-search', action: 'Single city search' },
        { id: 'tier-search', action: 'Tier-wise search' },
        { id: 'start-custom-search', action: 'Custom search' },
        { id: 'country-search', action: 'Countrywide search' }
    ];
    
    searchButtons.forEach(button => {
        const element = document.getElementById(button.id);
        if (element) {
            // Add a click event listener that logs the action for debugging
            element.addEventListener('click', () => {
                console.log(`${button.action} button clicked`);
            });
        } else {
            console.error(`Button element not found: ${button.id}`);
        }
    });
    
    // Show a welcome notification
    setTimeout(() => {
        showNotification('Welcome to Doctor Search! Start by selecting a search method above.', 'info');
    }, 1000);
    
    console.log('App initialization complete');
}

// UI Population functions
function populateUIElements() {
    populateCityDropdowns();
    populateSpecializationDropdowns();
    populateCountrywideSearchCities();
}

function populateCityDropdowns() {
    // Single City Tab city datalist
    const cityDatalist = document.getElementById('city-list');
    
    // Add all cities from all tiers
    const allCities = [...INDIA_CITIES.tier1, ...INDIA_CITIES.tier2, ...INDIA_CITIES.tier3];
    const uniqueCities = [...new Set(allCities)].sort();
    
    // Clear existing options
    cityDatalist.innerHTML = '';
    
    // Add options to datalist
    uniqueCities.forEach(city => {
        const option = document.createElement('option');
        option.value = city;
        cityDatalist.appendChild(option);
    });
    
    // Populate city checkboxes for custom cities tab
    populateCityCheckboxes('tier1-cities-select', INDIA_CITIES.tier1);
    populateCityCheckboxes('tier2-cities-select', INDIA_CITIES.tier2);
    populateCityCheckboxes('tier3-cities-select', INDIA_CITIES.tier3);
    
    // Populate tier cities list for tier-wise search
    updateTierCitiesList('tier1');
}

function populateCityCheckboxes(containerId, cities) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';
    
    cities.forEach(city => {
        const checkbox = document.createElement('div');
        checkbox.className = 'city-checkbox';
        checkbox.innerHTML = `
            <input type="checkbox" id="${city.replace(/\s+/g, '-').toLowerCase()}" name="city" value="${city}">
            <label for="${city.replace(/\s+/g, '-').toLowerCase()}">${city}</label>
        `;
        container.appendChild(checkbox);
    });
}

function populateSpecializationDropdowns() {
    const specializationSelects = [
        'spec-common-single',
        'spec-common-tier',
        'spec-common-custom',
        'spec-common-country'
    ];
    
    specializationSelects.forEach(selectId => {
        const select = document.getElementById(selectId);
        select.innerHTML = '';
        
        POPULAR_SPECIALIZATIONS.forEach(spec => {
            const option = document.createElement('option');
            option.value = spec;
            option.textContent = spec;
            select.appendChild(option);
        });
    });
}

function populateCountrywideSearchCities() {
    // Populate tier1 cities
    const tier1Container = document.getElementById('countrywide-tier1');
    INDIA_CITIES.tier1.forEach(city => {
        const cityElement = document.createElement('div');
        cityElement.textContent = `• ${city}`;
        tier1Container.appendChild(cityElement);
    });
    
    // Populate tier2 cities (showing first 15 with a "more" indicator)
    const tier2Container = document.getElementById('countrywide-tier2');
    const tier2Display = INDIA_CITIES.tier2.slice(0, 15);
    tier2Display.forEach(city => {
        const cityElement = document.createElement('div');
        cityElement.textContent = `• ${city}`;
        tier2Container.appendChild(cityElement);
    });
    
    if (INDIA_CITIES.tier2.length > 15) {
        const moreElement = document.createElement('div');
        moreElement.textContent = `...and ${INDIA_CITIES.tier2.length - 15} more`;
        moreElement.style.fontStyle = 'italic';
        tier2Container.appendChild(moreElement);
    }
    
    // Populate tier3 cities (showing first 10 with a "more" indicator)
    const tier3Container = document.getElementById('countrywide-tier3');
    const tier3Display = INDIA_CITIES.tier3.slice(0, 10);
    tier3Display.forEach(city => {
        const cityElement = document.createElement('div');
        cityElement.textContent = `• ${city}`;
        tier3Container.appendChild(cityElement);
    });
    
    if (INDIA_CITIES.tier3.length > 10) {
        const moreElement = document.createElement('div');
        moreElement.textContent = `...and ${INDIA_CITIES.tier3.length - 10} more`;
        moreElement.style.fontStyle = 'italic';
        tier3Container.appendChild(moreElement);
    }
}

function updateTierCitiesList(tier) {
    const tierCitiesList = document.getElementById('tier-cities-list');
    tierCitiesList.innerHTML = '';
    
    // Create a 3-column grid for cities
    const citiesPerColumn = Math.ceil(INDIA_CITIES[tier].length / 3);
    
    for (let i = 0; i < 3; i++) {
        const column = document.createElement('div');
        column.className = 'cities-column';
        
        for (let j = i * citiesPerColumn; j < (i + 1) * citiesPerColumn && j < INDIA_CITIES[tier].length; j++) {
            const cityElement = document.createElement('div');
            cityElement.textContent = `• ${INDIA_CITIES[tier][j]}`;
            column.appendChild(cityElement);
        }
        
        tierCitiesList.appendChild(column);
    }
}

// Event Listeners setup
function setupEventListeners() {
    // Main navigation tabs
    setupTabNavigation();
    
    // Single city tab
    setupSingleCityTab();
    
    // Tier-wise tab
    setupTierWiseTab();
    
    // Custom cities tab
    setupCustomCitiesTab();
    
    // Countrywide tab
    setupCountrywideTab();
    
    // Results filtering and sorting
    setupResultsControls();
    
    // Expanders (collapsible sections)
    setupExpanders();
    
    // Add back to search button functionality
    const backToSearchBtn = document.getElementById('back-to-search');
    if (backToSearchBtn) {
        backToSearchBtn.addEventListener('click', () => {
            console.log('Back to search button clicked');
            // Show search container
            const searchContainer = document.querySelector('.search-container');
            searchContainer.style.display = 'block';
            
            // Hide results section
            const resultsSection = document.getElementById('results-section');
            resultsSection.classList.add('hidden');
            
            // Scroll to top
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }
    
    // Add rating display for the range input
    const minRatingInput = document.getElementById('min-rating');
    const ratingValue = document.getElementById('rating-value');
    if (minRatingInput && ratingValue) {
        minRatingInput.addEventListener('input', () => {
            ratingValue.textContent = minRatingInput.value;
            updateAllTables();
        });
    }
    
    // Add input animation for search
    const searchInput = document.getElementById('results-search');
    if (searchInput) {
        searchInput.addEventListener('focus', () => {
            searchInput.parentElement.classList.add('focused');
        });
        
        searchInput.addEventListener('blur', () => {
            searchInput.parentElement.classList.remove('focused');
        });
    }
}

// Tab navigation
function setupTabNavigation() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Get the tab to activate
            const tabToActivate = button.getAttribute('data-tab');
            
            // Update active tab
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            button.classList.add('active');
            
            // Hide all tab content
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            // Show the active tab content
            document.getElementById(tabToActivate).classList.add('active');
            
            // Update application state
            appState.activeTab = tabToActivate;
            
            // Clear results when switching tabs
            clearSearchResults();
        });
    });
    
    // City tab navigation in custom cities tab
    const cityTabButtons = document.querySelectorAll('.city-tab-btn');
    cityTabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabToActivate = button.getAttribute('data-tab');
            
            document.querySelectorAll('.city-tab-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            button.classList.add('active');
            
            document.querySelectorAll('.city-tab-content').forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(tabToActivate).classList.add('active');
        });
    });
    
    // Result tabs for countrywide search
    const resultTabButtons = document.querySelectorAll('.results-tab-btn');
    resultTabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Get the tab to activate
            const tabToActivate = button.getAttribute('data-result-tab');
            
            // Update active tab
            document.querySelectorAll('.results-tab-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            button.classList.add('active');
            
            // Show the correct tab content
            document.querySelectorAll('.results-tab-content').forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(tabToActivate).classList.add('active');
        });
    });
}

// Setup Single City Tab
function setupSingleCityTab() {
    const cityInput = document.getElementById('city-input');
    const cityInfoContainer = document.querySelector('.city-info-container');
    
    // Handle city input change to show city tier info if it's in our list
    cityInput.addEventListener('input', () => {
        const city = cityInput.value.trim();
        
        if (city) {
            // Show city tier info if it's a known city
            let tierInfo = "";
            if (INDIA_CITIES.tier1.includes(city)) {
                tierInfo = "Tier 1 (Major Metro City)";
            } else if (INDIA_CITIES.tier2.includes(city)) {
                tierInfo = "Tier 2 (Mid-sized City)";
            } else if (INDIA_CITIES.tier3.includes(city)) {
                tierInfo = "Tier 3 (Smaller City)";
            }
            
            if (tierInfo) {
            cityInfoContainer.innerHTML = `
                <div class="info-banner">
                        ${city} - ${tierInfo}
                </div>
            `;
            } else {
                cityInfoContainer.innerHTML = '';
            }
        } else {
            cityInfoContainer.innerHTML = '';
        }
    });
    
    // Toggle specialization type in single city tab
    document.querySelectorAll('input[name="spec-type-single"]').forEach(radio => {
        radio.addEventListener('change', () => {
            if (radio.value === 'common') {
                document.querySelector('.spec-common-container').classList.remove('hidden');
                document.querySelector('.spec-custom-container').classList.add('hidden');
            } else {
                document.querySelector('.spec-common-container').classList.add('hidden');
                document.querySelector('.spec-custom-container').classList.remove('hidden');
            }
        });
    });
    
    // Search button for single city
    document.getElementById('single-city-search').addEventListener('click', () => {
        // Get city
        const city = cityInput.value.trim();
            if (!city) {
                showMessage('Please enter a city name', 'error');
                return;
        }
        
        // Get specialization
        let specialization;
        const specType = document.querySelector('input[name="spec-type-single"]:checked').value;
        if (specType === 'common') {
            specialization = document.getElementById('spec-common-single').value;
        } else {
            specialization = document.getElementById('spec-custom-single').value.trim();
            if (!specialization) {
                showMessage('Please enter a specialization', 'error');
                return;
            }
        }
        
        // Perform search
        searchDoctors({
            type: 'city',
            city: city,
            specialization: specialization
        });
    });
}

// Setup Tier-wise Tab
function setupTierWiseTab() {
    const tierSelect = document.getElementById('tier-select');
    const tierDescription = document.getElementById('tier-description');
    const tierLabel = document.getElementById('tier-label');
    const tierSearchButton = document.getElementById('tier-search');
    const tierSearchInfo = document.getElementById('tier-search-info');
    
    // Update tier information when selection changes
    tierSelect.addEventListener('change', () => {
        const tier = tierSelect.value;
        tierDescription.textContent = TIER_DESCRIPTIONS[tier];
        tierLabel.textContent = tierSelect.options[tierSelect.selectedIndex].text;
        updateTierCitiesList(tier);
        
        // Update search button text
        tierSearchButton.textContent = `Search ${tierSelect.options[tierSelect.selectedIndex].text}`;
        
        // Update estimated search time
        const cityCount = INDIA_CITIES[tier].length;
        tierSearchInfo.textContent = `Searching across ${cityCount} cities. Estimated search time: ${Math.round(cityCount / 2)}-${cityCount} minutes`;
    });
    
    // Toggle specialization type in tier-wise tab
    document.querySelectorAll('input[name="spec-type-tier"]').forEach(radio => {
        radio.addEventListener('change', () => {
            if (radio.value === 'common') {
                document.querySelector('.spec-common-container-tier').classList.remove('hidden');
                document.querySelector('.spec-custom-container-tier').classList.add('hidden');
            } else {
                document.querySelector('.spec-common-container-tier').classList.add('hidden');
                document.querySelector('.spec-custom-container-tier').classList.remove('hidden');
            }
        });
    });
    
    // Search button for tier-wise search
    tierSearchButton.addEventListener('click', () => {
        const tier = tierSelect.value;
        
        // Get specialization
        let specialization;
        const specType = document.querySelector('input[name="spec-type-tier"]:checked').value;
        if (specType === 'common') {
            specialization = document.getElementById('spec-common-tier').value;
        } else {
            specialization = document.getElementById('spec-custom-tier').value.trim();
            if (!specialization) {
                showMessage('Please enter a specialization', 'error');
                return;
            }
        }
        
        // Perform search
        searchDoctors({
            type: 'tier',
            tier: tier,
            specialization: specialization
        });
    });
}

// Setup expanders
function setupExpanders() {
    console.log('Setting up expanders...');
    const expanders = document.querySelectorAll('.expander-header');
    console.log(`Found ${expanders.length} expander headers`);
    
    expanders.forEach(expander => {
        console.log('Adding click event to expander:', expander);
        expander.addEventListener('click', (event) => {
            event.preventDefault();
            const parent = expander.parentElement;
            console.log('Toggling active class on', parent);
            parent.classList.toggle('active');
        });
    });
    
    // Also add onclick attributes directly to ensure they work
    document.querySelectorAll('.expander').forEach(expander => {
        const header = expander.querySelector('.expander-header');
        if (header) {
            header.setAttribute('onclick', "this.parentElement.classList.toggle('active')");
        }
    });
}

// API Service for backend integration
// ------------------------------------
const API = {
    // Search doctors via backend API
    async searchDoctors(params) {
        try {
            // Get base URL for API calls
            let baseUrl = BACKEND_API_URL;
            // Remove trailing slash if present
            if (baseUrl.endsWith('/')) {
                baseUrl = baseUrl.slice(0, -1);
            }
            
            let endpoint = `${baseUrl}/api/search`;
            let requestBody = {};
            
            // Build request body based on search type
            if (params.type === 'city') {
                requestBody = {
                    city: params.city,
                    specialization: params.specialization
                };
            } else if (params.type === 'tier') {
                endpoint = `${baseUrl}/api/search/tier`;
                requestBody = {
                    tier: params.tier,
                    specialization: params.specialization
                };
            } else if (params.type === 'custom') {
                endpoint = `${baseUrl}/api/search/custom`;
                requestBody = {
                    cities: params.cities,
                    specialization: params.specialization
                };
            } else if (params.type === 'countrywide') {
                endpoint = `${baseUrl}/api/search/countrywide`;
                requestBody = {
                    country: 'India',
                    specialization: params.specialization
                };
            }
            
            console.log(`Sending ${params.type} search request to: ${endpoint}`);
            console.log('Request body:', JSON.stringify(requestBody, null, 2));
            
            // Real API call
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody)
            });
            
            console.log(`API Response status: ${response.status}`);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error(`API Error: ${response.status} - ${errorText}`);
                throw new Error(`API Error: ${response.status} - ${errorText}`);
            }
            
            // Parse the response
            const rawResult = await response.text();
            console.log(`Raw response (first 200 chars): ${rawResult.substring(0, 200)}...`);
            
            const result = JSON.parse(rawResult);
            
            // Transform the API response to our expected format
            return {
                success: result.success !== false,
                data: {
                    doctors: result.data || [],
                    count: result.data ? result.data.length : 0,
                    cities_searched: result.metadata?.query?.city || 
                                  (result.metadata?.query?.cities ? result.metadata.query.cities.length : 0) ||
                                  (result.metadata?.query?.tier ? `Tier ${result.metadata.query.tier}` : 'All'),
                    duration_seconds: result.metadata?.search_duration || 0,
                    specialization: params.specialization
                },
                message: result.error
            };
        } catch (error) {
            console.error('API Error:', error);
            console.error('Error stack:', error.stack);
            throw error;
        }
    }
};

// Replace the mock search function with real implementation
function searchDoctors(searchParams) {
    console.log('Searching for doctors with params:', searchParams);
    
    // Clear previous results
    clearSearchResults();
    
    // Show loading spinner and start progress simulation
    showLoading();
    simulateSearchProgress();
    
    // Perform API call
    API.searchDoctors(searchParams)
        .then(response => {
            // Complete progress and hide loading spinner
            completeSearchProgress();
            
            // Add slight delay to show the 100% completion
            setTimeout(() => {
                hideLoading();
            
            if (response.success) {
                displaySearchResults(response.data, searchParams);
            } else {
                // Show error message
                    showNotification('Error searching for doctors: ' + (response.message || 'Unknown error'), 'error');
            }
            }, 500);
        })
        .catch(error => {
            // Stop progress simulation and hide loading if error occurs
            completeSearchProgress();
            hideLoading();
            
            console.error('Error searching for doctors:', error);
            showNotification('Error searching for doctors: ' + error.message, 'error');
        });
}

// Populate doctor table with data
function populateDoctorTable(tableId, doctors) {
    console.log(`Populating table ${tableId} with ${doctors.length} doctors`);
    const tbody = document.getElementById(tableId).querySelector('tbody');
    
    // Clear existing rows
    tbody.innerHTML = '';
    
    doctors.forEach((doctor, index) => {
        // Create row with fade-in animation
        const row = document.createElement('tr');
        row.style.animationDelay = `${index * 30}ms`;
        row.classList.add('fade-in');
        
        // Create doctor name cell
        const nameCell = document.createElement('td');
        nameCell.className = 'doctor-name';
        nameCell.innerHTML = `<div class="cell-content" title="${doctor.name}">${doctor.name}</div>`;
        row.appendChild(nameCell);
        
        // Create rating cell
        const ratingCell = document.createElement('td');
        ratingCell.className = 'doctor-rating';
        ratingCell.innerHTML = `<div class="cell-content">${getRatingStars(doctor.rating)}</div>`;
        ratingCell.setAttribute('data-rating', doctor.rating || 0);
        row.appendChild(ratingCell);
        
        // Create reviews cell
        const reviewsCell = document.createElement('td');
        reviewsCell.className = 'doctor-reviews';
        reviewsCell.innerHTML = `<div class="cell-content">${formatNumber(doctor.reviews || 0)}</div>`;
        reviewsCell.setAttribute('data-reviews', doctor.reviews || 0);
        row.appendChild(reviewsCell);
        
        // Create locations cell with truncation
        const locationsCell = document.createElement('td');
        locationsCell.className = 'doctor-locations';
        locationsCell.innerHTML = formatLocations(doctor.locations || []);
        row.appendChild(locationsCell);
        
        // Create city cell
        const cityCell = document.createElement('td');
        cityCell.className = 'doctor-city';
        cityCell.innerHTML = `<div class="cell-content" title="${doctor.city}">${doctor.city || 'N/A'}</div>`;
        row.appendChild(cityCell);
        
        // Create sources cell
        const sourcesCell = document.createElement('td');
        sourcesCell.className = 'doctor-sources';
        sourcesCell.innerHTML = formatSources(doctor.contributing_sources || []);
        row.appendChild(sourcesCell);
        
        // Add the row to the table
        tbody.appendChild(row);
    });
    
    // Add no results message if needed
    if (doctors.length === 0) {
        const noResultsRow = document.createElement('tr');
        const noResultsCell = document.createElement('td');
        noResultsCell.colSpan = 6;
        noResultsCell.textContent = 'No doctors found matching your criteria.';
        noResultsCell.className = 'no-results';
        noResultsRow.appendChild(noResultsCell);
        tbody.appendChild(noResultsRow);
    }
    
    console.log(`Populated ${doctors.length} rows in table ${tableId}`);
}

// Format locations to display nicely in a cell with dropdown for multiple locations
function formatLocations(locations) {
    if (!locations || locations.length === 0) {
        return '<span class="location-unknown">No location data available</span>';
    }
    
    // Format the primary location with title for tooltip
    const primaryLocation = locations[0];
    let html = `<div class="primary-location" title="${primaryLocation}">
                  <i class="material-icons">place</i> ${primaryLocation}
                </div>`;
    
    // If there are additional locations, add a dropdown
    if (locations.length > 1) {
        const remainingLocations = locations.slice(1);
        const locationCount = remainingLocations.length;
        
        html += `<div class="location-dropdown">
                  <span class="location-count" onclick="toggleLocationDropdown(this)">
                    <i class="material-icons">add_circle</i> ${locationCount} more
                  </span>
                  <div class="location-dropdown-content">
                    <div class="dropdown-header">All Locations (${locations.length})</div>`;
        
        // Add all locations to the dropdown with numbering
        locations.forEach((location, index) => {
            html += `<div class="location-item" title="${location}"><i class="material-icons">place</i> ${location}</div>`;
        });
        
        html += `</div></div>`;
    }
    
    return html;
}

// Format sources to display as color-coded tags with better layout
function formatSources(sources) {
    // If sources not provided or empty, return unknown tag
    if (!sources || sources.length === 0) {
        return '<span class="source-tag source-unknown" title="No known source"><i class="material-icons">help_outline</i> Unknown</span>';
    }
    
    // Normalize and filter unique sources
    const uniqueSources = Array.from(new Set(sources.map(s => 
        typeof s === 'string' ? s.trim().toLowerCase() : 'unknown'
    )));
    
    // Define color mapping for different sources with improved styling
    const sourceMapping = {
        'practo': { color: '#13b2b8', icon: 'local_hospital', name: 'Practo' },
        'justdial': { color: '#f95a2b', icon: 'call', name: 'JustDial' },
        'general': { color: '#4285F4', icon: 'search', name: 'General' },
        'hospital': { color: '#34a853', icon: 'local_hospital', name: 'Hospital' },
        'social': { color: '#fbbc05', icon: 'people', name: 'Social' },
        'unknown': { color: '#9e9e9e', icon: 'help_outline', name: 'Unknown' }
    };
    
    // Limit to max 2 sources to prevent overflow
    const maxSourcesToShow = 2;
    const visibleSources = uniqueSources.slice(0, maxSourcesToShow);
    const hiddenCount = Math.max(0, uniqueSources.length - maxSourcesToShow);
    
    // Format each source tag with color and icon - improved style
    let sourceTags = visibleSources.map(source => {
        // Find the best matching source mapping
        const mapping = Object.keys(sourceMapping).find(key => 
            source === key || source.includes(key)
        ) || 'unknown';
        
        const sourceInfo = sourceMapping[mapping];
        
        return `<span class="source-tag" 
                     style="background-color: ${sourceInfo.color}; color: white;" 
                     title="${source}">
                   <i class="material-icons">${sourceInfo.icon}</i> ${sourceInfo.name}
               </span>`;
    }).join('');
    
    // Add "more" tag if there are additional sources
    if (hiddenCount > 0) {
        const hiddenSources = uniqueSources.slice(maxSourcesToShow);
        const hiddenSourcesTitle = hiddenSources.join(', ');
        
        sourceTags += `<span class="source-tag source-more" 
                             title="${hiddenSourcesTitle}">
                         <i class="material-icons">add</i> ${hiddenCount}
                     </span>`;
    }
    
    return sourceTags;
}

// Improved rating stars display with clearer indicators
function getRatingStars(rating) {
    // Return "Not Rated" for falsy values (0, null, undefined)
    if (!rating) return '<span class="no-rating">Not Rated</span>';
    
    // Convert rating to number and validate
    rating = parseFloat(rating);
    if (isNaN(rating)) return '<span class="no-rating">Invalid Rating</span>';
    
    // Clamp rating between 0 and 5
    rating = Math.max(0, Math.min(5, rating));
    
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 >= 0.3; // Lower threshold to show half stars
    let starsHTML = '<div class="stars-container">';
    
    // Add full stars
    for (let i = 0; i < fullStars; i++) {
        starsHTML += '<i class="material-icons star-filled">star</i>';
    }
    
    // Add half star if needed
    if (hasHalfStar) {
        starsHTML += '<i class="material-icons star-half">star_half</i>';
    }
    
    // Add empty stars to always show 5 stars total
    const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);
    for (let i = 0; i < emptyStars; i++) {
        starsHTML += '<i class="material-icons star-empty">star_border</i>';
    }
    
    starsHTML += '</div>';
    
    // Add numeric rating with improved styling
    starsHTML += `<span class="numeric-rating">${rating.toFixed(1)}</span>`;
    
    return starsHTML;
}

// Add a verification function to ensure tables are correctly populated
function verifyTablesPopulated() {
    console.log('Verifying table is populated...');
    
    const tableId = 'doctors-table';
    const table = document.getElementById(tableId);
    
    if (!table) {
        console.error(`Table ${tableId} not found in the DOM!`);
        return;
    }
    
    const tbody = table.querySelector('tbody');
    if (!tbody) {
        console.error(`Table ${tableId} has no tbody element!`);
        return;
    }
    
    const rows = tbody.querySelectorAll('tr');
    console.log(`Table ${tableId} has ${rows.length} rows`);
    
    // Show/hide no results message
    const container = document.getElementById('doctors-section');
    if (container) {
        const noResultsMsg = container.querySelector('.no-results-message');
        if (noResultsMsg) {
            console.log(`Setting no-results-message for ${tableId} to ${rows.length === 0 ? 'visible' : 'hidden'}`);
            noResultsMsg.classList.toggle('hidden', rows.length > 0);
        } else {
            console.error(`No results message element not found for ${tableId}`);
        }
    } else {
        console.error(`Container not found for ${tableId}`);
    }
    
    console.log('Table verification complete');
}

// Toggle location dropdown visibility
function toggleLocationDropdown(element) {
    // Find the dropdown content element more reliably
    // First, find the parent location-dropdown container
    const dropdownContainer = element.closest('.location-dropdown');
    if (!dropdownContainer) {
        console.error('Location dropdown container not found');
        return;
    }
    
    // Then find the dropdown content within this container
    const dropdown = dropdownContainer.querySelector('.location-dropdown-content');
    if (!dropdown) {
        console.error('Location dropdown content not found');
        return;
    }
    
    // Close any open dropdowns first
    document.querySelectorAll('.location-dropdown-content.visible').forEach(openDropdown => {
        if (openDropdown !== dropdown) {
            openDropdown.classList.remove('visible');
        }
    });
    
    // Toggle this dropdown
    dropdown.classList.toggle('visible');
    
    // Position the dropdown correctly
    const rect = element.getBoundingClientRect();
    const tableRect = document.querySelector('.doctors-table').getBoundingClientRect();
    
    // Handle positioning so it doesn't go off screen
    if (rect.left + dropdown.offsetWidth > window.innerWidth) {
        dropdown.style.left = 'auto';
        dropdown.style.right = '0';
    } else {
        dropdown.style.left = '0';
        dropdown.style.right = 'auto';
    }
    
    // Close when clicking outside
    function closeDropdown(e) {
        // Only close if clicking outside the dropdown and the toggle element
        if (!dropdown.contains(e.target) && !element.contains(e.target)) {
            dropdown.classList.remove('visible');
            document.removeEventListener('click', closeDropdown);
        }
    }
    
    // Add event listener to detect clicks outside
    // Use setTimeout to avoid the current click event from immediately closing the dropdown
    setTimeout(() => {
        document.addEventListener('click', closeDropdown);
    }, 0);
}

// Enhanced display search results function with better table interactions
function displaySearchResults(data, searchParams) {
    console.log('Displaying search results:', data);
    console.log('Doctor count from API:', data.count);
    console.log('Doctors array length:', data.doctors ? data.doctors.length : 0);
    
    // Validate doctors data
    if (!data.doctors || !Array.isArray(data.doctors)) {
        console.error('Invalid doctors data - expected array but got:', typeof data.doctors);
        showMessage('Error: Invalid data received from server', 'error');
        return;
    }
    
    if (data.doctors.length === 0) {
        console.warn('Doctors array is empty even though count is:', data.count);
    } else {
        console.log('First doctor sample:', data.doctors[0]);
    }
    
    // Get the results section
    const resultsSection = document.getElementById('results-section');
    if (!resultsSection) {
        console.error('Results section not found in the DOM!');
        return;
    }
    
    // Make sure results section is visible and not hidden
    resultsSection.classList.remove('hidden');
    resultsSection.style.display = 'block';
    console.log('Results section display:', resultsSection.style.display);
    console.log('Results section classes:', resultsSection.className);
    
    // Set correct title based on search type
    const resultsTitle = document.getElementById('results-title');
    if (resultsTitle) {
        if (searchParams.type === 'city') {
            resultsTitle.textContent = `Top ${data.specialization} in ${searchParams.city}`;
        } else if (searchParams.type === 'tier') {
            resultsTitle.textContent = `Top ${data.specialization} in Tier ${searchParams.tier.slice(-1)} Cities`;
        } else if (searchParams.type === 'custom') {
            resultsTitle.textContent = `Top ${data.specialization} in Selected Cities`;
        } else if (searchParams.type === 'countrywide') {
            resultsTitle.textContent = `Top ${data.specialization} Across India`;
        }
    } else {
        console.error('Results title element not found!');
    }
    
    // Update search metadata
    const searchCountEl = document.getElementById('search-count');
    const searchLocationEl = document.getElementById('search-location');
    const searchSpecializationEl = document.getElementById('search-specialization');
    const searchTimeEl = document.getElementById('search-time');
    
    if (searchCountEl) searchCountEl.textContent = data.count;
    if (searchLocationEl) searchLocationEl.textContent = typeof data.cities_searched === 'number' ? 
        `${data.cities_searched} cities` : data.cities_searched;
    if (searchSpecializationEl) searchSpecializationEl.textContent = data.specialization;
    if (searchTimeEl) searchTimeEl.textContent = `${data.duration_seconds.toFixed(2)} seconds`;
    
    // Get the doctors table
    const doctorsTable = document.getElementById('doctors-table');
    if (!doctorsTable) {
        console.error('Doctors table not found in the DOM!');
        return;
    }
    
    // Clear existing table content
    const tableBody = doctorsTable.querySelector('tbody');
    if (tableBody) {
        tableBody.innerHTML = '';
        console.log('Cleared table body');
    } else {
        console.error('Doctors table body not found!');
        return;
    }
    
    // Sort doctors by rating and reviews (highest first)
    const sortedDoctors = [...data.doctors].sort((a, b) => {
        if (b.rating !== a.rating) {
            return b.rating - a.rating;
        }
        return b.reviews - a.reviews;
    });
    
    console.log(`Total doctors after sorting: ${sortedDoctors.length}`);
    
    // Populate the table with all doctors
    populateDoctorTable('doctors-table', sortedDoctors);
    
    // Show/hide no results message
    const noResultsMsg = document.querySelector('#doctors-section .no-results-message');
    if (noResultsMsg) {
        console.log(`Setting no-results-message to ${sortedDoctors.length === 0 ? 'visible' : 'hidden'}`);
        noResultsMsg.classList.toggle('hidden', sortedDoctors.length > 0);
    } else {
        console.error('No results message element not found!');
    }
    
    // Add table interactions after a small delay to ensure table is populated
    setTimeout(() => {
        addTableInteractions();
    }, 600);
    
    // Ensure the table has visible data
    verifyTablesPopulated();
    
    // Fade in results with a slight delay
    resultsSection.style.opacity = '0';
    setTimeout(() => {
        resultsSection.style.transition = 'opacity 0.5s ease';
        resultsSection.style.opacity = '1';
        console.log('Fading in results section, opacity:', resultsSection.style.opacity);
        
        // Scroll to results section after fade-in
        setTimeout(() => {
            resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 300);
    }, 200);
    
    // Apply initial filtering and sorting
    setTimeout(() => {
        const sortBySelect = document.getElementById('sort-by');
        if (sortBySelect) {
            // Trigger change event to apply sorting
            const event = new Event('change');
            sortBySelect.dispatchEvent(event);
        }
    }, 500);
    
    // Hide the search container to give more focus to results
    const searchContainer = document.querySelector('.search-container');
    if (searchContainer) {
        searchContainer.style.display = 'none';
        console.log('Hiding search container, display:', searchContainer.style.display);
    } else {
        console.error('Search container not found!');
    }
    
    // Show success message
    if (data.count > 0) {
        showMessage(`Found ${data.count} doctors matching your search criteria!`, 'success');
    } else {
        showMessage('No doctors found. Try a different specialization or location.', 'warning');
    }
}

// Add event listeners for table interactions after rendering
function addTableInteractions() {
    // Add row hover effect for all tables
    document.querySelectorAll('.doctors-table tbody tr').forEach(row => {
        // Add tooltips for long content
        const nameCell = row.querySelector('td:first-child');
        if (nameCell) {
            const doctorName = nameCell.querySelector('.doctor-name');
            if (doctorName && doctorName.offsetWidth < doctorName.scrollWidth) {
                // Create tooltip only if text is truncated
                const tooltip = document.createElement('div');
                tooltip.className = 'doctor-name-tooltip';
                tooltip.textContent = doctorName.textContent;
                nameCell.appendChild(tooltip);
            }
        }
        
        // Add animation for location dropdown
        const locationDropdown = row.querySelector('.location-dropdown');
        if (locationDropdown) {
            const locationCount = locationDropdown.querySelector('.location-count');
            const dropdownContent = locationDropdown.querySelector('.location-dropdown-content');
            
            locationCount.addEventListener('click', (e) => {
                e.stopPropagation();
                dropdownContent.classList.toggle('visible');
                
                // Close other open dropdowns
                document.querySelectorAll('.location-dropdown-content.visible').forEach(content => {
                    if (content !== dropdownContent) {
                        content.classList.remove('visible');
                    }
                });
            });
        }
    });
    
    // Close location dropdowns when clicking elsewhere
    document.addEventListener('click', () => {
        document.querySelectorAll('.location-dropdown-content.visible').forEach(dropdown => {
            dropdown.classList.remove('visible');
        });
    });
}

// Update the export button to use the actual export function
function setupExportButton() {
    const exportButton = document.getElementById('export-excel');
    
    if (!exportButton) {
        console.error('Export button not found in the DOM');
        return;
    }
    
    console.log('Setting up export button');
    
    exportButton.addEventListener('click', function(event) {
        event.preventDefault();
        try {
            console.log('Export button clicked');
            
            // Verify the XLSX library is available
            if (typeof XLSX === 'undefined') {
                throw new Error('XLSX library not loaded. Make sure you have included the SheetJS library.');
            }
            
            // Get the table ID
            const tableId = 'doctors-table';
            const table = document.getElementById(tableId);
            if (!table) {
                throw new Error(`Table ${tableId} not found in the DOM`);
            }
            
            // Check that there's data to export
            const rows = table.querySelectorAll('tbody tr:not(.no-results)');
            if (rows.length === 0) {
                showMessage('No data to export', 'warning');
                return;
            }
            
            // Get results title for file name
            const resultsTitle = document.getElementById('results-title').textContent;
            const safeTitle = resultsTitle.replace(/[^a-z0-9]/gi, '_').toLowerCase();
            const date = new Date().toISOString().split('T')[0];
            const fileName = `${safeTitle}_${date}.xlsx`;
            
            // Call the actual export function
            exportToExcel(tableId, fileName);
            
        } catch (error) {
            console.error('Error exporting to Excel:', error);
            showMessage('Error exporting to Excel: ' + error.message, 'error');
        }
    });
}

// Make sure BackToSearch button is also properly set up
function setupBackToSearchButton() {
    const backToSearchBtn = document.getElementById('back-to-search');
    
    if (!backToSearchBtn) {
        console.error('Back to search button not found in the DOM');
        return;
    }
    
    console.log('Setting up back to search button');
    
    backToSearchBtn.addEventListener('click', function() {
        console.log('Back to search button clicked');
        
        // Show search container
        const searchContainer = document.querySelector('.search-container');
        if (searchContainer) {
            searchContainer.style.display = 'block';
        } else {
            console.error('Search container not found');
        }
        
        // Hide results section
        const resultsSection = document.getElementById('results-section');
        if (resultsSection) {
            resultsSection.classList.add('hidden');
            resultsSection.style.opacity = '0';
        } else {
            console.error('Results section not found');
        }
        
        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
}

// Add tooltips to UI elements
function addTooltips() {
    // Add tooltip to export button
    const exportButton = document.getElementById('export-excel');
    exportButton.classList.add('tooltip');
    const exportTooltip = document.createElement('span');
    exportTooltip.className = 'tooltip-text';
    exportTooltip.textContent = 'Export results to Excel spreadsheet (XLSX)';
    exportButton.appendChild(exportTooltip);
    
    // Add tooltips to rating slider
    const ratingSlider = document.getElementById('min-rating');
    const ratingContainer = ratingSlider.parentElement;
    ratingContainer.classList.add('tooltip');
    const ratingTooltip = document.createElement('span');
    ratingTooltip.className = 'tooltip-text';
    ratingTooltip.textContent = 'Filter doctors by minimum rating';
    ratingContainer.appendChild(ratingTooltip);
    
    // Add tooltips to search filter
    const searchFilter = document.getElementById('results-search');
    const searchContainer = searchFilter.parentElement;
    searchContainer.classList.add('tooltip');
    const searchTooltip = document.createElement('span');
    searchTooltip.className = 'tooltip-text';
    searchTooltip.textContent = 'Search for doctors by name or location';
    searchContainer.appendChild(searchTooltip);
}

// Add function to clear search results
function clearSearchResults() {
    console.log('Clearing search results...');
    
    // Hide results section
    const resultsSection = document.getElementById('results-section');
    if (resultsSection) {
        resultsSection.classList.add('hidden');
        resultsSection.style.opacity = '0';
    }
    
    // Show search container
    const searchContainer = document.querySelector('.search-container');
    if (searchContainer) {
        searchContainer.style.display = 'block';
    }
    
    // Reset table contents
    const tableIds = ['top-doctors-table', 'other-doctors-table'];
    tableIds.forEach(tableId => {
        const tbody = document.getElementById(tableId)?.querySelector('tbody');
        if (tbody) {
            tbody.innerHTML = '';
            console.log(`Cleared table: ${tableId}`);
        }
    });
    
    // Reset counts
    const elements = [
        'search-count',
        'search-location',
        'search-specialization',
        'search-time',
        'top-doctors-count',
        'other-doctors-count'
    ];
    
    elements.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = id.includes('count') ? '0' : '-';
            console.log(`Reset element: ${id}`);
        }
    });
    
    console.log('Search results cleared');
}

// Function to show loading state
function showLoading() {
    console.log('Showing loading overlay...');
    // Show loading overlay
    const loadingContainer = document.querySelector('.loading-container');
    if (loadingContainer) {
        console.log('Loading container found, displaying...');
        loadingContainer.style.display = 'flex';
        loadingContainer.style.opacity = '0';
        setTimeout(() => {
            loadingContainer.style.opacity = '1';
        }, 10);
    } else {
        console.error('Loading container not found!');
    }
    
    // Disable buttons to prevent multiple requests
    const buttons = document.querySelectorAll('button');
    buttons.forEach(button => {
        button.disabled = true;
        button.style.cursor = 'not-allowed';
    });
    
    console.log('Setting search in progress flag...');
    appState.searchInProgress = true;
}

// Function to hide loading state
function hideLoading() {
    console.log('Hiding loading overlay...');
    // Hide loading overlay with fade effect
    const loadingContainer = document.querySelector('.loading-container');
    if (loadingContainer) {
        console.log('Loading container found, hiding...');
        loadingContainer.style.opacity = '0';
        setTimeout(() => {
            loadingContainer.style.display = 'none';
        }, 300);
    } else {
        console.error('Loading container not found!');
    }
    
    // Re-enable buttons
    const buttons = document.querySelectorAll('button');
    buttons.forEach(button => {
        button.disabled = false;
        button.style.cursor = 'pointer';
    });
    
    console.log('Clearing search in progress flag...');
    appState.searchInProgress = false;
}

// Function to show notification with more modern styling
function showNotification(message, type = 'info') {
    // Remove any existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => {
        notification.remove();
    });
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    // Icon based on type
    let icon = 'info';
    if (type === 'success') icon = 'check_circle';
    if (type === 'error') icon = 'error';
    if (type === 'warning') icon = 'warning';
    
    notification.innerHTML = `
        <i class="material-icons">${icon}</i>
        <span>${message}</span>
    `;
    
    // Append to body
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.style.transform = 'translateY(0)';
        notification.style.opacity = '1';
    }, 10);
    
    // Auto-remove after delay
    setTimeout(() => {
        notification.style.transform = 'translateY(-20px)';
        notification.style.opacity = '0';
        
        // Remove from DOM after animation completes
        setTimeout(() => {
            notification.remove();
        }, 500);
    }, 5000);
}

// Add a back to top button functionality
function addBackToTopButton() {
    // Create the button
    const backToTopBtn = document.createElement('div');
    backToTopBtn.className = 'back-to-top';
    backToTopBtn.innerHTML = '<i class="material-icons">arrow_upward</i>';
    document.body.appendChild(backToTopBtn);
    
    // Show/hide button based on scroll position
    window.addEventListener('scroll', () => {
        if (window.pageYOffset > 300) {
            backToTopBtn.classList.add('visible');
        } else {
            backToTopBtn.classList.remove('visible');
        }
    });
    
    // Scroll to top when clicked
    backToTopBtn.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

// Add polished loading indicators to tables during filtering/sorting
function addTableLoadingEffects() {
    const tables = document.querySelectorAll('.doctors-table');
    tables.forEach(table => {
        const tbody = table.querySelector('tbody');
        
        // Create a loading overlay
        const loadingOverlay = document.createElement('div');
        loadingOverlay.className = 'table-loading-overlay';
        loadingOverlay.innerHTML = `
            <div class="table-loading-spinner"></div>
            <p>Updating results...</p>
        `;
        
        table.parentElement.style.position = 'relative';
        table.parentElement.appendChild(loadingOverlay);
        
        // Show overlay during table operations
        table.addEventListener('table-update-start', () => {
            loadingOverlay.classList.add('visible');
        });
        
        table.addEventListener('table-update-end', () => {
            loadingOverlay.classList.remove('visible');
        });
    });
}

// Setup Custom Cities Tab
function setupCustomCitiesTab() {
    // Quick selection radio buttons
    const quickRadios = document.querySelectorAll('input[name="quick-cities"]');
    const quickSelectionInfo = document.getElementById('quick-selection-info');
    const customSelectionContainer = document.getElementById('custom-selection-container');
    const cityCheckboxes = document.querySelectorAll('input[name="city"]');
    const customSelectionSummary = document.getElementById('custom-selection-summary');
    const continueButton = document.getElementById('cities-continue');
    
    // Handle quick selection changes
    quickRadios.forEach(radio => {
        radio.addEventListener('change', () => {
            if (radio.value === 'custom') {
                // Show custom selection
                customSelectionContainer.classList.remove('hidden');
                quickSelectionInfo.classList.add('hidden');
                
                // Update selected cities from checkboxes
                updateSelectedCitiesFromCheckboxes();
            } else {
                // Hide custom selection and show preset
                customSelectionContainer.classList.add('hidden');
                quickSelectionInfo.classList.remove('hidden');
                
                // Set preselected cities
                appState.selectedCities = [...QUICK_CITY_SELECTIONS[radio.value]];
                
                // Show info message
                quickSelectionInfo.textContent = `Selected ${appState.selectedCities.length} cities: ${appState.selectedCities.join(', ')}`;
                
                // Enable continue button
                continueButton.disabled = false;
            }
        });
    });
    
    // Handle city checkbox changes
    cityCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', () => {
            updateSelectedCitiesFromCheckboxes();
        });
    });
    
    // Continue to step 2 button
    continueButton.addEventListener('click', () => {
        goToWizardStep(2);
        
        // Update cities summary
        const citiesSummary = document.getElementById('selected-cities-summary');
        if (appState.selectedCities.length > 5) {
            citiesSummary.textContent = `Selected ${appState.selectedCities.length} cities: ${appState.selectedCities.slice(0, 5).join(', ')} and ${appState.selectedCities.length - 5} more`;
        } else {
            citiesSummary.textContent = `Selected cities: ${appState.selectedCities.join(', ')}`;
        }
    });
    
    // Back to cities button
    document.getElementById('back-to-cities').addEventListener('click', () => {
        goToWizardStep(1);
    });
    
    // Toggle specialization type in custom cities tab
    document.querySelectorAll('input[name="spec-type-custom"]').forEach(radio => {
        radio.addEventListener('change', () => {
            if (radio.value === 'common') {
                document.querySelector('.spec-common-container-custom').classList.remove('hidden');
                document.querySelector('.spec-custom-container-custom').classList.add('hidden');
                
                // Enable continue if a specialization is selected
                document.getElementById('continue-to-review').disabled = false;
                appState.selectedSpecialization = document.getElementById('spec-common-custom').value;
            } else {
                document.querySelector('.spec-common-container-custom').classList.add('hidden');
                document.querySelector('.spec-custom-container-custom').classList.remove('hidden');
                
                // Check if custom specialization has value
                const customSpecValue = document.getElementById('spec-custom-custom').value.trim();
                document.getElementById('continue-to-review').disabled = !customSpecValue;
                
                if (customSpecValue) {
                    appState.selectedSpecialization = customSpecValue;
                }
            }
        });
    });
    
    // Handle custom specialization input
    document.getElementById('spec-custom-custom').addEventListener('input', (e) => {
        document.getElementById('continue-to-review').disabled = !e.target.value.trim();
        if (e.target.value.trim()) {
            appState.selectedSpecialization = e.target.value.trim();
        }
    });
    
    // Continue to review button
    document.getElementById('continue-to-review').addEventListener('click', () => {
        goToWizardStep(3);
        
        // Update summary
        document.getElementById('summary-cities').textContent = appState.selectedCities.length > 5 ? 
            `${appState.selectedCities.slice(0, 5).join(', ')} and ${appState.selectedCities.length - 5} more` :
            appState.selectedCities.join(', ');
        
        document.getElementById('summary-cities-count').textContent = appState.selectedCities.length;
        document.getElementById('summary-specialization').textContent = appState.selectedSpecialization;
        document.getElementById('summary-search-time').textContent = `${Math.round(appState.selectedCities.length / 2)}-${appState.selectedCities.length} minutes`;
    });
    
    // Edit search button
    document.getElementById('edit-search').addEventListener('click', () => {
        goToWizardStep(1);
    });
    
    // Start custom search button
    document.getElementById('start-custom-search').addEventListener('click', () => {
        searchDoctors({
            type: 'custom',
            cities: appState.selectedCities,
            specialization: appState.selectedSpecialization
        });
    });
    
    // Helper function to update selected cities from checkboxes
    function updateSelectedCitiesFromCheckboxes() {
        const selectedCities = [];
        document.querySelectorAll('input[name="city"]:checked').forEach(checkbox => {
            selectedCities.push(checkbox.value);
        });
        
        appState.selectedCities = selectedCities;
        
        // Update summary and button state
        if (selectedCities.length > 0) {
            customSelectionSummary.classList.remove('hidden');
            customSelectionSummary.textContent = `You've selected ${selectedCities.length} cities for search`;
            continueButton.disabled = false;
        } else {
            customSelectionSummary.classList.add('hidden');
            continueButton.disabled = true;
        }
    }
    
    // Helper function to go to a specific wizard step
    function goToWizardStep(step) {
        // Update progress steps
        document.querySelectorAll('.progress-step').forEach(stepEl => {
            const stepNum = parseInt(stepEl.getAttribute('data-step'));
            stepEl.classList.remove('active', 'completed');
            
            if (stepNum === step) {
                stepEl.classList.add('active');
            } else if (stepNum < step) {
                stepEl.classList.add('completed');
            }
        });
        
        // Show the correct step content
        document.querySelectorAll('.wizard-step').forEach(content => {
            content.classList.remove('active');
        });
        document.querySelector(`.wizard-step[data-step="${step}"]`).classList.add('active');
        
        // Update app state
        appState.wizardStep = step;
    }
}

// Setup Countrywide Tab
function setupCountrywideTab() {
    // Toggle specialization type in countrywide tab
    document.querySelectorAll('input[name="spec-type-country"]').forEach(radio => {
        radio.addEventListener('change', () => {
            if (radio.value === 'common') {
                document.querySelector('.spec-common-container-country').classList.remove('hidden');
                document.querySelector('.spec-custom-container-country').classList.add('hidden');
            } else {
                document.querySelector('.spec-common-container-country').classList.add('hidden');
                document.querySelector('.spec-custom-container-country').classList.remove('hidden');
            }
        });
    });
    
    // Search button for countrywide search
    document.getElementById('country-search').addEventListener('click', () => {
        // Get specialization
        let specialization;
        const specType = document.querySelector('input[name="spec-type-country"]:checked').value;
        if (specType === 'common') {
            specialization = document.getElementById('spec-common-country').value;
        } else {
            specialization = document.getElementById('spec-custom-country').value.trim();
            if (!specialization) {
                showMessage('Please enter a specialization', 'error');
                return;
            }
        }
        
        // Perform search
        searchDoctors({
            type: 'countrywide',
            country: 'India',
            specialization: specialization
        });
    });
}

// Setup Results Controls (filtering and sorting)
function setupResultsControls() {
    const searchInput = document.getElementById('results-search');
    const ratingSlider = document.getElementById('min-rating');
    const ratingValue = document.getElementById('rating-value');
    const sortBySelect = document.getElementById('sort-by');
    
    // Filter function for tables
    function filterTable(tableId) {
        console.log(`Filtering table ${tableId}`);
        const table = document.getElementById(tableId);
        if (!table) {
            console.error(`Table ${tableId} not found for filtering`);
            return;
        }
        
        const tbody = table.querySelector('tbody');
        const rows = tbody.querySelectorAll('tr');
        console.log(`Found ${rows.length} rows to filter`);
        
        // Get filter values
        const searchTerm = searchInput.value.toLowerCase();
        const minRating = parseFloat(ratingSlider.value);
        console.log(`Filter values: searchTerm="${searchTerm}", minRating=${minRating}`);
        
        // Apply filters to each row
        let visibleRows = 0;
        rows.forEach(row => {
            // Skip no-results rows
            if (row.classList.contains('no-results')) return;
            
            // Read data from cells, properly handling nested content
            const nameCell = row.querySelector('.doctor-name .cell-content');
            const name = nameCell ? nameCell.textContent.toLowerCase() : '';
            
            // Use data attribute for rating instead of text content
            const rating = parseFloat(row.querySelector('.doctor-rating').getAttribute('data-rating') || 0);
            
            const locationsCell = row.querySelector('.doctor-locations');
            const locations = locationsCell ? locationsCell.textContent.toLowerCase() : '';
            
            const cityCell = row.querySelector('.doctor-city .cell-content');
            const city = cityCell ? cityCell.textContent.toLowerCase() : '';
            
            // Check if row matches search and rating filters
            const matchesSearch = !searchTerm || 
                name.includes(searchTerm) || 
                locations.includes(searchTerm) || 
                city.includes(searchTerm);
            
            const matchesRating = isNaN(rating) || rating >= minRating;
            
            if (matchesSearch && matchesRating) {
                row.style.display = '';
                visibleRows++;
                console.log(`Row matching filters: ${name}, rating=${rating}`);
            } else {
                row.style.display = 'none';
            }
        });
        
        console.log(`Visible rows after filtering: ${visibleRows}`);
        
        // Show/hide no results message in the container, not just the table parent
        const container = document.getElementById('doctors-section');
        if (container) {
            const noResultsMsg = container.querySelector('.no-results-message');
            if (noResultsMsg) {
                if (visibleRows === 0 && rows.length > 0) {
                    console.log('Showing no-results message');
                    noResultsMsg.classList.remove('hidden');
                } else {
                    console.log('Hiding no-results message');
                    noResultsMsg.classList.add('hidden');
                }
            }
        }
        
        return visibleRows;
    }
    
    // Sort function for tables
    function sortTable(tableId) {
        console.log(`Sorting table ${tableId}`);
        const table = document.getElementById(tableId);
        if (!table) {
            console.error(`Table ${tableId} not found for sorting`);
            return;
        }
        
        const tbody = table.querySelector('tbody');
        if (!tbody) {
            console.error(`Table body not found in ${tableId}`);
            return;
        }
        
        // Only sort actual rows (skip the no-results row if present)
        const rows = Array.from(tbody.querySelectorAll('tr:not(.no-results)'));
        if (rows.length === 0) {
            console.log(`No rows to sort in table ${tableId}`);
            return;
        }
        
        console.log(`Sorting ${rows.length} rows in table ${tableId}`);
        
        // Get sort value
        const sortBy = sortBySelect.value;
        console.log(`Sort by: ${sortBy}`);
        
        // Sort rows based on data attributes where appropriate
        rows.sort((a, b) => {
            let valueA, valueB;
            
            if (sortBy === 'rating') {
                // Use data-rating attribute instead of text content
                valueA = parseFloat(a.querySelector('.doctor-rating').getAttribute('data-rating') || 0);
                valueB = parseFloat(b.querySelector('.doctor-rating').getAttribute('data-rating') || 0);
                console.log(`Comparing ratings: ${valueA} vs ${valueB}`);
                return valueB - valueA; // Descending
            } else if (sortBy === 'reviews') {
                // Use data-reviews attribute instead of text content
                valueA = parseInt(a.querySelector('.doctor-reviews').getAttribute('data-reviews') || 0);
                valueB = parseInt(b.querySelector('.doctor-reviews').getAttribute('data-reviews') || 0);
                console.log(`Comparing reviews: ${valueA} vs ${valueB}`);
                return valueB - valueA; // Descending
            } else if (sortBy === 'name') {
                valueA = a.querySelector('.doctor-name .cell-content').textContent.toLowerCase();
                valueB = b.querySelector('.doctor-name .cell-content').textContent.toLowerCase();
                return valueA.localeCompare(valueB); // Ascending
            } else if (sortBy === 'city') {
                valueA = a.querySelector('.doctor-city .cell-content').textContent.toLowerCase();
                valueB = b.querySelector('.doctor-city .cell-content').textContent.toLowerCase();
                return valueA.localeCompare(valueB); // Ascending
            }
            
            return 0;
        });
        
        // Reinsert rows in new order
        rows.forEach(row => {
            tbody.appendChild(row);
        });
        
        console.log(`Table ${tableId} sorting complete`);
    }
    
    // Apply filters and sorting to all tables
    function updateAllTables() {
        // Update all tables
        const tableIds = ['doctors-table', 'tier1-doctors-table', 'tier2-doctors-table', 'tier3-doctors-table', 'other-doctors-table'];
        
        tableIds.forEach(tableId => {
            filterTable(tableId);
            sortTable(tableId);
        });
    }
    
    // Event listeners for filter controls
    searchInput.addEventListener('input', updateAllTables);
    
    ratingSlider.addEventListener('input', () => {
        ratingValue.textContent = ratingSlider.value;
        updateAllTables();
    });
    
    sortBySelect.addEventListener('change', updateAllTables);
    
    // Note: The export button functionality is now handled in the setupExportButton function
}

// Format number to friendly display (e.g. 1.2k for 1,200)
function formatNumber(num) {
    if (!num) return '0';
    if (num >= 1000000) {
        return `${(num / 1000000).toFixed(1)}M`;
    } else if (num >= 1000) {
        return `${(num / 1000).toFixed(1)}k`;
    }
    return num.toString();
}

// Show a user-friendly message
function showMessage(message, type = 'info') {
    console.log(`${type.toUpperCase()}: ${message}`);
    
    // Create notification element if it doesn't exist
    let notification = document.getElementById('notification');
    if (!notification) {
        notification = document.createElement('div');
        notification.id = 'notification';
        notification.className = 'notification';
        document.body.appendChild(notification);
    }
    
    // Set notification content and type
    notification.textContent = message;
    notification.className = `notification ${type}`;
    
    // Remove any existing timeouts
    if (notification.timeoutId) {
        clearTimeout(notification.timeoutId);
    }
    
    // Remove notification after 3 seconds
    notification.timeoutId = setTimeout(() => {
        if (notification && notification.parentNode) {
            notification.style.opacity = '0';
            setTimeout(() => {
                if (notification && notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }
    }, 3000);
}

// Enhanced Excel export function with proper formatting
function exportToExcel(tableId, fileName) {
    try {
        console.log(`Exporting table ${tableId} to Excel as ${fileName}`);
        showLoading();
        
        // Create a new Excel workbook
        const workbook = XLSX.utils.book_new();
        
        // Add workbook properties
        workbook.Props = {
            Title: "Doctor Search Results",
            Author: "Doctor Search App",
            CreatedDate: new Date()
        };
        
        // Get the search metadata
        const searchTitle = document.getElementById('results-title').textContent;
        const searchCount = document.getElementById('search-count').textContent;
        const searchLocation = document.getElementById('search-location').textContent;
        const searchSpecialization = document.getElementById('search-specialization').textContent;
        const searchTime = document.getElementById('search-time').textContent;
        
        // Create summary info at the top
        const summaryData = [
            ['Doctor Search Results'],
            ['Search Query:', searchTitle],
            ['Total Results:', searchCount],
            ['Location:', searchLocation],
            ['Specialization:', searchSpecialization],
            ['Search Time:', searchTime],
            ['Generated:', new Date().toLocaleString()],
            [] // Empty row as separator
        ];
        
        // Create data for the Excel sheet
        const table = document.getElementById(tableId);
        if (!table) {
            throw new Error(`Table ${tableId} not found`);
        }
        
        // Get all visible rows (filtered rows are hidden)
        const rows = Array.from(table.querySelectorAll('tbody tr')).filter(row => {
            return row.style.display !== 'none' && !row.classList.contains('no-results');
        });
        
        console.log(`Found ${rows.length} visible rows to export`);
        
        // Prepare headers
        const headers = ['Doctor Name', 'Rating', 'Reviews', 'Location', 'City', 'Sources'];
        const excelRows = [headers];
        
        // Extract data from each row
        rows.forEach(row => {
            // Get name from .doctor-name cell
            const nameCell = row.querySelector('.doctor-name .cell-content');
            const name = nameCell ? nameCell.textContent.trim() : 'N/A';
            
            // Get rating - both numeric value and stars
            const ratingCell = row.querySelector('.doctor-rating');
            const rating = ratingCell ? 
                parseFloat(ratingCell.getAttribute('data-rating') || 0).toFixed(1) : 'N/A';
            
            // Get reviews count
            const reviewsCell = row.querySelector('.doctor-reviews');
            const reviews = reviewsCell ? 
                reviewsCell.getAttribute('data-reviews') || '0' : '0';
            
            // Get primary location
            const primaryLocationEl = row.querySelector('.primary-location');
            const location = primaryLocationEl ? 
                primaryLocationEl.textContent.replace('place', '').trim() : 'N/A';
            
            // Get city
            const cityCell = row.querySelector('.doctor-city .cell-content');
            const city = cityCell ? cityCell.textContent.trim() : 'N/A';
            
            // Get sources as a comma-separated list
            const sourceElements = row.querySelectorAll('.source-tag:not(.source-more)');
            const sources = sourceElements.length > 0 ?
                Array.from(sourceElements).map(el => el.textContent.trim()).join(', ') :
                'Unknown';
            
            // Add row to the dataset
            excelRows.push([name, rating, reviews, location, city, sources]);
        });
        
        // Combine summary and data rows
        const allData = [...summaryData, ...excelRows];
        
        // Create the worksheet
        const worksheet = XLSX.utils.aoa_to_sheet(allData);
        
        // Set column widths
        const columnWidths = [
            { wch: 30 }, // Doctor Name
            { wch: 10 }, // Rating
            { wch: 10 }, // Reviews
            { wch: 40 }, // Location
            { wch: 15 }, // City
            { wch: 30 }  // Sources
        ];
        
        worksheet['!cols'] = columnWidths;
        
        // Add the worksheet to the workbook
        XLSX.utils.book_append_sheet(workbook, worksheet, "Doctors");
        
        // Generate Excel file and trigger download
        XLSX.writeFile(workbook, fileName);
        
        // Hide loading spinner
        hideLoading();
        
        // Show success message
        showMessage(`Exported ${rows.length} doctors to Excel file`, 'success');
    } catch (error) {
        console.error('Error exporting to Excel:', error);
        hideLoading();
        showMessage('Error exporting to Excel: ' + error.message, 'error');
    }
}
