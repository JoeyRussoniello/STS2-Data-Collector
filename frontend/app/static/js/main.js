/* STS2 Stats — Minimal client-side JS */
document.addEventListener('DOMContentLoaded', function () {
  // Auto-focus search input if empty
  const searchInput = document.querySelector('.search-input');
  if (searchInput && !searchInput.value) {
    // Don't steal focus on mobile
    if (window.innerWidth > 768) {
      // Delay slightly so page renders first
      setTimeout(() => searchInput.focus(), 100);
    }
  }
});
