/** Dealer Application Page – location detect & state loader */
document.addEventListener('DOMContentLoaded', function () {

    // Detect location button
    var btnDetect = document.getElementById('btn_detect_location');
    if (btnDetect) {
        btnDetect.addEventListener('click', function () {
            if (!navigator.geolocation) {
                alert('Geolocation is not supported by your browser.');
                return;
            }
            btnDetect.innerHTML = '<i class="fa fa-spinner fa-spin me-1"></i> Detecting...';
            btnDetect.disabled = true;
            navigator.geolocation.getCurrentPosition(
                function (pos) {
                    document.getElementById('dealer_lat').value = pos.coords.latitude.toFixed(7);
                    document.getElementById('dealer_lng').value = pos.coords.longitude.toFixed(7);
                    btnDetect.innerHTML = '<i class="fa fa-check me-1"></i> Location Detected';
                    btnDetect.classList.replace('btn-outline-secondary', 'btn-success');
                },
                function () {
                    btnDetect.innerHTML = '<i class="fa fa-crosshairs me-1"></i> Detect My Location';
                    btnDetect.disabled = false;
                    alert('Unable to detect location. Please enter manually.');
                }
            );
        });
    }

    // Country → State AJAX loader
    var countrySelect = document.getElementById('country_id');
    var stateSelect = document.getElementById('state_id');
    if (countrySelect && stateSelect) {
        countrySelect.addEventListener('change', function () {
            var countryId = this.value;
            stateSelect.innerHTML = '<option value="">Loading...</option>';
            if (!countryId) {
                stateSelect.innerHTML = '<option value="">-- State --</option>';
                return;
            }
            fetch('/dealer/states', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ jsonrpc: '2.0', method: 'call', params: { country_id: countryId } })
            })
            .then(r => r.json())
            .then(function (resp) {
                var states = resp.result || [];
                stateSelect.innerHTML = '<option value="">-- State --</option>';
                states.forEach(function (s) {
                    var opt = document.createElement('option');
                    opt.value = s.id;
                    opt.textContent = s.name;
                    stateSelect.appendChild(opt);
                });
            })
            .catch(function () {
                stateSelect.innerHTML = '<option value="">-- State --</option>';
            });
        });
    }
});
