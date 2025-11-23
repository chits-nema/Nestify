// tinder.js – Swipe 15 random homes, then recommend similar ones

// Global state
let allProperties = [];     // all results from backend (up to size=50)
let properties = [];        // 15 random homes for this session
let currentIndex = 0;
let likedProperties = [];
let userBudget = 0;         // User's calculated budget

// Backend URL (FastAPI on port 8000)
const BACKEND_URL = "http://127.0.0.1:8000";

// How many homes you want to show per swipe session
const MAX_CARDS = 15;  // Initial batch size
const MAX_TOTAL_SWIPES = 50;  // Maximum total swipes allowed

// Note: formatCurrency is defined in budget.js which loads before this script

// DOM elements
const cardContainer = document.getElementById("card-container");
const statusText = document.getElementById("status-text");

const recSection = document.getElementById("recommendations");
const recContainer = document.getElementById("recommendations-container");

const likedSection = document.getElementById("liked-section");
const likedContainer = document.getElementById("liked-container");

const detailSection = document.getElementById("detail-section");
const detailImage = document.getElementById("detail-image");
const detailTitle = document.getElementById("detail-title");
const detailLocation = document.getElementById("detail-location");
const detailPrice = document.getElementById("detail-price");
const detailSize = document.getElementById("detail-size");
const detailRooms = document.getElementById("detail-rooms");
const detailLink = document.getElementById("detail-link");
const detailCloseBtn = document.getElementById("detail-close-btn");

// Swipe state
let startX = 0;
let startY = 0;
let currentX = 0;
let currentY = 0;
let isDragging = false;
let swipeCard = null;

// Setup listeners
document.addEventListener("DOMContentLoaded", () => {
  if (!cardContainer) return;

  // Wait for budget.js to call initSwipeMode with properties
  // Don't fetch properties automatically
  
  if (detailCloseBtn) {
    detailCloseBtn.addEventListener("click", () => {
      detailSection.style.display = "none";
    });
  }
});

// --------------------------------------------------------
// Initialize swipe mode with properties from budget.js
function initSwipeMode(propertiesList, budget, city, region) {
  console.log(`initSwipeMode called with ${propertiesList?.length || 0} properties, budget: ${formatCurrency(budget)}, city: ${city}`);
  
  if (!propertiesList || propertiesList.length === 0) {
    statusText.textContent = "No properties found from backend.";
    cardContainer.innerHTML = `
      <div style="padding: 40px; text-align: center; background: white; border-radius: 16px;">
        <div style="font-size: 3rem; margin-bottom: 20px;">😕</div>
        <h3 style="color: #2c3e50; margin-bottom: 15px;">No Properties Found</h3>
        <p style="color: #666;">The backend returned no properties for ${city || 'your area'}.</p>
      </div>
    `;
    return;
  }

  userBudget = budget;
  
  // Sort properties by price to prioritize affordable ones
  const sortedProperties = [...propertiesList].sort((a, b) => {
    const priceA = a.buyingPrice ?? a.price ?? 0;
    const priceB = b.buyingPrice ?? b.price ?? 0;
    return priceA - priceB;
  });
  
  // Take a mix: prioritize affordable but include some aspirational properties
  // Take 70% within 150% of budget, and 30% above that for variety
  const maxAffordable = budget * 1.5;
  const affordableProperties = sortedProperties.filter(p => {
    const price = p.buyingPrice ?? p.price ?? 0;
    return price > 0 && price <= maxAffordable;
  });
  
  const aspirationalProperties = sortedProperties.filter(p => {
    const price = p.buyingPrice ?? p.price ?? 0;
    return price > maxAffordable;
  });
  
  // Mix: 70% affordable, 30% aspirational (if available)
  const affordableCount = Math.ceil(sortedProperties.length * 0.7);
  const aspirationalCount = sortedProperties.length - affordableCount;
  
  const mixedProperties = [
    ...affordableProperties.slice(0, affordableCount),
    ...aspirationalProperties.slice(0, aspirationalCount)
  ];
  
  console.log(`Budget: ${formatCurrency(budget)}`);
  console.log(`Properties breakdown: ${affordableProperties.length} affordable (≤${formatCurrency(maxAffordable)}), ${aspirationalProperties.length} aspirational`);
  console.log(`Showing ${mixedProperties.length} properties total`);
  
  if (mixedProperties.length === 0) {
    statusText.textContent = "No properties found.";
    cardContainer.innerHTML = `
      <div style="padding: 40px; text-align: center; background: white; border-radius: 16px;">
        <div style="font-size: 3rem; margin-bottom: 20px;">😕</div>
        <h3 style="color: #2c3e50; margin-bottom: 15px;">No Properties Found</h3>
        <p style="color: #666; margin-bottom: 15px;">Your budget: ${formatCurrency(budget)}</p>
        <p style="color: #666;">Found ${propertiesList.length} properties in ${city || 'your area'}.</p>
      </div>
    `;
    return;
  }
  
  allProperties = mixedProperties;
  properties = pickRandomSubset(allProperties, MAX_CARDS);
  currentIndex = 0;
  likedProperties = [];

  const withinBudget = allProperties.filter(p => (p.buyingPrice ?? p.price) <= budget).length;
  const stretchCount = allProperties.filter(p => {
    const price = p.buyingPrice ?? p.price ?? 0;
    return price > budget && price <= maxAffordable;
  }).length;
  const dreamCount = allProperties.length - withinBudget - stretchCount;
  
  statusText.textContent = `Found ${allProperties.length} properties in ${city || 'your area'} (${withinBudget} within budget, ${stretchCount} stretch, ${dreamCount} aspirational). Swipe through ${properties.length} to start!`;
  statusText.style.color = '#2ecc71';
  
  console.log(`Starting swipe with ${properties.length} properties`);
  showCurrentProperty();
}

