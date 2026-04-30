/** @odoo-module **/
/**
 * Dealer Management – Become a Dealer JS helpers
 * Works as plain ES5 for Odoo 17 website (no module bundler needed for simple tasks)
 */

(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', function () {

        // ── Image Preview ────────────────────────────────────────
        var shopImageInput = document.querySelector('input[name="shop_image"]');
        if (shopImageInput) {
            var preview = document.createElement('img');
            preview.className = 'img-thumbnail mt-2';
            preview.style.maxHeight = '120px';
            preview.style.display = 'none';
            shopImageInput.parentNode.appendChild(preview);

            shopImageInput.addEventListener('change', function () {
                var file = this.files[0];
                if (file && file.type.startsWith('image/')) {
                    var reader = new FileReader();
                    reader.onload = function (e) {
                        preview.src = e.target.result;
                        preview.style.display = 'block';
                    };
                    reader.readAsDataURL(file);
                }
            });
        }

        // ── Document file names preview ──────────────────────────
        var docsInput = document.querySelector('input[name="documents"]');
        if (docsInput) {
            var fileList = document.createElement('ul');
            fileList.className = 'list-unstyled small text-muted mt-1 mb-0';
            docsInput.parentNode.appendChild(fileList);

            docsInput.addEventListener('change', function () {
                fileList.innerHTML = '';
                Array.from(this.files).forEach(function (f) {
                    var li = document.createElement('li');
                    li.innerHTML = '<i class="fa fa-file-o me-1"></i>' + f.name;
                    fileList.appendChild(li);
                });
            });
        }

        // ── Form progress indicator ──────────────────────────────
        var form = document.getElementById('dealerApplicationForm');
        if (form) {
            var submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                form.addEventListener('submit', function () {
                    submitBtn.disabled = true;
                    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Submitting…';
                });
            }
        }

    });
})();
