// UX Enhancements: Loader & Modal

// Loader Logic
// Loader Logic
window.addEventListener('load', () => {
    const loader = document.getElementById('page-loader');
    if (loader) {
        // Fade out loader
        loader.style.opacity = '0';
        setTimeout(() => {
            loader.style.display = 'none';
        }, 500);
    }
});

// Failsafe: Force remove loader after 5 seconds in case load event hangs
setTimeout(() => {
    const loader = document.getElementById('page-loader');
    if (loader && loader.style.display !== 'none') {
        loader.style.opacity = '0';
        setTimeout(() => {
            loader.style.display = 'none';
        }, 500);
    }
}, 3000);

// Handle Link Clicks to show loader
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            // Only show loader for internal navigation, not for JS actions or anchors
            if (href && (href.startsWith('/') || href.startsWith('./') || href.startsWith('..')) && !href.startsWith('#') && !href.startsWith('javascript')) {
                // Check if it's a download link
                if (this.hasAttribute('download')) return;

                const loader = document.getElementById('page-loader');
                if (loader) {
                    loader.style.display = 'flex';
                    // Short delay to allow display:flex to apply before opacity
                    setTimeout(() => { loader.style.opacity = '1'; }, 10);
                }
            }
        });
    });
});

// Profile Modal Logic
function toggleProfileModal(event) {
    if (event) event.stopPropagation();
    const modal = document.getElementById('profile-modal');
    if (modal) {
        const isVisible = modal.style.display === 'block';
        modal.style.display = isVisible ? 'none' : 'block';
    }
}

// Close modal when clicking outside
document.addEventListener('click', (event) => {
    const modal = document.getElementById('profile-modal');
    // Check if the click target is NOT the avatar toggle
    // We assume the avatar toggle stops propagation, but if it bubbles here, we check
    // The toggle has onclick="toggleProfileModal(event)", which stops prop.
    // So any click reaching here is "outside" or "unhandled".
    if (modal && modal.style.display === 'block') {
        // If click is inside modal, do nothing (stopPropagation in modal click listener handles this)
        // If click is outside, close.
        modal.style.display = 'none';
    }
});

// Stop propagation on modal click to prevent closing
document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('profile-modal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }
});
