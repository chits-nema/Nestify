// swipe.js - Tinder-style property swiping

// State
let allSwipeProperties = [];
let swipeProperties = [];
let currentSwipeIndex = 0;
let likedProperties = [];
let swipeBudget = 0;

const MAX_SWIPE_CARDS = 15;

// DOM elements
const cardContainer = document.getElementById('cardContainer');
const swipeStatus = document.getElementById('swipeStatus');
const likedSection = document.getElementById('likedSection');
const likedGrid = document.getElementById('likedGrid');
const recsSection = document.getElementById('recsSection');
const recsGrid = document.getElementById('recsGrid');

// Swipe state
let startX = 0, startY = 0, currentX = 0, isDragging = false, swipeCard = null;

// Initialize swipe mode with properties from budget.js
function initSwipeMode(properties, budget) {
  allSwipeProperties = properties || [];
  swipeBudget = budget;
  likedProperties = [];
  currentSwipeIndex = 0;
  
  // Filter to affordable + stretch only, then pick random subset
  const affordable = allSwipeProperties.filter(p => 
    p.affordability === 'affordable' || p.affordability === 'stretch'
  );
  
  swipeProperties = shuffleArray(affordable).slice(0, MAX_SWIPE_CARDS);
  
  // Reset UI
  if (likedSection) likedSection.style.display = 'none';
  if (recsSection) recsSection.style.display = 'none';
  
  if (swipeProperties.length === 0) {
    cardContainer.innerHTML = '<p class="no-props">No properties found in your budget range.</p>';
    return;
  }
  
  showCurrentCard();
}

