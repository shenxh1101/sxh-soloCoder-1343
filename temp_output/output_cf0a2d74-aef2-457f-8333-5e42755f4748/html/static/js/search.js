(function() {
    var searchInput = document.getElementById('search-input');
    var searchResults = document.getElementById('search-results');
    var searchData = window.SEARCH_DATA || [];

    if (!searchInput || !searchResults) return;

    function debounce(func, wait) {
        var timeout;
        return function() {
            var context = this, args = arguments;
            clearTimeout(timeout);
            timeout = setTimeout(function() {
                func.apply(context, args);
            }, wait);
        };
    }

    function escapeHtml(text) {
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function highlight(text, query) {
        if (!query) return escapeHtml(text);
        var escapedQuery = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        var regex = new RegExp('(' + escapedQuery + ')', 'gi');
        return escapeHtml(text).replace(regex, '<mark>$1</mark>');
    }

    function search(query) {
        query = query.trim().toLowerCase();
        if (!query) {
            searchResults.style.display = 'none';
            return;
        }

        var results = searchData.filter(function(item) {
            return item.name.toLowerCase().indexOf(query) !== -1 ||
                   item.full_name.toLowerCase().indexOf(query) !== -1 ||
                   item.description.toLowerCase().indexOf(query) !== -1;
        });

        results.sort(function(a, b) {
            var aName = a.name.toLowerCase().indexOf(query) !== -1 ? 0 : 1;
            var bName = b.name.toLowerCase().indexOf(query) !== -1 ? 0 : 1;
            return aName - bName;
        });

        results = results.slice(0, 20);

        if (results.length === 0) {
            searchResults.innerHTML = '<div class="search-result-item"><div style="color: #999;">No results found</div></div>';
        } else {
            searchResults.innerHTML = results.map(function(item) {
                return '<div class="search-result-item" data-url="' + escapeHtml(item.url) + '">' +
                           '<span class="result-type ' + item.type + '">' + item.type.toUpperCase() + '</span>' +
                           '<span class="result-name">' + highlight(item.name, query) + '</span>' +
                           '<div class="result-desc">' + highlight(item.description, query) + '</div>' +
                       '</div>';
            }).join('');
        }

        searchResults.style.display = 'block';
    }

    searchInput.addEventListener('input', debounce(function() {
        search(searchInput.value);
    }, 150));

    searchInput.addEventListener('focus', function() {
        if (searchInput.value.trim()) {
            search(searchInput.value);
        }
    });

    document.addEventListener('click', function(e) {
        if (!searchResults.contains(e.target) && e.target !== searchInput) {
            searchResults.style.display = 'none';
        }
    });

    searchResults.addEventListener('click', function(e) {
        var item = e.target.closest('.search-result-item');
        if (item && item.dataset.url) {
            window.location.href = item.dataset.url;
        }
    });

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            searchResults.style.display = 'none';
        }
    });
})();
