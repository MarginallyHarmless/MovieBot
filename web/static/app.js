/**
 * SGPL Movies - Client-side search, filter, sort, and seen toggle functionality
 */

document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('search-input');
    const genreFilters = document.getElementById('genre-filters');
    const movieGrid = document.getElementById('movie-grid');
    const emptyState = document.getElementById('empty-state');
    const seenFilterBtns = document.querySelectorAll('.seen-filter .filter-btn');
    const sortSelect = document.getElementById('sort-select');

    let currentGenre = 'all';
    let currentSearch = '';
    let currentSeenFilter = 'all';

    /**
     * Filter and sort movies
     */
    function filterAndSortMovies() {
        const cards = Array.from(movieGrid.querySelectorAll('.movie-card'));
        let visibleCount = 0;

        // First, filter cards
        cards.forEach(card => {
            const title = card.dataset.title || '';
            const genres = card.dataset.genres || '';
            const seen = card.dataset.seen === 'true';

            // Check search match
            const matchesSearch = currentSearch === '' ||
                title.includes(currentSearch.toLowerCase());

            // Check genre match
            const matchesGenre = currentGenre === 'all' ||
                genres.split(',').includes(currentGenre);

            // Check seen filter
            let matchesSeen = true;
            if (currentSeenFilter === 'seen') {
                matchesSeen = seen;
            } else if (currentSeenFilter === 'not-seen') {
                matchesSeen = !seen;
            }

            // Show/hide card
            if (matchesSearch && matchesGenre && matchesSeen) {
                card.classList.remove('hidden');
                visibleCount++;
            } else {
                card.classList.add('hidden');
            }
        });

        // Sort visible cards
        const sortOrder = sortSelect ? sortSelect.value : 'newest';
        const visibleCards = cards.filter(c => !c.classList.contains('hidden'));

        visibleCards.sort((a, b) => {
            const dateA = new Date(a.dataset.added || 0);
            const dateB = new Date(b.dataset.added || 0);

            if (sortOrder === 'newest') {
                return dateB - dateA;
            } else {
                return dateA - dateB;
            }
        });

        // Reorder in DOM
        visibleCards.forEach(card => {
            movieGrid.appendChild(card);
        });

        // Show empty state if no results
        if (emptyState) {
            emptyState.style.display = visibleCount === 0 ? 'block' : 'none';
        }
    }

    /**
     * Handle search input
     */
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            currentSearch = e.target.value.trim();
            filterAndSortMovies();
        });

        // Clear search on Escape key
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                searchInput.value = '';
                currentSearch = '';
                filterAndSortMovies();
            }
        });
    }

    /**
     * Handle genre filter clicks
     */
    if (genreFilters) {
        genreFilters.addEventListener('click', (e) => {
            if (e.target.classList.contains('genre-tag')) {
                // Update active state
                genreFilters.querySelectorAll('.genre-tag').forEach(tag => {
                    tag.classList.remove('active');
                });
                e.target.classList.add('active');

                // Update filter
                currentGenre = e.target.dataset.genre;
                filterAndSortMovies();
            }
        });
    }

    /**
     * Handle seen filter clicks
     */
    seenFilterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Update active state
            seenFilterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Update filter
            currentSeenFilter = btn.dataset.filter;
            filterAndSortMovies();
        });
    });

    /**
     * Handle sort change
     */
    if (sortSelect) {
        sortSelect.addEventListener('change', () => {
            filterAndSortMovies();
        });
    }

    /**
     * Handle seen toggle clicks
     */
    movieGrid.addEventListener('click', async (e) => {
        const toggleBtn = e.target.closest('.seen-toggle');
        if (!toggleBtn) return;

        const card = toggleBtn.closest('.movie-card');
        if (!card) return;

        const movieId = card.dataset.id;
        if (!movieId) return;

        // Optimistic UI update
        const wasSeen = card.dataset.seen === 'true';
        card.dataset.seen = wasSeen ? 'false' : 'true';
        card.classList.toggle('seen');

        // Update button text
        const textSpan = toggleBtn.querySelector('.seen-text');
        if (textSpan) {
            textSpan.textContent = wasSeen ? 'Mark as Seen' : 'Seen';
        }

        // Send request to server
        try {
            const response = await fetch(`/api/movies/${movieId}/toggle-seen`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error('Failed to update');
            }

            const data = await response.json();

            // Update with server response (in case of mismatch)
            card.dataset.seen = data.seen ? 'true' : 'false';
            if (data.seen) {
                card.classList.add('seen');
                if (textSpan) textSpan.textContent = 'Seen';
            } else {
                card.classList.remove('seen');
                if (textSpan) textSpan.textContent = 'Mark as Seen';
            }

            // Re-filter in case seen filter is active
            filterAndSortMovies();

        } catch (error) {
            console.error('Error toggling seen status:', error);

            // Revert on error
            card.dataset.seen = wasSeen ? 'true' : 'false';
            card.classList.toggle('seen');
            if (textSpan) {
                textSpan.textContent = wasSeen ? 'Seen' : 'Mark as Seen';
            }
        }
    });

    /**
     * Keyboard shortcuts
     */
    document.addEventListener('keydown', (e) => {
        // Focus search on '/' key (like many search interfaces)
        if (e.key === '/' && document.activeElement !== searchInput) {
            e.preventDefault();
            searchInput?.focus();
        }
    });

    // Initial sort
    filterAndSortMovies();
});
