/**
 * SGPL Movies - Client-side search, filter, sort, and movie management
 */

document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('search-input');
    const genreFilters = document.getElementById('genre-filters');
    const movieGrid = document.getElementById('movie-grid');
    const emptyState = document.getElementById('empty-state');
    const seenFilterBtns = document.querySelectorAll('.seen-filter .filter-btn');
    const sortSelect = document.getElementById('sort-select');

    // Modal elements
    const addMovieBtn = document.getElementById('add-movie-btn');
    const modal = document.getElementById('add-movie-modal');
    const modalClose = document.getElementById('modal-close');
    const tmdbSearchInput = document.getElementById('tmdb-search-input');
    const searchResults = document.getElementById('search-results');

    let currentGenre = 'all';
    let currentSearch = '';
    let currentSeenFilter = 'not-seen';
    let searchTimeout = null;

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
     * Handle delete button clicks
     */
    movieGrid.addEventListener('click', async (e) => {
        const deleteBtn = e.target.closest('.delete-btn');
        if (!deleteBtn) return;

        e.stopPropagation();

        const card = deleteBtn.closest('.movie-card');
        if (!card) return;

        const movieId = card.dataset.id;
        const movieTitle = card.querySelector('.movie-title')?.textContent || 'this movie';

        if (!confirm(`Remove "${movieTitle}" from the collection?`)) {
            return;
        }

        try {
            const response = await fetch(`/api/movies/${movieId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error('Failed to delete');
            }

            // Remove card from DOM with animation
            card.style.opacity = '0';
            card.style.transform = 'scale(0.8)';
            setTimeout(() => {
                card.remove();
                filterAndSortMovies();
            }, 200);

        } catch (error) {
            console.error('Error deleting movie:', error);
            alert('Failed to delete movie. Please try again.');
        }
    });

    /**
     * Modal handling
     */
    function openModal() {
        modal.classList.add('active');
        tmdbSearchInput.value = '';
        searchResults.innerHTML = '';
        setTimeout(() => tmdbSearchInput.focus(), 100);
    }

    function closeModal() {
        modal.classList.remove('active');
    }

    if (addMovieBtn) {
        addMovieBtn.addEventListener('click', openModal);
    }

    if (modalClose) {
        modalClose.addEventListener('click', closeModal);
    }

    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal();
            }
        });
    }

    // Close modal on Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('active')) {
            closeModal();
        }
    });

    /**
     * TMDB Search
     */
    if (tmdbSearchInput) {
        tmdbSearchInput.addEventListener('input', (e) => {
            const query = e.target.value.trim();

            // Clear previous timeout
            if (searchTimeout) {
                clearTimeout(searchTimeout);
            }

            if (query.length < 2) {
                searchResults.innerHTML = '';
                return;
            }

            // Show loading
            searchResults.innerHTML = '<div class="search-loading">Searching...</div>';

            // Debounce search
            searchTimeout = setTimeout(async () => {
                try {
                    const response = await fetch(`/api/tmdb/search?q=${encodeURIComponent(query)}`);
                    const movies = await response.json();

                    if (movies.length === 0) {
                        searchResults.innerHTML = '<div class="search-empty">No movies found</div>';
                        return;
                    }

                    searchResults.innerHTML = movies.map(movie => `
                        <div class="search-result-item" data-tmdb-id="${movie.tmdb_id}">
                            ${movie.poster_url
                                ? `<img src="${movie.poster_url}" alt="${movie.title}">`
                                : '<div class="no-poster">No Image</div>'
                            }
                            <div class="search-result-info">
                                <h3>${movie.title}</h3>
                                <p>${movie.year || 'Unknown year'}${movie.genres?.length ? ' - ' + movie.genres.slice(0, 2).join(', ') : ''}</p>
                            </div>
                        </div>
                    `).join('');

                } catch (error) {
                    console.error('Search error:', error);
                    searchResults.innerHTML = '<div class="search-empty">Search failed. Please try again.</div>';
                }
            }, 300);
        });
    }

    /**
     * Handle search result clicks (add movie)
     */
    if (searchResults) {
        searchResults.addEventListener('click', async (e) => {
            const item = e.target.closest('.search-result-item');
            if (!item) return;

            const tmdbId = item.dataset.tmdbId;
            if (!tmdbId) return;

            // Show loading state
            item.style.opacity = '0.5';
            item.style.pointerEvents = 'none';

            try {
                const response = await fetch('/api/movies', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ tmdb_id: parseInt(tmdbId) })
                });

                const data = await response.json();

                if (response.status === 409) {
                    alert('This movie is already in the collection!');
                    item.style.opacity = '1';
                    item.style.pointerEvents = 'auto';
                    return;
                }

                if (!response.ok) {
                    throw new Error(data.error || 'Failed to add movie');
                }

                // Success - reload page to show new movie
                closeModal();
                window.location.reload();

            } catch (error) {
                console.error('Error adding movie:', error);
                alert('Failed to add movie. Please try again.');
                item.style.opacity = '1';
                item.style.pointerEvents = 'auto';
            }
        });
    }

    /**
     * Keyboard shortcuts
     */
    document.addEventListener('keydown', (e) => {
        // Focus search on '/' key (like many search interfaces)
        if (e.key === '/' && document.activeElement !== searchInput && !modal.classList.contains('active')) {
            e.preventDefault();
            searchInput?.focus();
        }
    });

    // Initial sort
    filterAndSortMovies();
});
