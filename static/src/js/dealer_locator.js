/** Dealer Locator – Map + List with distance */
(function () {
    'use strict';

    var allDealers = [];
    var markers = [];
    var map = null;
    var userLat = null, userLng = null;
    var infoWindow = null;

    // ── Fetch dealer data from backend ────────────────────────────────────────
    function fetchDealers(lat, lng) {
        return fetch('/dealer/map/data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                jsonrpc: '2.0', method: 'call',
                params: { lat: lat || null, lng: lng || null }
            })
        })
        .then(r => r.json())
        .then(function (resp) {
            return (resp.result && resp.result.dealers) || [];
        });
    }

    // ── Render the sidebar list ───────────────────────────────────────────────
    function renderList(dealers) {
        var container = document.getElementById('dealer_list_container');
        if (!container) return;
        if (!dealers.length) {
            container.innerHTML = '<p class="text-muted text-center py-4">No dealers found.</p>';
            return;
        }
        var html = '';
        dealers.forEach(function (d) {
            var stars = '';
            for (var i = 1; i <= 5; i++) {
                stars += '<i class="fa fa-star' + (i <= Math.round(d.rating) ? '' : '-o') + ' dealer-star-' + (i <= Math.round(d.rating) ? 'full' : 'empty') + '"></i>';
            }
            var distHtml = d.distance_km !== null
                ? '<p class="text-info small mb-1"><i class="fa fa-location-arrow me-1"></i>' + d.distance_km + ' km away</p>'
                : '';
            html += '<div class="dealer-list-item border rounded p-3 mb-2" data-id="' + d.id + '">' +
                '<h6 class="fw-bold mb-1">' + escHtml(d.name) + '</h6>' +
                '<p class="text-muted small mb-1"><i class="fa fa-map-marker me-1"></i>' + escHtml(d.city) + (d.state ? ', ' + escHtml(d.state) : '') + '</p>' +
                '<div class="mb-1">' + stars + ' <small class="text-muted">(' + d.review_count + ')</small></div>' +
                distHtml +
                '<div class="small text-muted"><i class="fa fa-tag me-1"></i>' + escHtml(d.plan || '') + '</div>' +
                '</div>';
        });
        container.innerHTML = html;

        // Click handlers
        container.querySelectorAll('.dealer-list-item').forEach(function (el) {
            el.addEventListener('click', function () {
                var id = parseInt(this.getAttribute('data-id'));
                var dealer = dealers.find(function (d) { return d.id === id; });
                if (dealer) focusDealer(dealer);
            });
        });
    }

    // ── Place markers on map ──────────────────────────────────────────────────
    function placeMarkers(dealers) {
        markers.forEach(function (m) { m.setMap(null); });
        markers = [];
        dealers.forEach(function (d) {
            if (!d.lat || !d.lng) return;
            var marker = new google.maps.Marker({
                position: { lat: d.lat, lng: d.lng },
                map: map,
                title: d.name,
            });
            marker.addListener('click', function () { focusDealer(d, marker); });
            markers.push(marker);
            d._marker = marker;
        });
    }

    // ── Focus/open info window ────────────────────────────────────────────────
    function focusDealer(d, marker) {
        if (!map) return;
        marker = marker || d._marker;
        if (!infoWindow) infoWindow = new google.maps.InfoWindow();

        var imgHtml = d.images && d.images.length
            ? '<img src="' + d.images[0] + '" style="width:100%;height:90px;object-fit:cover;border-radius:4px;margin-bottom:6px;" />'
            : '';
        var stars = '';
        for (var i = 1; i <= 5; i++) {
            stars += '<i class="fa fa-star' + (i <= Math.round(d.rating) ? '' : '-o') + '" style="color:' + (i <= d.rating ? '#f39c12' : '#ccc') + '"></i>';
        }
        var distHtml = d.distance_km !== null
            ? '<p style="color:#3498db;margin:4px 0 0;font-size:13px;"><i class="fa fa-location-arrow"></i> ' + d.distance_km + ' km away</p>'
            : '';

        var content = '<div class="dealer-info-window" style="max-width:250px;font-family:inherit;">' +
            imgHtml +
            '<h6 style="margin:0 0 4px;font-weight:700;">' + escHtml(d.name) + '</h6>' +
            '<p style="margin:0 0 2px;color:#666;font-size:13px;">' + escHtml(d.city) + '</p>' +
            '<div>' + stars + '</div>' +
            distHtml +
            (d.phone ? '<p style="margin:4px 0 0;font-size:13px;"><i class="fa fa-phone"></i> ' + escHtml(d.phone) + '</p>' : '') +
            '</div>';

        infoWindow.setContent(content);
        if (marker) {
            infoWindow.open(map, marker);
            map.panTo(marker.getPosition());
            map.setZoom(14);
        }

        // Highlight sidebar item
        document.querySelectorAll('.dealer-list-item').forEach(function (el) {
            el.classList.toggle('active-dealer', parseInt(el.getAttribute('data-id')) === d.id);
        });
        var activeEl = document.querySelector('.dealer-list-item[data-id="' + d.id + '"]');
        if (activeEl) activeEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    // ── Search filter ─────────────────────────────────────────────────────────
    function setupSearch() {
        var input = document.getElementById('dealer_search_input');
        if (!input) return;
        input.addEventListener('input', function () {
            var q = this.value.toLowerCase();
            var filtered = allDealers.filter(function (d) {
                return d.name.toLowerCase().includes(q) || (d.city || '').toLowerCase().includes(q);
            });
            renderList(filtered);
            placeMarkers(filtered);
        });
    }

    // ── Fallback: OpenStreetMap/Leaflet (no API key) ──────────────────────────
    function initLeafletMap() {
        if (typeof L === 'undefined') return false;
        var mapEl = document.getElementById('dealer_map');
        if (!mapEl) return false;
        map = L.map('dealer_map').setView([23.8103, 90.4125], 7);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);

        fetchDealers().then(function (dealers) {
            allDealers = dealers;
            renderList(dealers);
            dealers.forEach(function (d) {
                if (!d.lat || !d.lng) return;
                var m = L.marker([d.lat, d.lng]).addTo(map);
                var popHtml = '<b>' + escHtml(d.name) + '</b><br>' + escHtml(d.city || '');
                m.bindPopup(popHtml);
                d._marker = m;
            });
        });
        return true;
    }

    // ── Google Maps init ──────────────────────────────────────────────────────
    window.initDealerMap = function () {
        var mapEl = document.getElementById('dealer_map');
        if (!mapEl) return;
        map = new google.maps.Map(mapEl, {
            center: { lat: 23.8103, lng: 90.4125 },
            zoom: 7,
            mapTypeControl: false,
            streetViewControl: false,
        });

        fetchDealers().then(function (dealers) {
            allDealers = dealers;
            renderList(dealers);
            placeMarkers(dealers);
        });

        // My location button
        var btnLoc = document.getElementById('btn_use_my_location');
        if (btnLoc) {
            btnLoc.addEventListener('click', function () {
                if (!navigator.geolocation) { alert('Geolocation not supported.'); return; }
                btnLoc.innerHTML = '<i class="fa fa-spinner fa-spin me-1"></i> Locating...';
                btnLoc.disabled = true;
                navigator.geolocation.getCurrentPosition(function (pos) {
                    userLat = pos.coords.latitude;
                    userLng = pos.coords.longitude;
                    map.setCenter({ lat: userLat, lng: userLng });
                    map.setZoom(12);
                    new google.maps.Marker({
                        position: { lat: userLat, lng: userLng },
                        map: map,
                        title: 'You are here',
                        icon: { path: google.maps.SymbolPath.CIRCLE, scale: 8, fillColor: '#3498db', fillOpacity: 1, strokeColor: '#fff', strokeWeight: 2 }
                    });
                    fetchDealers(userLat, userLng).then(function (dealers) {
                        allDealers = dealers;
                        renderList(dealers);
                        placeMarkers(dealers);
                        btnLoc.innerHTML = '<i class="fa fa-check me-1"></i> Located';
                        btnLoc.classList.replace('btn-primary', 'btn-success');
                    });
                }, function () {
                    btnLoc.innerHTML = '<i class="fa fa-crosshairs me-1"></i> Use My Location';
                    btnLoc.disabled = false;
                });
            });
        }
    };

    // ── Init on DOMContentLoaded ──────────────────────────────────────────────
    document.addEventListener('DOMContentLoaded', function () {
        if (!document.getElementById('dealer_map')) return;
        setupSearch();

        if (typeof GMAPS_API_KEY !== 'undefined' && GMAPS_API_KEY) {
            var script = document.createElement('script');
            script.src = 'https://maps.googleapis.com/maps/api/js?key=' + GMAPS_API_KEY + '&callback=initDealerMap';
            script.async = true;
            script.defer = true;
            document.head.appendChild(script);
        } else {
            // Try Leaflet fallback
            var leafletCSS = document.createElement('link');
            leafletCSS.rel = 'stylesheet';
            leafletCSS.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
            document.head.appendChild(leafletCSS);
            var leafletJS = document.createElement('script');
            leafletJS.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
            leafletJS.onload = function () { initLeafletMap(); };
            document.head.appendChild(leafletJS);
        }
    });

    function escHtml(str) {
        if (!str) return '';
        return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    }
})();
