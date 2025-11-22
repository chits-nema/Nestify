// Sample home listings data
const homes = [
    {
        id: 1,
        title: "Modern Family House",
        location: "Seattle, WA",
        price: 650000,
        bedrooms: 4,
        bathrooms: 3,
        sqft: 2500,
        type: "house",
        image: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        featured: true
    },
    {
        id: 2,
        title: "Downtown Luxury Apartment",
        location: "New York, NY",
        price: 850000,
        bedrooms: 2,
        bathrooms: 2,
        sqft: 1200,
        type: "apartment",
        image: "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
        featured: false
    },
    {
        id: 3,
        title: "Cozy Suburban Townhouse",
        location: "Portland, OR",
        price: 425000,
        bedrooms: 3,
        bathrooms: 2.5,
        sqft: 1800,
        type: "townhouse",
        image: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
        featured: false
    },
    {
        id: 4,
        title: "Beachfront Condo",
        location: "Miami, FL",
        price: 725000,
        bedrooms: 3,
        bathrooms: 2,
        sqft: 1600,
        type: "condo",
        image: "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
        featured: true
    },
    {
        id: 5,
        title: "Spacious Ranch House",
        location: "Austin, TX",
        price: 495000,
        bedrooms: 5,
        bathrooms: 3,
        sqft: 3200,
        type: "house",
        image: "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
        featured: false
    },
    {
        id: 6,
        title: "Urban Studio Apartment",
        location: "San Francisco, CA",
        price: 550000,
        bedrooms: 1,
        bathrooms: 1,
        sqft: 650,
        type: "apartment",
        image: "linear-gradient(135deg, #30cfd0 0%, #330867 100%)",
        featured: false
    },
    {
        id: 7,
        title: "Mountain View Estate",
        location: "Denver, CO",
        price: 950000,
        bedrooms: 6,
        bathrooms: 4,
        sqft: 4500,
        type: "house",
        image: "linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)",
        featured: true
    },
    {
        id: 8,
        title: "Historic Downtown Condo",
        location: "Boston, MA",
        price: 675000,
        bedrooms: 2,
        bathrooms: 2,
        sqft: 1400,
        type: "condo",
        image: "linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)",
        featured: false
    },
    {
        id: 9,
        title: "Lakeside Family Home",
        location: "Minneapolis, MN",
        price: 585000,
        bedrooms: 4,
        bathrooms: 3,
        sqft: 2800,
        type: "house",
        image: "linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)",
        featured: false
    },
    {
        id: 10,
        title: "Modern Loft Apartment",
        location: "Chicago, IL",
        price: 475000,
        bedrooms: 2,
        bathrooms: 2,
        sqft: 1100,
        type: "apartment",
        image: "linear-gradient(135deg, #ff6e7f 0%, #bfe9ff 100%)",
        featured: false
    }
];

// Store favorites in memory
let favorites = new Set();

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    displayHomes(homes);
    
    // Handle contact form submission
    const contactForm = document.querySelector('.contact-form');
    contactForm.addEventListener('submit', function(e) {
        e.preventDefault();
        alert('Thank you for your message! We\'ll get back to you soon.');
        contactForm.reset();
    });

    // Smooth scrolling for navigation links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});

// Display homes in the listings grid
function displayHomes(homesToDisplay) {
    const container = document.getElementById('listingsContainer');
    const noResults = document.getElementById('noResults');
    
    container.innerHTML = '';
    
    if (homesToDisplay.length === 0) {
        noResults.style.display = 'block';
        return;
    }
    
    noResults.style.display = 'none';
    
    homesToDisplay.forEach(home => {
        const card = createHomeCard(home);
        container.appendChild(card);
    });
}

// Create a home card element
function createHomeCard(home) {
    const card = document.createElement('div');
    card.className = 'listing-card';
    card.onclick = () => showHomeDetails(home);
    
    const isFavorite = favorites.has(home.id);
    
    card.innerHTML = `
        <div class="listing-image" style="background: ${home.image}">
            ${home.featured ? '<div class="listing-badge">Featured</div>' : ''}
        </div>
        <div class="listing-content">
            <div class="listing-price">$${home.price.toLocaleString()}</div>
            <div class="listing-title">${home.title}</div>
            <div class="listing-location">📍 ${home.location}</div>
            <div class="listing-details">
                <div class="detail-item">🛏️ ${home.bedrooms} Beds</div>
                <div class="detail-item">🚿 ${home.bathrooms} Baths</div>
                <div class="detail-item">📏 ${home.sqft.toLocaleString()} sqft</div>
            </div>
            <button class="favorite-btn ${isFavorite ? 'active' : ''}" onclick="toggleFavorite(event, ${home.id})">
                ${isFavorite ? '❤️' : '🤍'}
            </button>
        </div>
    `;
    
    return card;
}

// Toggle favorite status
function toggleFavorite(event, homeId) {
    event.stopPropagation();
    
    if (favorites.has(homeId)) {
        favorites.delete(homeId);
    } else {
        favorites.add(homeId);
    }
    
    // Refresh the display
    applyFilters();
}

// Show home details (could be expanded to modal)
function showHomeDetails(home) {
    alert(`${home.title}\n\nLocation: ${home.location}\nPrice: $${home.price.toLocaleString()}\nBedrooms: ${home.bedrooms}\nBathrooms: ${home.bathrooms}\nSquare Feet: ${home.sqft.toLocaleString()}\nType: ${home.type.charAt(0).toUpperCase() + home.type.slice(1)}\n\nClick the heart icon to save this home to your favorites!`);
}

// Search functionality
function searchHomes() {
    const searchInput = document.getElementById('searchInput').value.toLowerCase();
    
    if (!searchInput.trim()) {
        displayHomes(homes);
        return;
    }
    
    const filtered = homes.filter(home => {
        return home.title.toLowerCase().includes(searchInput) ||
               home.location.toLowerCase().includes(searchInput) ||
               home.type.toLowerCase().includes(searchInput);
    });
    
    displayHomes(filtered);
    
    // Scroll to listings
    document.getElementById('listings').scrollIntoView({ behavior: 'smooth' });
}

// Apply filters
function applyFilters() {
    const typeFilter = document.getElementById('typeFilter').value;
    const bedroomFilter = document.getElementById('bedroomFilter').value;
    const priceFilter = document.getElementById('priceFilter').value;
    const searchInput = document.getElementById('searchInput').value.toLowerCase();
    
    let filtered = homes;
    
    // Apply type filter
    if (typeFilter !== 'all') {
        filtered = filtered.filter(home => home.type === typeFilter);
    }
    
    // Apply bedroom filter
    if (bedroomFilter !== 'all') {
        filtered = filtered.filter(home => home.bedrooms >= parseInt(bedroomFilter));
    }
    
    // Apply price filter
    if (priceFilter !== 'all') {
        filtered = filtered.filter(home => home.price <= parseInt(priceFilter));
    }
    
    // Apply search filter
    if (searchInput.trim()) {
        filtered = filtered.filter(home => {
            return home.title.toLowerCase().includes(searchInput) ||
                   home.location.toLowerCase().includes(searchInput) ||
                   home.type.toLowerCase().includes(searchInput);
        });
    }
    
    displayHomes(filtered);
}

// Handle Enter key in search input
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchHomes();
            }
        });
    }
});
