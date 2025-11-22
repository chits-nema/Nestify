// tinder.js – Tinder-style swipe UI using backend (FastAPI)
// --------------------------------------------------------

// Global state
let properties = [];
let currentIndex = 0;
let likedProperties = [];

// Adjust if you run backend on a different port
const BACKEND_URL = "http://127.0.0.1:8000";

// DOM elements
const cardContainer = document.getElementById("card-container");
const statusText = document.getElementById("status-text");
const likeBtn = document.getElementById("like-btn");
const nopeBtn = document.getElementById("nope-btn");

// When page finished loading, fetch first batch
document.addEventListener("DOMContentLoaded", () => {
  // later you can replace "Munich"/"BY" with user choice or Pinterest logic
  fetchProperties("Munich", "BY");
});

// ---- Fetch properties from backend (which calls ThinkImmo or demo data) ----
async function fetchProperties(city, region) {
  if (!cardContainer) return; // safety

  statusText.textContent = "Loading properties...";
  cardContainer.innerHTML = "<p>Loading properties...</p>";

  try {
    const res = await fetch(`${BACKEND_URL}/api/properties/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        city: city,
        region: region,
        size: 20,
        from_index: 0,
        propertyType: "APPARTMENTBUY"
      })
    });

    const data = await res.json();

    // Expecting { results: [...] } from backend (real or demo)
    properties = Array.isArray(data.results) ? data.results : [];
    currentIndex = 0;

    if (properties.length === 0) {
      cardContainer.innerHTML = "<p>No properties found in this area.</p>";
      statusText.textContent = "";
      return;
    }

    showCurrentProperty();
    statusText.textContent = "";
  } catch (err) {
    console.error(err);
    cardContainer.innerHTML = "<p>Error loading properties.</p>";
    statusText.textContent = "Could not load properties.";
  }
}

// ---- Render the current property card ----
function showCurrentProperty() {
  if (!properties.length) {
    cardContainer.innerHTML = "<p>No properties.</p>";
    return;
  }

  if (currentIndex >= properties.length) {
    cardContainer.innerHTML = "<p>You've reached the end of this batch.</p>";
    return;
  }

  const p = properties[currentIndex];

  const title = p.title || "Untitled property";
  const price = p.buyingPrice ?? p.price ?? "N/A";
  const sqm = p.squareMeter ?? p.livingSpace ?? "N/A";
  const rooms = p.rooms ?? "N/A";
  const city =
    p.address?.city ||
    p.address?.displayName ||
    p.address?._normalized_city ||
    "Unknown location";

  const imgUrl =
    (p.images && p.images[0] && (p.images[0].originalUrl || p.images[0].url)) ||
    null;

  cardContainer.innerHTML = `
    <div class="card">
      ${imgUrl ? `<img src="${imgUrl}" alt="${title}" class="card-image" />` : ""}
      <div class="card-content">
        <h2 class="card-title">${title}</h2>
        <p class="card-price">${
          price === "N/A" ? "Price on request" : price + " €"
        }</p>
        <p class="card-details">${sqm} m² · ${rooms} rooms</p>
        <p class="card-location">${city}</p>
      </div>
    </div>
  `;
}

// ---- Like / Nope button logic ----
if (likeBtn && nopeBtn) {
  likeBtn.addEventListener("click", handleLike);
  nopeBtn.addEventListener("click", handleNope);
}

function handleLike() {
  if (currentIndex >= properties.length) return;

  const current = properties[currentIndex];
  likedProperties.push(current);
  currentIndex += 1;

  // every 5 likes, "learn" preferences and refetch
  if (likedProperties.length > 0 && likedProperties.length % 5 === 0) {
    applyLearningAndRefetch();
  } else {
    showCurrentProperty();
  }
}

function handleNope() {
  if (currentIndex >= properties.length) return;
  currentIndex += 1;
  showCurrentProperty();
}

// ---- Simple preference learning (no ML, just rules) ----
function applyLearningAndRefetch() {
  if (likedProperties.length === 0) return;

  // preferred city: most common in liked homes
  const cities = likedProperties
    .map((p) => p.address?.city || p.address?._normalized_city)
    .filter(Boolean);

  let preferredCity = "Munich";
  if (cities.length > 0) {
    preferredCity = mostCommon(cities);
  }

  // (optional) price range – currently only for logging
  const prices = likedProperties
    .map((p) => p.buyingPrice)
    .filter((v) => typeof v === "number");

  let minPrice = null;
  let maxPrice = null;
  if (prices.length > 0) {
    minPrice = Math.min(...prices);
    maxPrice = Math.max(...prices);
  }

  console.log("Learning from likes:", {
    preferredCity,
    minPrice,
    maxPrice
  });

  statusText.textContent = `Learning your style… showing more homes in ${preferredCity}.`;

  // For now: re-fetch with new city, same region
  fetchProperties(preferredCity, "BY");
}

// helper: most frequent value in array
function mostCommon(arr) {
  const counts = {};
  arr.forEach((item) => {
    counts[item] = (counts[item] || 0) + 1;
  });
  return Object.entries(counts).sort((a, b) => b[1] - a[1])[0][0];
}
