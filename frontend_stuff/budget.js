// budget.js - Budget Calculator & Heatmap Logic

const API_BASE = 'http://127.0.0.1:8000';

// State
let map = null;
let markers = [];
let budgetData = null;
let buyingPower = 0;
let calculatorInputs = null; // Store user's calculator inputs

// City centers for map
const cityCenters = {
  'München': [48.137154, 11.576124],
  'Berlin': [52.520008, 13.404954],
  'Hamburg': [53.551086, 9.993682],
  'Frankfurt': [50.110924, 8.682127],
  'Köln': [50.937531, 6.960279],
  'Stuttgart': [48.775846, 9.182932],
  'Düsseldorf': [51.227741, 6.773456],
  'Nürnberg': [49.452030, 11.076750],
};

// Utility functions
const formatCurrency = (n) => n ? '€' + Math.round(n).toLocaleString('de-DE') : '€0';
const formatPercent = (n) => n ? n.toFixed(2) + '%' : '0%';

// Landing page navigation
function startBudgetCalculator() {
  const landing = document.getElementById('landingFeatures');
  const calculator = document.getElementById('budgetCalculatorApp');
  if (landing) landing.style.display = 'none';
  if (calculator) calculator.style.display = 'block';
  window.scrollTo(0, 0);
}

function backToLanding() {
  const landing = document.getElementById('landingFeatures');
  const calculator = document.getElementById('budgetCalculatorApp');
  if (landing) landing.style.display = 'block';
  if (calculator) calculator.style.display = 'none';
  window.scrollTo(0, 0);
  
  // Reset to step 1
  goToStep(1);
}

// DOM Ready
document.addEventListener('DOMContentLoaded', () => {
  // Check if we should show landing or calculator
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('mode') === 'calculator') {
    startBudgetCalculator();
  }
  
  // Attach event listeners
  const calculateBtn = document.getElementById('calculateBtn');
  const exploreBtn = document.getElementById('exploreBtn');
  const swipeBtn = document.getElementById('swipeBtn');
  
  if (calculateBtn) calculateBtn.addEventListener('click', calculateBudget);
  if (exploreBtn) exploreBtn.addEventListener('click', loadHeatmap);
  if (swipeBtn) swipeBtn.addEventListener('click', startSwipeMode);
  
  // Toggle fixed years input based on radio selection
  const fixedRadios = document.querySelectorAll('input[name="fixed"]');
  fixedRadios.forEach(radio => {
    radio.addEventListener('change', toggleFixedYearsInput);
  });
  
  // Initial state
  toggleFixedYearsInput();
});

// Show/hide fixed years input based on selection
function toggleFixedYearsInput() {
  const fixedYes = document.querySelector('input[name="fixed"][value="yes"]').checked;
  const fixedYearsGroup = document.getElementById('fixedYearsGroup');
  
  if (fixedYes) {
    fixedYearsGroup.style.display = 'block';
  } else {
    fixedYearsGroup.style.display = 'none';
  }
}

// Navigation between steps
function goToStep(step) {
  // Hide all sections
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  
  // Reset all steps
  document.querySelectorAll('.step').forEach(s => s.classList.remove('active', 'completed'));
  
  // Handle step 3 variants (3 = heatmap, '3b' = swipe)
  const stepNum = typeof step === 'string' && step.includes('b') ? 3 : step;
  
  // Mark completed steps
  for (let i = 1; i < stepNum; i++) {
    document.getElementById('step' + i).classList.add('completed');
  }
  
  // Activate current step
  if (step === '3b') {
    document.getElementById('step1').classList.add('completed');
    document.getElementById('step2').classList.add('completed');
    document.getElementById('step3b').classList.add('active');
    document.getElementById('sec3b').classList.add('active');
  } else {
    document.getElementById('step' + step).classList.add('active');
    document.getElementById('sec' + step).classList.add('active');
  }
  
  // Refresh map if going to step 3
  if (step === 3) {
    setTimeout(() => {
      if (map) map.invalidateSize();
    }, 100);
  }
}