// Shuffle array helper
function shuffleArray(arr) {
  const copy = [...arr];
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

// Format currency
const fmtPrice = (n) => n ? '€' + Math.round(n).toLocaleString('de-DE') : '€0';

// Show current property card
function showCurrentCard() {
  if (currentSwipeIndex >= swipeProperties.length) {
    handleSwipeComplete();
    return;
  }
  
  const p = swipeProperties[currentSwipeIndex];
  const ratioPercent = Math.round((p.price_ratio || 0) * 100);
  const levelClass = p.affordability || 'stretch';
  
  // Get image
  const imgUrl = p.image || null;
  
  cardContainer.innerHTML = `
    <div class="swipe-card ${levelClass}">
      ${imgUrl ? `
        <div class="card-image-container">
          <img src="${imgUrl}" alt="${p.title}" class="card-image" 
               onerror="this.parentElement.innerHTML='<div class=\\'no-image\\'>🏠</div>'">
        </div>
      ` : `<div class="card-image-container"><div class="no-image">🏠</div></div>`}
      <div class="card-content">
        <div class="card-badge ${levelClass}">${ratioPercent}% of budget</div>
        <h3 class="card-title">${p.title || 'Property'}</h3>
        <div class="card-price">${fmtPrice(p.price)}</div>
        <div class="card-details">
          ${p.sqm ? p.sqm + ' m²' : ''} 
          ${p.rooms ? '· ' + p.rooms + ' rooms' : ''}
        </div>
        <div class="card-location">${p.city || ''} ${p.postcode || ''}</div>
      </div>
    </div>
  `;
  
  swipeStatus.textContent = `${currentSwipeIndex + 1} / ${swipeProperties.length}`;
  
  setupSwipeGestures();
}

// Setup touch/mouse gestures
function setupSwipeGestures() {
  swipeCard = cardContainer.querySelector('.swipe-card');
  if (!swipeCard) return;
  
  // Mouse events
  swipeCard.addEventListener('mousedown', handleDragStart);
  document.addEventListener('mousemove', handleDragMove);
  document.addEventListener('mouseup', handleDragEnd);
  
  // Touch events
  swipeCard.addEventListener('touchstart', handleDragStart);
  document.addEventListener('touchmove', handleDragMove);
  document.addEventListener('touchend', handleDragEnd);
}

function handleDragStart(e) {
  isDragging = true;
  swipeCard = e.target.closest('.swipe-card');
  if (!swipeCard) return;
  
  const touch = e.type.includes('touch') ? e.touches[0] : e;
  startX = touch.clientX;
  startY = touch.clientY;
  swipeCard.style.transition = 'none';
}

function handleDragMove(e) {
  if (!isDragging || !swipeCard) return;
  
  const touch = e.type.includes('touch') ? e.touches[0] : e;
  currentX = touch.clientX - startX;
  const currentY = touch.clientY - startY;
  
  const rotation = currentX * 0.1;
  swipeCard.style.transform = `translate(${currentX}px, ${currentY}px) rotate(${rotation}deg)`;
  
  // Visual feedback
  const opacity = Math.min(Math.abs(currentX) / 100, 1);
  if (currentX > 0) {
    swipeCard.style.boxShadow = `0 0 30px rgba(46, 204, 113, ${opacity})`;
  } else if (currentX < 0) {
    swipeCard.style.boxShadow = `0 0 30px rgba(231, 76, 60, ${opacity})`;
  }
}

function handleDragEnd(e) {
  if (!isDragging || !swipeCard) return;
  isDragging = false;
  
  const threshold = 100;
  swipeCard.style.transition = 'transform 0.3s ease, opacity 0.3s ease, box-shadow 0.3s ease';
  
  if (Math.abs(currentX) > threshold) {
    const direction = currentX > 0 ? 1 : -1;
    swipeCard.style.transform = `translateX(${direction * 1000}px) rotate(${direction * 30}deg)`;
    swipeCard.style.opacity = '0';
    
    setTimeout(() => {
      if (direction > 0) {
        handleLike();
      } else {
        handlePass();
      }
    }, 300);
  } else {
    // Snap back
    swipeCard.style.transform = '';
    swipeCard.style.boxShadow = '';
  }
  
  startX = 0;
  currentX = 0;
}

// Like current property
function handleLike() {
  if (currentSwipeIndex < swipeProperties.length) {
    likedProperties.push(swipeProperties[currentSwipeIndex]);
  }
  currentSwipeIndex++;
  showCurrentCard();
}

// Pass on current property
function handlePass() {
  currentSwipeIndex++;
  showCurrentCard();
}

// Handle swipe completion
function handleSwipeComplete() {
  if (likedProperties.length === 0) {
    cardContainer.innerHTML = `
      <div class="swipe-complete">
        <div class="complete-icon">🤷</div>
        <h3>No matches yet!</h3>
        <p>You swiped through ${swipeProperties.length} properties but didn't like any.</p>
        <button class="btn primary" onclick="resetSwipe()">🔄 Try Again</button>
      </div>
    `;
    return;
  }
  
  cardContainer.innerHTML = `
    <div class="swipe-complete">
      <div class="complete-icon">🎉</div>
      <h3>Great choices!</h3>
      <p>You liked ${likedProperties.length} properties.</p>
    </div>
  `;
  
  // Show liked properties
  renderLikedProperties();
  
  // Show recommendations based on likes
  renderRecommendations();
}

// Render liked properties
function renderLikedProperties() {
  if (!likedSection || !likedGrid) return;
  
  likedSection.style.display = 'block';
  likedGrid.innerHTML = likedProperties.map(p => createPropertyCard(p)).join('');
}

// Render recommendations based on liked properties
function renderRecommendations() {
  if (!recsSection || !recsGrid) return;
  
  // Build preference profile from likes
  const avgPrice = likedProperties.reduce((sum, p) => sum + (p.price || 0), 0) / likedProperties.length;
  const avgSqm = likedProperties.reduce((sum, p) => sum + (p.sqm || 0), 0) / likedProperties.length;
  
  // Find similar properties not already shown or liked
  const shownIds = new Set([
    ...swipeProperties.map(p => p.id),
    ...likedProperties.map(p => p.id)
  ]);
  
  const recommendations = allSwipeProperties
    .filter(p => !shownIds.has(p.id))
    .filter(p => p.affordability === 'affordable' || p.affordability === 'stretch')
    .map(p => {
      // Score based on similarity to liked properties
      let score = 0;
      if (p.price && avgPrice) {
        const priceDiff = Math.abs(p.price - avgPrice) / avgPrice;
        score += (1 - Math.min(priceDiff, 1)) * 50;
      }
      if (p.sqm && avgSqm) {
        const sqmDiff = Math.abs(p.sqm - avgSqm) / avgSqm;
        score += (1 - Math.min(sqmDiff, 1)) * 50;
      }
      return { ...p, matchScore: score };
    })
    .sort((a, b) => b.matchScore - a.matchScore)
    .slice(0, 6);
  
  if (recommendations.length === 0) {
    recsSection.style.display = 'none';
    return;
  }
  
  recsSection.style.display = 'block';
  recsGrid.innerHTML = recommendations.map(p => createPropertyCard(p)).join('');
}

// Create property card HTML
function createPropertyCard(p) {
  const ratioPercent = Math.round((p.price_ratio || 0) * 100);
  const levelClass = p.affordability || 'stretch';
  
  return `
    <div class="prop-card ${levelClass}">
      <div class="prop-title">${p.title || 'Property'}</div>
      <div class="prop-price">${fmtPrice(p.price)}</div>
      <div class="prop-details">
        ${p.sqm ? p.sqm + ' m²' : ''} 
        ${p.rooms ? '· ' + p.rooms + ' rooms' : ''}
        ${p.city ? '· ' + p.city : ''}
      </div>
      <span class="prop-badge ${levelClass}">${ratioPercent}% of budget</span>
    </div>
  `;
}

// Reset and start swiping again
function resetSwipe() {
  // Get more random properties
  const affordable = allSwipeProperties.filter(p => 
    p.affordability === 'affordable' || p.affordability === 'stretch'
  );
  
  // Exclude already liked
  const likedIds = new Set(likedProperties.map(p => p.id));
  const available = affordable.filter(p => !likedIds.has(p.id));
  
  swipeProperties = shuffleArray(available).slice(0, MAX_SWIPE_CARDS);
  currentSwipeIndex = 0;
  
  if (swipeProperties.length === 0) {
    cardContainer.innerHTML = '<p class="no-props">No more properties to show!</p>';
    return;
  }
  
  showCurrentCard();
}

// Make functions available globally
window.initSwipeMode = initSwipeMode;
window.resetSwipe = resetSwipe;