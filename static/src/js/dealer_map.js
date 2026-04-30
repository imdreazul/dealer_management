/* Dealer Management – Find a Dealer map logic
 * Loaded via web.assets_frontend. Depends on Leaflet loaded inline in template.
 * Server data is injected by the template as: window.DEALER_MAP_DATA
 */
(function () {
    'use strict';

    var DEALERS = [];
    var map, userMarker = null, userLat = null, userLng = null;
    var dealerMarkers = {}, polylines = [];

    function escHtml(s) {
        return String(s)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    function blueIcon() {
        return L.divIcon({
            className: '',
            html: '<div style="width:36px;height:36px;background:#1565c0;border-radius:50% 50% 50% 0;border:3px solid #fff;box-shadow:0 2px 8px rgba(0,0,0,0.3);transform:rotate(-45deg);"></div>',
            iconSize: [36, 36], iconAnchor: [18, 36], popupAnchor: [0, -38]
        });
    }

    function myIcon() {
        return L.divIcon({
            className: '',
            html: '<div style="width:18px;height:18px;background:#43a047;border-radius:50%;border:3px solid #fff;box-shadow:0 0 0 3px rgba(67,160,71,0.3);"></div>',
            iconSize: [18, 18], iconAnchor: [9, 9]
        });
    }

    function haversineDist(lat1, lng1, lat2, lng2) {
        var R = 6371;
        var dL = (lat2 - lat1) * Math.PI / 180;
        var dN = (lng2 - lng1) * Math.PI / 180;
        var a = Math.sin(dL / 2) * Math.sin(dL / 2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dN / 2) * Math.sin(dN / 2);
        return (R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))).toFixed(1);
    }

    function buildDrawerCard(d) {
        var el = document.createElement('div');

        if (d.has_image) {
            var img = document.createElement('img');
            img.src = '/web/image/dealership.application/' + d.id + '/shop_image/400x160';
            img.style.cssText = 'width:100%;height:140px;object-fit:cover;border-radius:10px;margin-bottom:14px;';
            el.appendChild(img);
        }

        if (userLat !== null && d.lat && d.lng) {
            var distBadge = document.createElement('div');
            distBadge.className = 'mb-2';
            distBadge.innerHTML = '<span style="background:#e3f2fd;color:#1565c0;border-radius:12px;padding:2px 10px;font-size:0.8rem;">' +
                '<i class="fa fa-location-arrow me-1"></i>' +
                haversineDist(userLat, userLng, d.lat, d.lng) + ' km away</span>';
            el.appendChild(distBadge);
        }

        var title = document.createElement('h6');
        title.style.cssText = 'font-weight:700;margin-bottom:10px;';
        title.textContent = d.name || '';
        el.appendChild(title);

        var rows = [
            d.city || d.country ? ['fa-map-marker', 'Location', (d.city || '') + (d.country ? (d.city ? ', ' : '') + d.country : '')] : null,
            d.phone ? ['fa-phone', 'Phone', d.phone, 'tel:' + d.phone] : null,
            d.email ? ['fa-envelope', 'Email', d.email, 'mailto:' + d.email] : null,
            d.website ? ['fa-globe', 'Website', d.website, d.website, true] : null,
        ].filter(Boolean);

        if (rows.length) {
            var table = document.createElement('table');
            table.style.cssText = 'width:100%;border-collapse:collapse;background:#f8f9fa;border-radius:8px;overflow:hidden;';
            rows.forEach(function (r) {
                var tr = document.createElement('tr');
                var td1 = document.createElement('td');
                td1.style.cssText = 'padding:6px 10px;color:#888;font-size:0.82rem;white-space:nowrap;';
                td1.innerHTML = '<i class="fa ' + r[0] + ' me-1"></i>' + r[1];
                var td2 = document.createElement('td');
                td2.style.cssText = 'padding:6px 10px;font-size:0.82rem;';
                if (r[3]) {
                    var a = document.createElement('a');
                    a.href = r[3];
                    a.textContent = r[2];
                    if (r[4]) { a.target = '_blank'; a.rel = 'noopener'; }
                    td2.appendChild(a);
                } else {
                    td2.textContent = r[2];
                }
                tr.appendChild(td1);
                tr.appendChild(td2);
                table.appendChild(tr);
            });
            el.appendChild(table);
        }

        return el;
    }

    function openDrawer(d) {
        var titleEl = document.getElementById('drawerTitle');
        var contentEl = document.getElementById('drawerContent');
        var drawer = document.getElementById('dealerDrawer');
        var inner = document.getElementById('dealerDrawerInner');
        var backdrop = document.getElementById('drawerBackdrop');
        if (!titleEl || !contentEl || !drawer) return;

        titleEl.textContent = d.name || 'Dealer Details';
        contentEl.innerHTML = '';
        contentEl.appendChild(buildDrawerCard(d));
        drawer.style.display = 'block';
        backdrop.style.display = 'block';
        requestAnimationFrame(function () {
            inner.style.transform = 'translateY(0)';
        });
    }

    function closeDrawer() {
        var inner = document.getElementById('dealerDrawerInner');
        if (!inner) return;
        inner.style.transform = 'translateY(100%)';
        setTimeout(function () {
            var drawer = document.getElementById('dealerDrawer');
            var backdrop = document.getElementById('drawerBackdrop');
            if (drawer) drawer.style.display = 'none';
            if (backdrop) backdrop.style.display = 'none';
        }, 300);
    }

    // Exposed globally for onclick handlers
    window.dealerMapCloseDrawer = closeDrawer;

    function focusDealer(id) {
        var d = DEALERS.find(function (x) { return x.id === id; });
        if (!d) return;
        if (d.lat && d.lng) {
            map.flyTo([d.lat, d.lng], 14, { duration: 1.2 });
            if (dealerMarkers[id]) dealerMarkers[id].openPopup();
        }
        openDrawer(d);
        document.querySelectorAll('.dealer-list-card').forEach(function (c) {
            c.style.background = parseInt(c.dataset.id) === id ? '#e3f2fd' : '';
        });
    }
    window.dealerMapFocusDealer = focusDealer;

    function initMap() {
        var mapEl = document.getElementById('dealerMap');
        if (!mapEl || typeof L === 'undefined') return;

        DEALERS = window.DEALER_MAP_DATA || [];
        var withCoords = DEALERS.filter(function (d) { return d.lat && d.lng; });
        var defLat = 20, defLng = 0, defZoom = 2;
        if (withCoords.length === 1) { defLat = withCoords[0].lat; defLng = withCoords[0].lng; defZoom = 13; }

        map = L.map('dealerMap', { zoomControl: true }).setView([defLat, defLng], defZoom);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap</a>',
            maxZoom: 19
        }).addTo(map);

        DEALERS.forEach(function (d) {
            if (!d.lat || !d.lng) return;
            var marker = L.marker([d.lat, d.lng], { icon: blueIcon() }).addTo(map);

            // Build popup using DOM to stay XML-safe
            var popupDiv = document.createElement('div');
            popupDiv.style.minWidth = '180px';

            if (d.has_image) {
                var img = document.createElement('img');
                img.src = '/web/image/dealership.application/' + d.id + '/shop_image/240x90';
                img.style.cssText = 'width:100%;height:90px;object-fit:cover;border-radius:6px;margin-bottom:8px;';
                popupDiv.appendChild(img);
            }

            var strong = document.createElement('strong');
            strong.style.cssText = 'display:block;margin-bottom:4px;';
            strong.textContent = d.name || '';
            popupDiv.appendChild(strong);

            if (d.city) {
                var small = document.createElement('small');
                small.style.color = '#888';
                small.textContent = d.city + (d.country ? ', ' + d.country : '');
                popupDiv.appendChild(small);
                popupDiv.appendChild(document.createElement('br'));
            }

            var btn = document.createElement('button');
            btn.textContent = 'View Details';
            btn.style.cssText = 'margin-top:8px;width:100%;background:#1565c0;color:#fff;border:none;border-radius:6px;padding:6px;cursor:pointer;font-size:0.8rem;';
            btn.addEventListener('click', (function (dealer) {
                return function () { focusDealer(dealer.id); };
            })(d));
            popupDiv.appendChild(btn);

            marker.bindPopup(popupDiv, { maxWidth: 260 });
            marker.on('click', (function (dealer) {
                return function () { openDrawer(dealer); };
            })(d));
            dealerMarkers[d.id] = marker;
        });

        if (withCoords.length > 1) {
            map.fitBounds(
                L.latLngBounds(withCoords.map(function (d) { return [d.lat, d.lng]; })).pad(0.15)
            );
        }

        // Locate me
        var locBtn = document.getElementById('locateMeBtn');
        if (locBtn) {
            locBtn.addEventListener('click', function () {
                if (!navigator.geolocation) { alert('Geolocation not supported.'); return; }
                locBtn.innerHTML = '<i class="fa fa-spinner fa-spin me-1"></i>Locating\u2026';
                navigator.geolocation.getCurrentPosition(function (pos) {
                    userLat = pos.coords.latitude;
                    userLng = pos.coords.longitude;
                    locBtn.innerHTML = '<i class="fa fa-location-arrow me-1"></i>My Location';
                    if (userMarker) map.removeLayer(userMarker);
                    userMarker = L.marker([userLat, userLng], { icon: myIcon() })
                        .addTo(map).bindPopup('<strong>Your Location</strong>').openPopup();
                    map.flyTo([userLat, userLng], 10, { duration: 1.5 });
                    polylines.forEach(function (p) { map.removeLayer(p); });
                    polylines = [];
                    withCoords.forEach(function (d) {
                        polylines.push(
                            L.polyline([[userLat, userLng], [d.lat, d.lng]], {
                                color: '#1565c0', weight: 1.5, opacity: 0.3, dashArray: '6,10'
                            }).addTo(map)
                        );
                    });
                }, function () {
                    locBtn.innerHTML = '<i class="fa fa-location-arrow me-1"></i>My Location';
                    alert('Could not retrieve your location.');
                });
            });
        }

        // Drawer backdrop + ESC
        var backdrop = document.getElementById('drawerBackdrop');
        if (backdrop) backdrop.addEventListener('click', closeDrawer);
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') closeDrawer();
        });
    }

    // Initialise after Leaflet is loaded (Leaflet loads synchronously via CDN script tag in template)
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () {
            // Leaflet might not be loaded yet — poll briefly
            var tries = 0;
            var poll = setInterval(function () {
                tries++;
                if (typeof L !== 'undefined') { clearInterval(poll); initMap(); }
                else if (tries > 20) { clearInterval(poll); }
            }, 100);
        });
    } else {
        var tries = 0;
        var poll = setInterval(function () {
            tries++;
            if (typeof L !== 'undefined') { clearInterval(poll); initMap(); }
            else if (tries > 20) { clearInterval(poll); }
        }, 100);
    }

})();