// Loading overlay
function showLoading(text) {
  document.getElementById('loadTxt').textContent = text;
  document.getElementById('loading').classList.add('show');
}

function hideLoading() {
  document.getElementById('loading').classList.remove('show');
}

// Get form values
function getFormValues() {
  const hasFixedPeriod = document.querySelector('input[name="fixed"][value="yes"]').checked;
  const fixedYearsInput = document.getElementById('fixedYears');
  const fixedYears = parseInt(fixedYearsInput.value) || 10;
  
  const formData = {
    salary: parseFloat(document.getElementById('salary').value) || 0,
    monthly_rate: parseFloat(document.getElementById('monthlyRate').value) || 0,
    equity: parseFloat(document.getElementById('equity').value) || 0,
    city: document.getElementById('city').value,
  };
  
  // Add fixed period if user selected "Yes" with custom years
  if (hasFixedPeriod) {
    formData.fixed_period_years = fixedYears;
  }
  
  return formData;
}

// STEP 1: Calculate Budget
async function calculateBudget() {
  const payload = getFormValues();
  calculatorInputs = payload; // Store for later use
  
  showLoading('Calculating your budget...');
  
  try {
    const response = await fetch(`${API_BASE}/heatmap/budget`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const data = await response.json();
    budgetData = data.raw_response;
    buyingPower = data.buying_power;
    
    displayResults();
    goToStep(2);
    
  } catch (error) {
    console.error('Budget calculation error:', error);
    alert('Error calculating budget: ' + error.message);
  } finally {
    hideLoading();
  }
}

// STEP 2: Display Results
function displayResults() {
  const scoring = budgetData?.scoringResult || {};
  const costs = budgetData?.additionalCosts || {};
  
  // Make sure we have the data stored
  if (!calculatorInputs) {
    calculatorInputs = getFormValues();
    console.log('Stored calculator inputs from displayResults:', calculatorInputs);
  }
  if (!buyingPower && scoring.priceBuilding) {
    buyingPower = scoring.priceBuilding;
    console.log('Stored buying power from displayResults:', buyingPower);
  }
  
  // Main result
  document.getElementById('rMaxPrice').textContent = formatCurrency(scoring.priceBuilding);
  
  // Loan details
  document.getElementById('rLoan').textContent = formatCurrency(scoring.loanAmount);
  document.getElementById('rInterest').textContent = formatPercent(scoring.nominalInterest);
  document.getElementById('rEffective').textContent = formatPercent(scoring.effectiveInterest);
  document.getElementById('rMonthly').textContent = formatCurrency(scoring.monthlyPayment);
  document.getElementById('rAmort').textContent = formatPercent(scoring.amortisation);
  document.getElementById('rBank').textContent = scoring.bankDetails?.bankName || '-';
  
  // Duration
  const duration = scoring.totalDuration || {};
  const totalYears = duration.years || 0;
  const totalMonths = duration.months || 0;
  const fixedYears = scoring.fixedPeriodWanted || 10;
  
  document.getElementById('rYears').textContent = totalYears;
  document.getElementById('rDuration').textContent = `${totalYears} years, ${totalMonths} months`;
  
  // Duration bar
  const fixedPercent = totalYears > 0 ? Math.min(100, (fixedYears / totalYears) * 100) : 0;
  document.getElementById('durFill').style.width = fixedPercent + '%';
  document.getElementById('rFixed').textContent = fixedYears + ' yrs fixed';
  document.getElementById('rRemain').textContent = (totalYears - fixedYears) + ' yrs remaining';
  
  // Total payments
  document.getElementById('rTotal').textContent = formatCurrency(scoring.totalPayment);
  document.getElementById('rTotalInt').textContent = formatCurrency(scoring.totalInterestPayment);
  document.getElementById('rRemainDebt').textContent = formatCurrency(scoring.paymentLeftAfterFixedPeriod);
  
  // Additional costs
  const costPct = costs.additionalCostsPercentage || {};
  const costVal = costs.additionalCostsValue || {};
  
  document.getElementById('pctNotary').textContent = costPct.notary || 0;
  document.getElementById('pctTax').textContent = costPct.tax || 0;
  document.getElementById('pctBroker').textContent = costPct.broker || 0;
  
  document.getElementById('rNotary').textContent = formatCurrency(costVal.notary);
  document.getElementById('rTax').textContent = formatCurrency(costVal.tax);
  document.getElementById('rBroker').textContent = formatCurrency(costVal.broker);
  
  const extraTotal = (costVal.notary || 0) + (costVal.tax || 0) + (costVal.broker || 0);
  document.getElementById('rExtraTotal').textContent = formatCurrency(extraTotal);
  
  // Cost breakdown bar
  if (extraTotal > 0) {
    document.getElementById('barNotary').style.width = ((costVal.notary || 0) / extraTotal * 100) + '%';
    document.getElementById('barTax').style.width = ((costVal.tax || 0) / extraTotal * 100) + '%';
    document.getElementById('barBroker').style.width = ((costVal.broker || 0) / extraTotal * 100) + '%';
  }
}

// STEP 3: Load Heatmap
async function loadHeatmap() {
  const formValues = getFormValues();
  const city = formValues.city;
  
  document.getElementById('cityLabel').textContent = city;
  
  // Initialize or update map
  const center = cityCenters[city] || cityCenters['München'];
  
  if (!map) {
    map = L.map('map').setView(center, 12);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors'
    }).addTo(map);
  } else {
    map.setView(center, 12);
  }
  
  // Clear existing markers
  markers.forEach(m => map.removeLayer(m));
  markers = [];
  
  showLoading('Searching properties in ' + city + '...');
  
  try {
    const payload = {
      ...formValues,
      property_type: 'APARTMENTBUY',
      property_count: 200,
    };
    
    const response = await fetch(`${API_BASE}/heatmap/calculate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const data = await response.json();
    
    // Update stats
    const stats = data.heatmap?.stats || {};
    document.getElementById('cntGreen').textContent = stats.affordable || 0;
    document.getElementById('cntYellow').textContent = stats.stretch || 0;
    document.getElementById('cntRed').textContent = stats.out_of_range || 0;
    
    // Add markers to map
    const properties = data.properties || [];
    const bounds = [];
    
    properties.forEach(p => {
      if (!p.lat || !p.lon) return;
      
      const color = getAffordabilityColor(p.affordability);
      const icon = createMarkerIcon(color);
      
      const marker = L.marker([p.lat, p.lon], { icon }).addTo(map);
      
      const ratioPercent = Math.round((p.price_ratio || 0) * 100);
      marker.bindPopup(`
        <strong>${p.title}</strong><br>
        <b>${formatCurrency(p.price)}</b><br>
        ${p.sqm || '?'} m² · ${p.rooms || '?'} rooms<br>
        <span style="color:${color};font-weight:bold;">${ratioPercent}% of budget</span>
        ${p.platform_url ? `<br><a href="${p.platform_url}" target="_blank">View listing →</a>` : ''}
      `);
      
      markers.push(marker);
      bounds.push([p.lat, p.lon]);
    });
    
    // Fit map to markers
    if (bounds.length > 0) {
      map.fitBounds(bounds, { padding: [30, 30] });
    }
    
    // Render property cards
    renderPropertyCards(properties);
    
    // Go to step 3
    goToStep(3);
    
  } catch (error) {
    console.error('Heatmap error:', error);
    alert('Error loading properties: ' + error.message);
  } finally {
    hideLoading();
  }
}

// Get color based on affordability level
function getAffordabilityColor(level) {
  switch (level) {
    case 'affordable': return '#2ecc71';
    case 'stretch': return '#f39c12';
    case 'out_of_range': return '#e74c3c';
    default: return '#e74c3c';
  }
}

// Create custom marker icon
function createMarkerIcon(color) {
  return L.divIcon({
    className: 'custom-marker',
    html: `<div style="
      width: 14px;
      height: 14px;
      background: ${color};
      border-radius: 50%;
      border: 2px solid white;
      box-shadow: 0 2px 5px rgba(0,0,0,0.3);
    "></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  });
}

// Render property cards
function renderPropertyCards(properties) {
  const container = document.getElementById('propGrid');
  
  // Sort: affordable first, then stretch, then out_of_range
  const sorted = [...properties].sort((a, b) => {
    const order = { affordable: 0, stretch: 1, out_of_range: 2 };
    return (order[a.affordability] || 2) - (order[b.affordability] || 2);
  });
  
  // Limit to 30 cards for performance
  const limited = sorted.slice(0, 30);
  
  container.innerHTML = limited.map(p => {
    const ratioPercent = Math.round((p.price_ratio || 0) * 100);
    const levelClass = p.affordability || 'out_of_range';
    const levelLabel = levelClass === 'affordable' ? 'Affordable' :
                       levelClass === 'stretch' ? 'Stretch' : 'Out of Range';
    
    return `
      <div class="prop-card ${levelClass}">
        <div class="prop-title">${p.title || 'Unknown Property'}</div>
        <div class="prop-price">${formatCurrency(p.price)}</div>
        <div class="prop-details">
          ${p.sqm ? p.sqm + ' m²' : ''} 
          ${p.rooms ? '· ' + p.rooms + ' rooms' : ''}
          ${p.postcode ? '· ' + p.postcode : ''}
        </div>
        <span class="prop-badge ${levelClass}">${ratioPercent}% of budget · ${levelLabel}</span>
      </div>
    `;
  }).join('');
}

// Start Swipe Mode
async function startSwipeMode() {
  console.log('startSwipeMode called');
  console.log('calculatorInputs:', calculatorInputs);
  console.log('buyingPower:', buyingPower);
  
  if (!calculatorInputs || !buyingPower) {
    console.error('Missing calculator inputs or budget!');
    alert('Please calculate your budget first!');
    goToStep(1);
    return;
  }
  
  document.getElementById('swipeBudget').textContent = formatCurrency(buyingPower);
  
  showLoading('Loading properties for swiping...');
  
  try {
    // Get city directly from form value (no need to split)
    const city = calculatorInputs.city;
    
    // Map city to region
    const cityToRegion = {
      'München': 'Bayern',
      'Berlin': 'Berlin',
      'Hamburg': 'Hamburg',
      'Frankfurt': 'Hessen',
      'Köln': 'Nordrhein-Westfalen',
      'Stuttgart': 'Baden-Wuerttemberg'  // Use transliterated form for ThinkImmo
    };
    
    const region = cityToRegion[city] || 'Bayern';
    
    console.log(`Using city: ${city}, region: ${region}`);
    
    const payload = {
      city: city,
      region: region,
      propertyType: 'ALL',  // Get all property types for swipe discovery
      size: 200,
      from_index: 0
    };
    
    const response = await fetch(`${API_BASE}/api/properties/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    
    const data = await response.json();
    
    console.log('Backend response:', data);
    console.log(`Total properties: ${data.total || 0}`);
    console.log(`Results array length: ${data.results?.length || 0}`);
    console.log(`Budget: ${formatCurrency(buyingPower)}`);
    console.log(`City: ${city}, Region: ${region}`);
    
    if (!data.results || data.results.length === 0) {
      console.error('No results in backend response!');
      alert(`Backend returned no properties. Total: ${data.total || 0}`);
      hideLoading();
      return;
    }
    
    // Pass properties, budget, city, and region to swipe module
    if (typeof initSwipeMode === 'function') {
      initSwipeMode(data.results || [], buyingPower, city, region);
    } else {
      console.error('initSwipeMode function not found in tinder.js');
    }
    
    goToStep('3b');
    
  } catch (error) {
    console.error('Swipe mode error:', error);
    alert('Error loading properties: ' + error.message);
  } finally {
    hideLoading();
  }
}