(function() {
    'use strict';

    function toggleHoldReasonField() {
        var statusField = document.getElementById('id_status');
        var holdReasonRow = document.querySelector('.field-hold_reason');

        if (!statusField || !holdReasonRow) {
            return;
        }

        function updateHoldReasonVisibility() {
            var selectedStatus = statusField.value;

            if (selectedStatus === 'hold') {
                holdReasonRow.style.display = '';
                // Make the field required when status is hold
                var holdReasonTextarea = document.getElementById('id_hold_reason');
                if (holdReasonTextarea) {
                    holdReasonTextarea.setAttribute('required', 'required');
                    // Add a visual indicator
                    var label = holdReasonRow.querySelector('label');
                    if (label && !label.classList.contains('required')) {
                        label.classList.add('required');
                    }
                }
            } else {
                holdReasonRow.style.display = 'none';
                // Remove required attribute when not hold
                var holdReasonTextarea = document.getElementById('id_hold_reason');
                if (holdReasonTextarea) {
                    holdReasonTextarea.removeAttribute('required');
                    var label = holdReasonRow.querySelector('label');
                    if (label) {
                        label.classList.remove('required');
                    }
                }
            }
        }

        // Initial check
        updateHoldReasonVisibility();

        // Listen for changes
        statusField.addEventListener('change', updateHoldReasonVisibility);
    }

    // Run when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', toggleHoldReasonField);
    } else {
        toggleHoldReasonField();
    }
})();