// --------------------------------------------------------
// Fetch properties from backend (ThinkImmo proxy or demo)
async function fetchProperties(city, region) {
  if (!cardContainer) return;

  statusText.textContent = "Loading properties...";
  cardContainer.innerHTML = "<p>Loading properties...</p>";

  try {
    const res = await fetch(`${BACKEND_URL}/api/properties/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        city: city,
        region: region,
        size: 200,         // Fetch 200 properties for better recommendations
        from_index: 0,
        propertyType: "APARTMENTBUY"
      })
    });

    const data = await res.json();
    allProperties = Array.isArray(data.results) ? data.results : [];

    // Properties loaded successfully

    // Pick up to MAX_CARDS (30) random homes from allProperties for swiping
    properties = pickRandomSubset(allProperties, MAX_CARDS);
    currentIndex = 0;
    likedProperties = [];

    if (properties.length === 0) {
      cardContainer.innerHTML = "<p>No properties found in this area.</p>";
      statusText.textContent = "";
      return;
    }

    if (recSection) recSection.style.display = "none";
    if (likedSection) likedSection.style.display = "none";
    if (detailSection) detailSection.style.display = "none";

    showCurrentProperty();
    statusText.textContent = "";
  } catch (err) {
    console.error("Error fetching properties:", err);
    cardContainer.innerHTML = "<p>Error loading properties.</p>";
    statusText.textContent = "Could not load properties.";
  }
}

// Helper: randomly choose up to n items from an array
function pickRandomSubset(arr, n) {
  const copy = [...arr];
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy.slice(0, Math.min(n, copy.length));
}

// Global variable to track current image index for carousel
let currentImageIndex = 0;

// --------------------------------------------------------
// Render the current property card with image carousel
function showCurrentProperty() {
  if (!properties.length) {
    cardContainer.innerHTML = "<p>No properties.</p>";
    return;
  }

  if (currentIndex >= properties.length) {
    // User finished current batch
    handleEndOfSwipes();
    return;
  }

  const p = properties[currentIndex];
  currentImageIndex = 0; // Reset image index for new property

  const title = p.title || "Untitled property";
  const price = p.buyingPrice ?? p.price ?? 0;
  const sqm = p.squareMeter ?? p.livingSpace ?? "N/A";
  const rooms = p.rooms ?? "N/A";
  const city =
    (p.address &&
      (p.address.city || p.address.displayName || p.address._normalized_city)) ||
    "Unknown location";
  
  // Calculate affordability
  const priceRatio = userBudget > 0 ? (price / userBudget) : 1;
  const affordability = priceRatio <= 0.9 ? 'affordable' : priceRatio <= 1.0 ? 'within-budget' : 'stretch';
  const affordabilityLabel = priceRatio <= 0.9 ? '✓ Affordable' : priceRatio <= 1.0 ? '✓ Within Budget' : '⚠ Stretch';
  const affordabilityColor = priceRatio <= 0.9 ? '#2ecc71' : priceRatio <= 1.0 ? '#3498db' : '#f39c12';
  const budgetPercent = Math.round(priceRatio * 100);

  // Get all images with better error handling
  const images = p.images && p.images.length > 0 
    ? p.images
        .map((img, idx) => {
          // Try multiple image URL formats
          const url = img.originalUrl || img.url || img.src || img.href;
          
          // Debug logging for missing images
          if (!url) {
            console.warn(`⚠️ Image ${idx + 1} missing URL for property:`, p.title, img);
          }
          
          return url;
        })
        .filter(Boolean)
        .filter(url => {
          // Basic URL validation
          try {
            const isValid = url.startsWith('http://') || url.startsWith('https://');
            if (!isValid) {
              console.warn('⚠️ Invalid image URL (not http/https):', url);
            }
            return isValid;
          } catch (e) {
            console.warn('⚠️ Error validating URL:', url, e);
            return false;
          }
        })
    : [];

  // Log if no valid images found but property has images array
  if (images.length === 0 && p.images && p.images.length > 0) {
    console.warn('⚠️ Property has images array but no valid URLs:', {
      title: p.title,
      imagesCount: p.images.length,
      images: p.images
    });
  }

  // Image validation complete

  const hasMultipleImages = images.length > 1;
  const hasAnyImage = images.length > 0;

  cardContainer.innerHTML = `
    <div class="swipe-card">
      ${
        hasAnyImage
          ? `<div class="card-image-container">
               <img alt="${title}"
                    class="card-image"
                    id="card-image"
                    style="display: none;" />
               <div id="no-image-msg" class="no-image-message" style="display: none;"></div>
               ${hasMultipleImages ? `
                 <button class="carousel-btn carousel-prev" id="prev-img-btn">
                   <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                     <polyline points="15 18 9 12 15 6"></polyline>
                   </svg>
                 </button>
                 <button class="carousel-btn carousel-next" id="next-img-btn">
                   <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                     <polyline points="9 18 15 12 9 6"></polyline>
                   </svg>
                 </button>
                 <div class="carousel-dots" id="carousel-dots">
                   ${images.map((_, idx) => 
                     `<span class="carousel-dot ${idx === 0 ? 'active' : ''}" data-index="${idx}"></span>`
                   ).join('')}
                 </div>
               ` : ''}
             </div>`
          : ""
      }
      <div class="card-content">
        <h2 class="card-title">${title}</h2>
        <p class="card-price">${
          price === 0 ? "Price on request" : formatCurrency(price)
        }</p>
        <p class="card-details">${sqm} m² · ${rooms} rooms</p>
        <p class="card-location">${city}</p>
        ${userBudget > 0 ? `
          <div style="margin-top: 12px; padding: 8px 12px; background: ${affordabilityColor}15; border-left: 3px solid ${affordabilityColor}; border-radius: 4px;">
            <span style="color: ${affordabilityColor}; font-weight: 600; font-size: 0.9rem;">${affordabilityLabel}</span>
            <span style="color: #666; font-size: 0.85rem; margin-left: 8px;">${budgetPercent}% of your budget</span>
          </div>
        ` : ''}
      </div>
    </div>
  `;

  // Setup carousel navigation if multiple images
  if (hasMultipleImages) {
    setupCarousel(images);
  } else if (hasAnyImage) {
    // Load single image with error handling
    setTimeout(() => loadSingleImage(images[0]), 50);
  }

  // Setup swipe gestures
  setupSwipeGestures();
}

// Load single image with error handling
function loadSingleImage(imageUrl) {
  const cardImage = document.getElementById('card-image');
  const noImageMsg = document.getElementById('no-image-msg');
  
  if (!cardImage) return;
  
  cardImage.onerror = function() {
    this.onerror = null;
    this.style.display = 'none';
    if (noImageMsg) {
      noImageMsg.style.display = 'block';
      noImageMsg.innerHTML = `
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
          <circle cx="8.5" cy="8.5" r="1.5"></circle>
          <polyline points="21 15 16 10 5 21"></polyline>
        </svg>
        <p class="main-message">📷 Images Protected by Source</p>
        <p class="sub-message">If you're interested, swipe right! ❤️<br>Visit the website for photos</p>
      `;
    }
  };
  
  cardImage.onload = function() {
    this.style.display = 'block';
  };
  
  cardImage.src = imageUrl;
}

// Setup carousel navigation
function setupCarousel(images) {
  const cardImage = document.getElementById('card-image');
  const prevBtn = document.getElementById('prev-img-btn');
  const nextBtn = document.getElementById('next-img-btn');
  const dotsContainer = document.getElementById('carousel-dots');

  if (!cardImage) return;

  // Track which images failed to load
  const failedImages = new Set();
  
  const updateImage = (index) => {
    currentImageIndex = index;
    const noImageMsg = document.getElementById('no-image-msg');
    
    // Reset image visibility
    cardImage.style.display = 'none';
    if (noImageMsg) noImageMsg.style.display = 'none';
    
    // Set onerror handler BEFORE setting src
    cardImage.onerror = function() {
      this.onerror = null;
      
      // Mark this image as failed
      failedImages.add(currentImageIndex);
      
      console.warn(`❌ Image ${currentImageIndex + 1} failed to load:`, images[currentImageIndex]);
      
      // Show placeholder for this specific image (don't skip)
      this.style.display = 'none';
      if (noImageMsg) {
        noImageMsg.style.display = 'block';
        noImageMsg.innerHTML = `
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
            <circle cx="8.5" cy="8.5" r="1.5"></circle>
            <polyline points="21 15 16 10 5 21"></polyline>
          </svg>
          <p class="main-message">📷 Images Protected by Source</p>
          <p class="sub-message">If you're interested, swipe right! ❤️<br>Visit the website for photos</p>
        `;
      }
    };
    
    // Set onload handler to show image when successful
    cardImage.onload = function() {
      this.style.display = 'block';
    };
    
    // Now set the src to trigger loading
    cardImage.src = images[currentImageIndex];
    
    // Update dots
    if (dotsContainer) {
      const dots = dotsContainer.querySelectorAll('.carousel-dot');
      dots.forEach((dot, idx) => {
        dot.classList.toggle('active', idx === currentImageIndex);
      });
    }
  };

  // Previous button
  if (prevBtn) {
    prevBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const newIndex = (currentImageIndex - 1 + images.length) % images.length;
      updateImage(newIndex);
    });
  }

  // Next button
  if (nextBtn) {
    nextBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const newIndex = (currentImageIndex + 1) % images.length;
      updateImage(newIndex);
    });
  }

  // Dot navigation
  if (dotsContainer) {
    const dots = dotsContainer.querySelectorAll('.carousel-dot');
    dots.forEach((dot) => {
      dot.addEventListener('click', (e) => {
        e.stopPropagation();
        const index = parseInt(dot.getAttribute('data-index'));
        updateImage(index);
      });
    });
  }

  // Keyboard navigation
  const handleKeyboard = (e) => {
    if (e.key === 'ArrowLeft') {
      e.preventDefault();
      const newIndex = (currentImageIndex - 1 + images.length) % images.length;
      updateImage(newIndex);
    } else if (e.key === 'ArrowRight') {
      e.preventDefault();
      const newIndex = (currentImageIndex + 1) % images.length;
      updateImage(newIndex);
    }
  };

  document.addEventListener('keydown', handleKeyboard);
  
  // Load first image immediately
  updateImage(0);
}

// --------------------------------------------------------
// Setup swipe gestures (touch and mouse)
function setupSwipeGestures() {
  swipeCard = document.querySelector('.swipe-card');
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
  // Don't interfere with carousel buttons and dots
  if (e.target.closest('.carousel-btn') || 
      e.target.closest('.carousel-dot') ||
      e.target.closest('#like-btn') ||
      e.target.closest('#nope-btn')) {
    return;
  }

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
  currentY = touch.clientY - startY;

  // Apply transform
  const rotation = currentX * 0.1; // Slight rotation based on drag
  swipeCard.style.transform = `translate(${currentX}px, ${currentY}px) rotate(${rotation}deg)`;

  // Visual feedback
  const opacity = Math.abs(currentX) / 100;
  if (currentX > 0) {
    // Swiping right (like)
    swipeCard.style.borderColor = `rgba(76, 175, 80, ${Math.min(opacity, 1)})`;
  } else if (currentX < 0) {
    // Swiping left (nope)
    swipeCard.style.borderColor = `rgba(244, 67, 54, ${Math.min(opacity, 1)})`;
  }
}

function handleDragEnd(e) {
  if (!isDragging || !swipeCard) return;
  isDragging = false;

  const swipeThreshold = 100; // Minimum distance to trigger swipe

  swipeCard.style.transition = 'transform 0.3s ease, opacity 0.3s ease, border-color 0.3s ease';

  if (Math.abs(currentX) > swipeThreshold) {
    // Complete the swipe
    const direction = currentX > 0 ? 1 : -1;
    swipeCard.style.transform = `translateX(${direction * 1000}px) rotate(${direction * 30}deg)`;
    swipeCard.style.opacity = '0';

    setTimeout(() => {
      if (direction > 0) {
        handleLike();
      } else {
        handleNope();
      }
      // Reset card style
      if (swipeCard) {
        swipeCard.style.transform = '';
        swipeCard.style.opacity = '';
        swipeCard.style.borderColor = '';
        swipeCard.style.transition = '';
      }
    }, 300);
  } else {
    // Snap back to center
    swipeCard.style.transform = '';
    swipeCard.style.borderColor = '';
  }

  startX = 0;
  startY = 0;
  currentX = 0;
  currentY = 0;
}

// --------------------------------------------------------
// Like / Nope logic
function handleLike() {
  if (currentIndex >= properties.length) return;

  const current = properties[currentIndex];
  likedProperties.push(current);
  currentIndex += 1;

  showCurrentProperty();
}

function handleNope() {
  if (currentIndex >= properties.length) return;
  currentIndex += 1;
  showCurrentProperty();
}

// --------------------------------------------------------
// Handle end of swipe session
function handleEndOfSwipes() {
  const totalSwipesInSession = currentIndex;
  const profile = buildPreferenceProfile(likedProperties);
  
  // Case 1: No likes at all
  if (likedProperties.length === 0) {
    cardContainer.innerHTML = `
      <div style="padding: 40px; text-align: center; background: white; border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        <div style="font-size: 3rem; margin-bottom: 20px;">🤷‍♀️</div>
        <h3 style="color: #2c3e50; margin-bottom: 15px;">No matches yet!</h3>
        <p style="color: #666; margin-bottom: 25px;">You swiped through ${totalSwipesInSession} properties but didn't like any.</p>
        <button onclick="loadMoreProperties()" style="padding: 12px 30px; background: #667eea; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 1rem; font-weight: 500;">
          🔄 Load 15 More Properties
        </button>
      </div>
    `;
    return;
  }
  
  // Case 2: Few likes (< 5) - Low confidence
  if (likedProperties.length < 5) {
    cardContainer.innerHTML = `
      <div style="padding: 40px; text-align: center; background: white; border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        <div style="font-size: 3rem; margin-bottom: 20px;">📊</div>
        <h3 style="color: #2c3e50; margin-bottom: 15px;">Getting there!</h3>
        <p style="color: #666; margin-bottom: 10px;">You liked ${likedProperties.length} ${likedProperties.length === 1 ? 'property' : 'properties'}.</p>
        <p style="color: #666; margin-bottom: 25px;">
          <strong>Confidence: ${profile ? profile.confidence : 40}%</strong> - 
          Like a few more for better recommendations!
        </p>
        <div style="display: flex; gap: 15px; justify-content: center; flex-wrap: wrap;">
          <button onclick="loadMoreProperties()" style="padding: 12px 30px; background: #667eea; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 1rem; font-weight: 500;">
            🔄 Swipe 15 More (Recommended)
          </button>
          <button onclick="showResultsNow()" style="padding: 12px 30px; background: #95a5a6; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 1rem; font-weight: 500;">
            ✓ Show Results Anyway
          </button>
        </div>
      </div>
    `;
    return;
  }
  
  // Case 3: Good amount of likes (5+) - Show results
  cardContainer.innerHTML = `
    <div style="padding: 40px; text-align: center; background: white; border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
      <div style="font-size: 3rem; margin-bottom: 20px;">✨</div>
      <h3 style="color: #2c3e50; margin-bottom: 15px;">Great job!</h3>
      <p style="color: #666; margin-bottom: 10px;">You liked ${likedProperties.length} ${likedProperties.length === 1 ? 'property' : 'properties'}.</p>
      <p style="color: #666; margin-bottom: 25px;">
        <strong>Confidence: ${profile ? profile.confidence : 75}%</strong> - 
        ${profile && profile.confidence >= 90 ? 'Excellent data!' : 'Good confidence level!'}
      </p>
      <div style="display: flex; gap: 15px; justify-content: center; flex-wrap: wrap;">
        <button onclick="showResultsNow()" style="padding: 12px 30px; background: #2ecc71; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 1rem; font-weight: 500;">
          ❤️ Show My Recommendations
        </button>
        <button onclick="loadMoreProperties()" style="padding: 12px 30px; background: #667eea; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 1rem; font-weight: 500;">
          🔄 Swipe More for Better Results
        </button>
      </div>
    </div>
  `;
  
  // Automatically scroll to the card
  cardContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// Load more properties (15 more)
function loadMoreProperties() {
  // Check if user has reached max swipes
  if (properties.length >= MAX_TOTAL_SWIPES) {
    cardContainer.innerHTML = `
      <div style="padding: 40px; text-align: center; background: white; border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        <div style="font-size: 3rem; margin-bottom: 20px;">🎯</div>
        <h3 style="color: #2c3e50; margin-bottom: 15px;">Maximum swipes reached!</h3>
        <p style="color: #666; margin-bottom: 10px;">You've swiped through ${properties.length} properties.</p>
        <p style="color: #666; margin-bottom: 25px;">Time to see your personalized recommendations!</p>
        <button onclick="showResultsNow()" style="padding: 12px 30px; background: #2ecc71; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 1rem; font-weight: 500;">
          ✓ Show My Recommendations
        </button>
      </div>
    `;
    return;
  }
  
  // Get 15 more random properties from allProperties that we haven't shown yet
  const unseenProperties = allProperties.filter(p => 
    !properties.some(shown => isSameProperty(shown, p))
  );
  
  if (unseenProperties.length === 0) {
    cardContainer.innerHTML = `
      <div style="padding: 40px; text-align: center; background: white; border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        <div style="font-size: 3rem; margin-bottom: 20px;">🎉</div>
        <h3 style="color: #2c3e50; margin-bottom: 15px;">You've seen everything!</h3>
        <p style="color: #666; margin-bottom: 25px;">No more properties available in this area.</p>
        <button onclick="showResultsNow()" style="padding: 12px 30px; background: #2ecc71; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 1rem; font-weight: 500;">
          ✓ Show My Recommendations
        </button>
      </div>
    `;
    return;
  }
  
  // Calculate how many more we can show
  const remainingSlots = MAX_TOTAL_SWIPES - properties.length;
  const batchSize = Math.min(15, remainingSlots, unseenProperties.length);
  
  // Add more properties
  const moreProperties = pickRandomSubset(unseenProperties, batchSize);
  properties = [...properties, ...moreProperties];
  
  // Continue from where we left off
  showCurrentProperty();
  
  // Show feedback
  statusText.textContent = `Loaded ${moreProperties.length} more properties! (${properties.length}/${MAX_TOTAL_SWIPES} total)`;
  statusText.style.color = '#2ecc71';
  setTimeout(() => {
    statusText.textContent = '';
  }, 2000);
}

// Show results immediately
function showResultsNow() {
  renderRecommendations();
  renderLikedHomes();
  
  // Hide the card container (but keep it in DOM for return)
  cardContainer.style.display = 'none';
  
  // Scroll to recommendations
  if (recSection) {
    recSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

// --------------------------------------------------------
// Build smart preference profile from liked properties with dynamic weighting
function buildPreferenceProfile(liked) {
  if (!liked || liked.length === 0) return null;

  // Extract all data points
  const cities = liked
    .map(
      (p) =>
        p.address &&
        (p.address.city || p.address.displayName || p.address._normalized_city)
    )
    .filter(Boolean);

  const prices = liked
    .map((p) => p.buyingPrice)
    .filter((v) => typeof v === "number" && v > 0);

  const sqms = liked
    .map((p) => p.squareMeter || p.livingSpace)
    .filter((v) => typeof v === "number" && v > 0);

  const rooms = liked
    .map((p) => p.rooms)
    .filter((v) => typeof v === "number" && v > 0);

  // City preferences - find most common + alternatives
  const cityStats = calculateCategoryPreferences(cities);
  const preferredCity = cityStats.preferred;
  const alternativeCities = cityStats.alternatives;
  const cityConsistency = cityStats.consistency; // How often preferred city appears

  // Price preferences with smart range + standard deviation
  let minPrice = null, maxPrice = null, avgPrice = null, stdDevPrice = null;
  if (prices.length > 0) {
    const sorted = [...prices].sort((a, b) => a - b);
    minPrice = sorted[0];
    maxPrice = sorted[sorted.length - 1];
    avgPrice = prices.reduce((sum, p) => sum + p, 0) / prices.length;
    stdDevPrice = calculateStdDev(prices, avgPrice);
  }

  // Size preferences with standard deviation
  let minSqm = null, maxSqm = null, avgSqm = null, stdDevSqm = null;
  if (sqms.length > 0) {
    const sorted = [...sqms].sort((a, b) => a - b);
    minSqm = sorted[0];
    maxSqm = sorted[sorted.length - 1];
    avgSqm = sqms.reduce((sum, s) => sum + s, 0) / sqms.length;
    stdDevSqm = calculateStdDev(sqms, avgSqm);
  }

  // Room preferences
  let minRooms = null, maxRooms = null, avgRooms = null, stdDevRooms = null;
  if (rooms.length > 0) {
    minRooms = Math.min(...rooms);
    maxRooms = Math.max(...rooms);
    avgRooms = rooms.reduce((sum, r) => sum + r, 0) / rooms.length;
    stdDevRooms = calculateStdDev(rooms, avgRooms);
  }

  // Calculate dynamic weights based on consistency (low stdDev = user is specific = higher weight)
  const weights = calculateDynamicWeights({
    cityConsistency,
    stdDevPrice,
    avgPrice,
    stdDevSqm,
    avgSqm,
    stdDevRooms,
    avgRooms,
    sampleSize: liked.length
  });

  // Calculate confidence score (0-100) based on sample size and consistency
  const confidence = calculateConfidenceScore(liked.length, {
    cityConsistency,
    stdDevPrice,
    avgPrice,
    stdDevSqm,
    avgSqm
  });

  console.log('📊 Preference Profile:', {
    sampleSize: liked.length,
    confidence: `${confidence}%`,
    weights: `City:${weights.city}%, Price:${weights.price}%, Size:${weights.size}%, Rooms:${weights.rooms}%`,
    city: `${preferredCity} (${cityConsistency}% consistency)`,
    price: `€${minPrice}-€${maxPrice} (avg: €${Math.round(avgPrice)}, stdDev: €${Math.round(stdDevPrice)})`,
    size: `${minSqm}-${maxSqm}m² (avg: ${Math.round(avgSqm)}m², stdDev: ${Math.round(stdDevSqm)}m²)`
  });

  return {
    // City preferences
    preferredCity,
    alternativeCities,
    cityConsistency,

    // Price preferences
    minPrice,
    maxPrice,
    avgPrice,
    stdDevPrice,

    // Size preferences
    minSqm,
    maxSqm,
    avgSqm,
    stdDevSqm,

    // Room preferences
    minRooms,
    maxRooms,
    avgRooms,
    stdDevRooms,

    // Dynamic weights
    weights,

    // Meta
    sampleSize: liked.length,
    confidence
  };
}

// Helper: Calculate category preferences (cities) with consistency metric
function calculateCategoryPreferences(categories) {
  if (!categories || categories.length === 0) {
    return { preferred: null, alternatives: [], consistency: 0 };
  }

  const counts = {};
  categories.forEach((cat) => {
    counts[cat] = (counts[cat] || 0) + 1;
  });

  const sorted = Object.entries(counts)
    .sort((a, b) => b[1] - a[1]);

  const preferred = sorted[0][0];
  const preferredCount = sorted[0][1];
  const consistency = Math.round((preferredCount / categories.length) * 100);
  
  // Include cities that appear at least twice or 15% of likes
  const threshold = Math.max(2, Math.floor(categories.length * 0.15));
  const alternatives = sorted
    .slice(1)
    .filter(([_, count]) => count >= threshold)
    .map(([city, _]) => city);

  return { preferred, alternatives, consistency };
}

// Helper: Calculate standard deviation
function calculateStdDev(values, mean) {
  if (values.length < 2) return 0;
  const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length;
  return Math.sqrt(variance);
}

// Helper: Calculate dynamic weights based on user consistency
function calculateDynamicWeights(stats) {
  const { cityConsistency, stdDevPrice, avgPrice, stdDevSqm, avgSqm, stdDevRooms, avgRooms, sampleSize } = stats;
  
  // Base weights
  let weights = { city: 25, price: 35, size: 30, rooms: 10 };
  
  // Not enough data - use defaults
  if (sampleSize < 3) return weights;
  
  // Calculate coefficient of variation (CV) for each metric
  // Lower CV = more consistent = user cares more = higher weight
  const cvPrice = avgPrice > 0 ? (stdDevPrice / avgPrice) : 1;
  const cvSize = avgSqm > 0 ? (stdDevSqm / avgSqm) : 1;
  const cvRooms = avgRooms > 0 ? (stdDevRooms / avgRooms) : 1;
  
  // City consistency already in percentage (0-100)
  const cityScore = cityConsistency / 100;
  
  // Score each factor (0-1, where 1 = very consistent)
  // CV < 0.15 = very specific, CV > 0.4 = very flexible
  const priceScore = Math.max(0, Math.min(1, 1 - (cvPrice / 0.4)));
  const sizeScore = Math.max(0, Math.min(1, 1 - (cvSize / 0.4)));
  const roomsScore = Math.max(0, Math.min(1, 1 - (cvRooms / 0.4)));
  
  // Redistribute weights based on consistency
  // More consistent = higher weight, less consistent = lower weight
  const totalScore = cityScore + priceScore + sizeScore + roomsScore;
  if (totalScore > 0) {
    // Adjust weights proportionally, but keep reasonable bounds
    weights.city = Math.round(Math.max(15, Math.min(35, 25 * (cityScore / totalScore) * 4)));
    weights.price = Math.round(Math.max(25, Math.min(45, 35 * (priceScore / totalScore) * 4)));
    weights.size = Math.round(Math.max(20, Math.min(40, 30 * (sizeScore / totalScore) * 4)));
    weights.rooms = Math.round(Math.max(5, Math.min(15, 10 * (roomsScore / totalScore) * 4)));
    
    // Normalize to 100%
    const sum = weights.city + weights.price + weights.size + weights.rooms;
    weights.city = Math.round((weights.city / sum) * 100);
    weights.price = Math.round((weights.price / sum) * 100);
    weights.size = Math.round((weights.size / sum) * 100);
    weights.rooms = 100 - weights.city - weights.price - weights.size; // Ensure exactly 100%
  }
  
  return weights;
}

// Helper: Calculate confidence score (0-100)
function calculateConfidenceScore(sampleSize, stats) {
  // Base confidence on sample size
  let confidence = 0;
  if (sampleSize >= 10) confidence = 100;
  else if (sampleSize >= 7) confidence = 90;
  else if (sampleSize >= 5) confidence = 75;
  else if (sampleSize >= 3) confidence = 60;
  else if (sampleSize >= 2) confidence = 40;
  else confidence = 20;
  
  // Adjust based on consistency
  const { cityConsistency, stdDevPrice, avgPrice, stdDevSqm, avgSqm } = stats;
  
  // If user is very inconsistent, reduce confidence
  if (cityConsistency < 40) confidence *= 0.9;
  
  const cvPrice = avgPrice > 0 ? (stdDevPrice / avgPrice) : 1;
  const cvSize = avgSqm > 0 ? (stdDevSqm / avgSqm) : 1;
  
  if (cvPrice > 0.5 || cvSize > 0.5) confidence *= 0.85;
  
  return Math.round(confidence);
}

// Helper: check if two properties are essentially the same
function isSameProperty(a, b) {
  if (!a || !b) return false;
  if (a.id && b.id) return a.id === b.id;
  return a.title === b.title && a.buyingPrice === b.buyingPrice;
}

// Helper: Calculate match score for property (0-100)
function calculateMatchScore(p, profile) {
  if (!profile) return 0;

  let score = 0;
  // Use dynamic weights from profile, or fallback to defaults
  let weights = profile.weights || { city: 25, price: 35, size: 30, rooms: 10 };
  let scores = {};

  const city = p.address &&
    (p.address.city || p.address.displayName || p.address._normalized_city);

  // City matching (25%)
  if (city && profile.preferredCity) {
    if (city === profile.preferredCity) {
      scores.city = 100;
    } else if (profile.alternativeCities && profile.alternativeCities.includes(city)) {
      scores.city = 70;
    } else {
      scores.city = 0;
    }
  } else {
    scores.city = 0;
  }

  // Price matching (35%) - now considering average preference
  const price = p.buyingPrice;
  if (typeof price === "number" && price > 0 && profile.minPrice && profile.maxPrice && profile.avgPrice) {
    const priceRange = profile.maxPrice - profile.minPrice;
    const buffer = Math.max(priceRange * 0.3, 50000);  // 30% buffer, min 50k
    const lower = profile.minPrice - buffer;
    const upper = profile.maxPrice + buffer;
    
    if (price >= profile.minPrice && price <= profile.maxPrice) {
      // Within user's liked range
      // Give higher score if closer to average
      const distanceFromAvg = Math.abs(price - profile.avgPrice);
      const maxDistanceFromAvg = Math.max(
        profile.avgPrice - profile.minPrice,
        profile.maxPrice - profile.avgPrice
      );
      
      // 100 points if exactly at average, scales down as it moves away
      scores.price = Math.max(80, 100 - (distanceFromAvg / maxDistanceFromAvg) * 20);
    } else if (price >= lower && price <= upper) {
      // Good match: within buffer zone
      const distanceFromRange = price < profile.minPrice 
        ? profile.minPrice - price
        : price - profile.maxPrice;
      scores.price = Math.max(50, 80 - (distanceFromRange / buffer) * 30);
    } else {
      // No match: outside buffer
      scores.price = 0;
    }
  } else {
    scores.price = 0;
  }

  // Size matching (30%) - CRITICAL CHECK, now considering average
  const sqm = p.squareMeter || p.livingSpace;
  if (typeof sqm === "number" && sqm > 0 && profile.minSqm && profile.maxSqm && profile.avgSqm) {
    // Data validation: reject clearly wrong data
    if (sqm < 15) {
      // Less than 15 m² is unrealistic for an apartment
      scores.size = 0;
    } else {
      const sizeRange = profile.maxSqm - profile.minSqm;
      const buffer = Math.max(sizeRange * 0.3, 15);  // 30% buffer, min 15 m²
      const lower = profile.minSqm - buffer;
      const upper = profile.maxSqm + buffer;
      
      if (sqm >= profile.minSqm && sqm <= profile.maxSqm) {
        // Within user's liked range
        // Give higher score if closer to average
        const distanceFromAvg = Math.abs(sqm - profile.avgSqm);
        const maxDistanceFromAvg = Math.max(
          profile.avgSqm - profile.minSqm,
          profile.maxSqm - profile.avgSqm
        );
        
        // 100 points if exactly at average, scales down as it moves away
        scores.size = Math.max(80, 100 - (distanceFromAvg / maxDistanceFromAvg) * 20);
      } else if (sqm >= lower && sqm <= upper) {
        // Good match: within buffer zone
        const distanceFromRange = sqm < profile.minSqm
          ? profile.minSqm - sqm
          : sqm - profile.maxSqm;
        scores.size = Math.max(50, 80 - (distanceFromRange / buffer) * 30);
      } else {
        // No match: outside buffer
        scores.size = 0;
      }
    }
  } else {
    scores.size = 0;
  }

  // Room matching (10%)
  const rooms = p.rooms;
  if (typeof rooms === "number" && rooms > 0 && profile.avgRooms !== null) {
    const roomDiff = Math.abs(rooms - profile.avgRooms);
    if (roomDiff === 0) {
      scores.rooms = 100;
    } else if (roomDiff <= 1) {
      scores.rooms = 70;
    } else if (roomDiff <= 2) {
      scores.rooms = 40;
    } else {
      scores.rooms = 0;
    }
  } else {
    scores.rooms = 0;
  }

  // Calculate weighted average
  const totalScore = 
    (scores.city || 0) * (weights.city / 100) +
    (scores.price || 0) * (weights.price / 100) +
    (scores.size || 0) * (weights.size / 100) +
    (scores.rooms || 0) * (weights.rooms / 100);

  // Match calculation complete

  // Critical fields must be valid
  // If price OR size is 0 (invalid/unrealistic), heavily penalize
  if (scores.price === 0 || scores.size === 0) {
    return Math.round(totalScore * 0.3);
  }

  // Apply penalty if too many categories are missing/zero
  const validScores = Object.values(scores).filter(s => s > 0).length;
  if (validScores < 3) {
    return Math.round(totalScore * 0.5);
  }

  return Math.round(totalScore);
}

// Helper: Check if property matches profile (threshold: 60%)
function matchesProfile(p, profile) {
  return calculateMatchScore(p, profile) >= 60;
}

// --------------------------------------------------------
// Recommendations: new homes similar to liked, not just liked
function renderRecommendations() {
  if (!recSection || !recContainer) return;

  recContainer.innerHTML = "";

  const profile = buildPreferenceProfile(likedProperties);
  if (!profile || !allProperties.length) {
    recSection.style.display = "none";
    return;
  }

  // Calculate match scores and filter
  const scoredProperties = allProperties
    .filter((p) => {
      const liked = likedProperties.some((lp) => isSameProperty(lp, p));
      return !liked;
    })
    .map((p) => ({
      property: p,
      score: calculateMatchScore(p, profile)
    }))
    .filter((item) => item.score >= 60)  // Only show matches above 60%
    .sort((a, b) => b.score - a.score);  // Sort by best match first

  // Add "surprise me" recommendation (1 wildcard between 45-59%)
  const surpriseProperties = allProperties
    .filter((p) => {
      const liked = likedProperties.some((lp) => isSameProperty(lp, p));
      const alreadyRecommended = scoredProperties.some(item => isSameProperty(item.property, p));
      return !liked && !alreadyRecommended;
    })
    .map((p) => ({
      property: p,
      score: calculateMatchScore(p, profile)
    }))
    .filter((item) => item.score >= 45 && item.score < 60)
    .sort((a, b) => b.score - a.score);
  
  // Add one surprise if available and confidence is high enough
  if (surpriseProperties.length > 0 && profile.confidence >= 60) {
    const surprise = surpriseProperties[0];
    surprise.isSurprise = true;
    scoredProperties.push(surprise);
    console.log('✨ Added surprise recommendation:', surprise.property.title, `(${surprise.score}% match)`);
  }

  // Show message if no matches
  if (scoredProperties.length === 0) {
    // If confidence is low, show helpful message
    if (profile.confidence < 60) {
      recContainer.innerHTML = `
        <div style="padding: 20px; text-align: center; color: #666;">
          <p style="font-size: 1.1rem; margin-bottom: 10px;">🤔 Need more data!</p>
          <p>Like a few more properties to get better recommendations.</p>
          <p style="font-size: 0.9rem; margin-top: 10px;">Confidence: ${profile.confidence}%</p>
        </div>
      `;
      recSection.style.display = "block";
    } else {
      recSection.style.display = "none";
    }
    return;
  }

  recSection.style.display = "block";

  // Show confidence indicator if less than perfect
  if (profile.confidence < 90) {
    recContainer.innerHTML = `
      <div style="padding: 15px; background: #f0f8ff; border-radius: 8px; margin-bottom: 15px; text-align: center;">
        <p style="margin: 0; color: #2c3e50;">📊 Recommendation Confidence: ${profile.confidence}%</p>
        <p style="margin: 5px 0 0 0; font-size: 0.85rem; color: #666;">
          ${profile.confidence < 60 ? 'Like more properties for better matches' : 'Good confidence level!'}
        </p>
      </div>
    `;
  }

  // Render top recommendations (limit to 10 for performance)
  scoredProperties.slice(0, 10).forEach((item) => {
    const p = item.property;
    const isSurprise = item.isSurprise || false;
    const matchPercent = Math.round(item.score);
    
    const title = p.title || "Untitled property";
    const price = p.buyingPrice ?? p.price ?? "N/A";
    const sqm = p.squareMeter ?? p.livingSpace ?? "N/A";
    const rooms = p.rooms ?? "N/A";
    const city =
      (p.address &&
        (p.address.city ||
          p.address.displayName ||
          p.address._normalized_city)) ||
      "Unknown location";

    const imgUrl =
      (p.images &&
        p.images[0] &&
        (p.images[0].originalUrl || p.images[0].url)) ||
      null;

    const card = document.createElement("div");
    card.className = "rec-card";
    card.innerHTML = `
      ${
        imgUrl
          ? `<div class="rec-image-wrapper">
               <img src="${imgUrl}"
                    alt="${title}"
                    onerror="this.style.display='none';" />
             </div>`
          : ""
      }
      <div class="rec-info">
        <h5>${title}</h5>
        <p>${city}</p>
        <p>${price === "N/A" ? "Price on request" : price + " €"} · ${
      sqm === "N/A" ? "?" : sqm
    } m² · ${rooms} rooms</p>
        ${isSurprise ? '<p style="margin-top: 8px;"><span style="background: #9b59b6; color: white; padding: 4px 10px; border-radius: 4px; font-size: 0.8rem;">✨ Surprise Pick</span></p>' : ''}
      </div>
    `;

    card.addEventListener("click", () => openDetail(p));
    recContainer.appendChild(card);
  });
  
  // Add "Continue Swiping" button at the end
  const continueButton = document.createElement("div");
  continueButton.style.cssText = "text-align: center; margin-top: 30px; padding: 20px;";
  continueButton.innerHTML = `
    <p style="color: #666; margin-bottom: 15px; font-size: 0.95rem;">
      Want to refine your matches? Swipe through more properties!
    </p>
    <button onclick="continueSwipingFromResults()" 
            style="padding: 12px 30px; background: #667eea; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 1rem; font-weight: 500; box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3); transition: all 0.3s;"
            onmouseover="this.style.transform='scale(1.05)'; this.style.boxShadow='0 4px 12px rgba(102, 126, 234, 0.4)'"
            onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='0 2px 8px rgba(102, 126, 234, 0.3)'">
      🔄 Continue Swiping
    </button>
  `;
  recContainer.appendChild(continueButton);
}

// Continue swiping from results page
function continueSwipingFromResults() {
  // Hide recommendations and liked sections
  if (recSection) recSection.style.display = "none";
  if (likedSection) likedSection.style.display = "none";
  
  // Show card container
  cardContainer.style.display = "block";
  
  // Load more properties
  loadMoreProperties();
  
  // Scroll to swipe section
  cardContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// --------------------------------------------------------
// Homes you liked in this session (simple list of liked)
function renderLikedHomes() {
  if (!likedSection || !likedContainer) return;

  likedContainer.innerHTML = "";

  if (!likedProperties.length) {
    likedSection.style.display = "none";
    return;
  }

  likedSection.style.display = "block";

  likedProperties.forEach((p) => {
    const title = p.title || "Untitled property";
    const price = p.buyingPrice ?? p.price ?? "N/A";
    const sqm = p.squareMeter ?? p.livingSpace ?? "N/A";
    const rooms = p.rooms ?? "N/A";
    const city =
      (p.address &&
        (p.address.city ||
          p.address.displayName ||
          p.address._normalized_city)) ||
      "Unknown location";

    const imgUrl =
      (p.images &&
        p.images[0] &&
        (p.images[0].originalUrl || p.images[0].url)) ||
      null;

    const card = document.createElement("div");
    card.className = "rec-card";
    card.innerHTML = `
      ${
        imgUrl
          ? `<div class="rec-image-wrapper">
               <img src="${imgUrl}"
                    alt="${title}"
                    onerror="this.style.display='none';" />
             </div>`
          : ""
      }
      <div class="rec-info">
        <h5>${title}</h5>
        <p>${city}</p>
        <p>${price === "N/A" ? "Price on request" : price + " €"} · ${
      sqm === "N/A" ? "?" : sqm
    } m² · ${rooms} rooms</p>
      </div>
    `;

    card.addEventListener("click", () => openDetail(p));
    likedContainer.appendChild(card);
  });
}

// --------------------------------------------------------
// Detail view for a single home (with original portal link)
function openDetail(p) {
  if (!detailSection) return;

  const title = p.title || "Untitled property";
  const price = p.buyingPrice ?? p.price ?? "N/A";
  const sqm = p.squareMeter ?? p.livingSpace ?? "N/A";
  const rooms = p.rooms ?? "N/A";
  const city =
    (p.address &&
      (p.address.city || p.address.displayName || p.address._normalized_city)) ||
    "Unknown location";

  const imgUrl =
    (p.images && p.images[0] && (p.images[0].originalUrl || p.images[0].url)) ||
    null;

  let platformUrl = null;
  if (Array.isArray(p.platforms) && p.platforms.length > 0) {
    platformUrl = p.platforms[0].url || null;
  }

  if (imgUrl) {
    detailImage.src = imgUrl;
    detailImage.style.display = "block";
  } else {
    detailImage.style.display = "none";
  }

  detailTitle.textContent = title;
  detailLocation.textContent = city;
  detailPrice.textContent =
    price === "N/A" ? "Price on request" : `Price: ${price} €`;
  detailSize.textContent = sqm === "N/A" ? "" : `Size: ${sqm} m²`;
  detailRooms.textContent =
    rooms === "N/A" ? "" : `Rooms: ${rooms}`;

  if (detailLink) {
    if (platformUrl) {
      detailLink.href = platformUrl;
      detailLink.style.display = "inline-block";
    } else {
      detailLink.style.display = "none";
    }
  }

  detailSection.style.display = "flex";
}

// --------------------------------------------------------
// Helper: most frequent value in array
function mostCommon(arr) {
  const counts = {};
  arr.forEach((item) => {
    counts[item] = (counts[item] || 0) + 1;
  });
  const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  return sorted[0][0];
}
