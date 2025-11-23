// pinterest.js - Pinterest Style Analyzer

const PINTEREST_API = 'http://127.0.0.1:8000/pinterest';

// State
let analysisData = null;

// DOM Ready
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('analyzeBtn').addEventListener('click', analyzePinterestBoard);
});

// Navigation between steps
function goToPinterestStep(step) {
  // Hide all sections
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  
  // Reset all steps
  document.querySelectorAll('.step').forEach(s => s.classList.remove('active', 'completed'));
  
  // Mark completed steps
  for (let i = 1; i < step; i++) {
    const stepEl = document.getElementById('pStep' + i);
    if (stepEl) stepEl.classList.add('completed');
  }
  
  // Activate current step
  const currentStep = document.getElementById('pStep' + step);
  if (currentStep) currentStep.classList.add('active');
  
  const currentSection = document.getElementById('pSec' + step);
  if (currentSection) currentSection.classList.add('active');
}

// Loading overlay
function showLoading(text) {
  document.getElementById('loadTxt').textContent = text;
  document.getElementById('loading').classList.add('show');
}

function hideLoading() {
  document.getElementById('loading').classList.remove('show');
}

// Main analysis function
async function analyzePinterestBoard() {
  const url = document.getElementById('pinterestUrl').value.trim();
  const city = document.getElementById('pinterestCity').value;
  
  if (!url) {
    alert('Please enter a Pinterest board URL');
    return;
  }
  
  // Validate URL
  if (!url.includes('pinterest.com')) {
    alert('Please enter a valid Pinterest board URL');
    return;
  }
  
  showLoading('Analyzing your Pinterest board...');
  
  try {
    const response = await fetch(`${PINTEREST_API}/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        board_url: url,
        city: city
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to analyze board');
    }
    
    const data = await response.json();
    analysisData = data.data;
    
    hideLoading();
    
    // Display results
    displayBoardContext(analysisData.board_context);
    displayFeatureScores(analysisData.feature_scores);
    displayProperties(analysisData.properties);
    
    // Move to step 2
    goToPinterestStep(2);
    
  } catch (error) {
    hideLoading();
    console.error('Analysis error:', error);
    alert(`Error: ${error.message}. Please check your URL and try again.`);
  }
}

// Display board context analysis
function displayBoardContext(context) {
  const container = document.getElementById('boardContext');
  
  const html = `
    <div class="context-card">
      <div class="context-header">
        <span class="context-icon"><i class="fas fa-bullseye"></i></span>
        <h4>Board Analysis</h4>
      </div>
      <div class="context-grid">
        <div class="context-item">
          <span class="label">Primary Focus</span>
          <span class="value">${context.primary_focus || 'Mixed'}</span>
        </div>
        <div class="context-item">
          <span class="label">Space Type</span>
          <span class="value">${context.space_type || 'Various'}</span>
        </div>
        <div class="context-item">
          <span class="label">Living Type</span>
          <span class="value">${context.living_type || 'Not specified'}</span>
        </div>
      </div>
    </div>
  `;
  
  container.innerHTML = html;
}

// Display feature scores
function displayFeatureScores(scores) {
  const container = document.getElementById('featuresGrid');
  
  // Sort features by confidence score and take top 3
  const sortedFeatures = Object.entries(scores)
    .sort(([, a], [, b]) => b.confidence - a.confidence)
    .filter(([, scoreObj]) => scoreObj.confidence > 0)
    .slice(0, 3); // Limit to top 3
  
  if (sortedFeatures.length === 0) {
    container.innerHTML = '<p class="no-data">No distinct features detected</p>';
    return;
  }
  
  const html = sortedFeatures.map(([feature, scoreObj]) => {
    const percentage = Math.round(scoreObj.confidence * 100);
    const iconClass = getFeatureIcon(feature);
    const color = getFeatureColor(feature);
    
    return `
      <div class="feature-card">
        <div class="feature-header">
          <span class="feature-icon"><i class="fas ${iconClass}"></i></span>
          <span class="feature-name">${feature}</span>
        </div>
        <div class="feature-bar">
          <div class="feature-fill" style="width: ${percentage}%; background: ${color};"></div>
        </div>
        <div class="feature-score">${percentage}% confidence</div>
      </div>
    `;
  }).join('');
  
  container.innerHTML = html;
}

// Get icon for feature
function getFeatureIcon(feature) {
  const icons = {
    'Apartment': 'fa-building',
    'House': 'fa-home',
    'Balcony': 'fa-leaf',
    'Garden': 'fa-tree',
    'Modern': 'fa-sparkles',
    'Rustic': 'fa-mountain',
    'Vintage': 'fa-clock',
    'Dark': 'fa-moon',
    'Natural': 'fa-seedling',
    'Minimalist': 'fa-square',
    'Cozy': 'fa-couch'
  };
  return icons[feature] || 'fa-home';
}

// Get color for feature
function getFeatureColor(feature) {
  const colors = {
    'Apartment': '#2E7D99',
    'House': '#4CAF50',
    'Balcony': '#81C784',
    'Garden': '#66BB6A',
    'Modern': '#42A5F5',
    'Rustic': '#81C784',
    'Vintage': '#7986CB',
    'Dark': '#546E7A',
    'Natural': '#66BB6A',
    'Minimalist': '#90CAF9',
    'Cozy': '#4CAF50'
  };
  return colors[feature] || '#2E7D99';
}

// Display matched properties
function displayProperties(properties) {
  const container = document.getElementById('propertiesGrid');
  const countEl = document.getElementById('matchCount');
  
  if (!properties || properties.length === 0) {
    container.innerHTML = '<p class="no-data">No matching properties found. Try a different board or city.</p>';
    countEl.textContent = 'No matches found';
    return;
  }
  
  console.log('Displaying properties:', properties.length);
  console.log('First property sample:', properties[0]);
  
  // Show all properties (don't filter by images)
  const totalFound = properties.length;
  countEl.textContent = `Found ${totalFound} matching properties`;
  
  const html = properties.map(prop => {
    const matchScore = prop.match_score || 0;
    const matchReasons = prop.match_reasons || [];
    const price = prop.buyingPrice || prop.price || 0;
    const size = prop.squareMeter || prop.livingSpace || 0;
    const rooms = prop.rooms || 0;
    const title = prop.title || 'Property';
    const city = prop.address?.city || 'Unknown';
    // Use data URL for fallback to avoid external dependencies
    const fallbackImage = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="300"%3E%3Crect fill="%23ecf0f1" width="400" height="300"/%3E%3Ctext fill="%237f8c8d" font-family="Arial" font-size="20" x="50%25" y="50%25" text-anchor="middle" dy=".3em"%3ENo Image%3C/text%3E%3C/svg%3E';
    const image = prop.titlePicture || prop.image || fallbackImage;
    
    // Get match level
    let matchLevel = 'Low Match';
    let matchClass = 'low';
    if (matchScore >= 8) {
      matchLevel = 'Excellent Match';
      matchClass = 'excellent';
    } else if (matchScore >= 5) {
      matchLevel = 'Good Match';
      matchClass = 'good';
    } else if (matchScore >= 3) {
      matchLevel = 'Fair Match';
      matchClass = 'fair';
    }
    
    const propertyUrl = prop.link || prop.exposeUrl || '#';
    const hasValidUrl = propertyUrl !== '#' && propertyUrl !== '';
    
    return `
      <a href="${propertyUrl}" target="_blank" rel="noopener noreferrer" class="property-card-link" ${!hasValidUrl ? 'style="pointer-events: none; cursor: default;"' : ''}>
        <div class="property-card">
          <div class="property-image">
            <img src="${image}" alt="${title}" onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22400%22 height=%22300%22%3E%3Crect fill=%22%23ecf0f1%22 width=%22400%22 height=%22300%22/%3E%3Ctext fill=%22%237f8c8d%22 font-family=%22Arial%22 font-size=%2220%22 x=%2250%25%22 y=%2250%25%22 text-anchor=%22middle%22 dy=%22.3em%22%3ENo Image%3C/text%3E%3C/svg%3E'">
            <div class="match-badge ${matchClass}">
              <span class="match-score">${matchScore.toFixed(1)}</span>
              <span class="match-label">${matchLevel}</span>
            </div>
          </div>
          <div class="property-content">
          <h4 class="property-title">${title}</h4>
          <p class="property-location"><i class="fas fa-map-marker-alt"></i> ${city}</p>
          
          <div class="property-stats">
            <div class="stat">
              <span class="stat-value">€${price.toLocaleString('de-DE')}</span>
              <span class="stat-label">Price</span>
            </div>
            <div class="stat">
              <span class="stat-value">${size}m²</span>
              <span class="stat-label">Size</span>
            </div>
            <div class="stat">
              <span class="stat-value">${rooms}</span>
              <span class="stat-label">Rooms</span>
            </div>
          </div>
          
          ${matchReasons.length > 0 ? `
            <div class="match-reasons">
              <p class="reasons-title">Why this matches:</p>
              <ul>
                ${matchReasons.slice(0, 3).map(reason => `<li>${reason}</li>`).join('')}
              </ul>
            </div>
          ` : ''}
          
          <div class="view-details-hint">
            <i class="fas fa-external-link-alt"></i> Click to view details
          </div>
        </div>
      </div>
      </a>
    `;
  }).join('');
  
  container.innerHTML = html;
}

// Format currency
function formatCurrency(n) {
  return n ? '€' + Math.round(n).toLocaleString('de-DE') : '€0';
}
