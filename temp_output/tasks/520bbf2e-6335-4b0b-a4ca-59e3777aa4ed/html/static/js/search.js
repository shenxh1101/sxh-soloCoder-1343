(function() {
    var searchInput = document.getElementById('search-input');
    var searchResults = document.getElementById('search-results');
    var searchData = window.SEARCH_DATA || [];
    var basePath = (searchInput && searchInput.getAttribute('data-base-path')) || '';

    if (!searchInput || !searchResults) return;

    var TYPE_ORDER = { 'class': 0, 'interface': 1, 'function': 2, 'method': 3, 'module': 4 };
    var TYPE_LABELS = { 'module': 'MODULE', 'class': 'CLASS', 'interface': 'IFACE', 'function': 'FUNC', 'method': 'METHOD' };

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
                   (item.module_path && item.module_path.toLowerCase().indexOf(query) !== -1) ||
                   item.description.toLowerCase().indexOf(query) !== -1;
        });

        results.sort(function(a, b) {
            var aName = a.name.toLowerCase().indexOf(query) !== -1 ? 0 : 1;
            var bName = b.name.toLowerCase().indexOf(query) !== -1 ? 0 : 1;
            if (aName !== bName) return aName - bName;
            var aType = TYPE_ORDER[a.type] !== undefined ? TYPE_ORDER[a.type] : 99;
            var bType = TYPE_ORDER[b.type] !== undefined ? TYPE_ORDER[b.type] : 99;
            return aType - bType;
        });

        results = results.slice(0, 30);

        if (results.length === 0) {
            searchResults.innerHTML = '<div class="search-result-item"><div style="color: #999;">No results found</div></div>';
        } else {
            var grouped = {};
            results.forEach(function(item) {
                var group = item.type;
                if (!grouped[group]) grouped[group] = [];
                grouped[group].push(item);
            });

            var html = '';
            var groupOrder = ['class', 'interface', 'function', 'method', 'module'];
            groupOrder.forEach(function(group) {
                if (!grouped[group]) return;
                var label = TYPE_LABELS[group] || group.toUpperCase();
                var count = grouped[group].length;
                html += '<div class="search-group"><div class="search-group-header">' +
                        '<span class="search-group-type ' + group + '">' + label + '</span>' +
                        '<span class="search-group-count">' + count + ' result' + (count > 1 ? 's' : '') + '</span></div>';
                grouped[group].forEach(function(item) {
                    var modulePath = item.module_path ? escapeHtml(item.module_path) : '';
                    html += '<div class="search-result-item" data-url="' + escapeHtml(basePath + item.url) + '">' +
                            '<span class="result-type ' + item.type + '">' + (TYPE_LABELS[item.type] || item.type.toUpperCase()) + '</span>' +
                            '<span class="result-name">' + highlight(item.name, query) + '</span>' +
                            (modulePath ? '<span class="result-path">' + highlight(modulePath, query) + '</span>' : '') +
                            '<div class="result-desc">' + highlight(item.description, query) + '</div>' +
                            '</div>';
                });
                html += '</div>';
            });

            searchResults.innerHTML = html;
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
            var url = item.dataset.url;
            var hashIndex = url.indexOf('#');
            if (hashIndex !== -1 && window.location.pathname.replace(/\/[^/]*\.html$/, '') === url.substring(0, url.lastIndexOf('/')).replace(/\/[^/]*\.html$/, '')) {
                var hash = url.substring(hashIndex + 1);
                var element = document.getElementById(hash) || document.querySelector('[id="' + hash + '"]');
                if (element) {
                    element.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    element.classList.add('search-highlight');
                    setTimeout(function() { element.classList.remove('search-highlight'); }, 3000);
                    searchResults.style.display = 'none';
                    return;
                }
            }
            window.location.href = url;
        }
    });

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            searchResults.style.display = 'none';
        }
    });

    function handleHashHighlight() {
        var hash = window.location.hash;
        if (hash) {
            var id = hash.substring(1);
            var element = document.getElementById(id) || document.querySelector('[id="' + id + '"]');
            if (element) {
                setTimeout(function() {
                    element.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    element.classList.add('search-highlight');
                    setTimeout(function() { element.classList.remove('search-highlight'); }, 3000);
                }, 100);
            }
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', handleHashHighlight);
    } else {
        handleHashHighlight();
    }
})();
