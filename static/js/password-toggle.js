/**
 * AUTO FINDING AI - Universal Password Visibility Toggle Component
 * Status Mode:
 *   - When password is hidden (dots / type="password"): displays Crossed-Eye (lucide-eye-off).
 *   - When password is visible (plain text / type="text"): displays Open Eye (lucide-eye).
 */
(function(window) {
    'use strict';

    const PasswordVisibility = {
        // Built-in SVG templates matching Lucide design
        icons: {
            eye: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-eye"><path d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"/><circle cx="12" cy="12" r="3"/></svg>',
            eyeOff: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-eye-off"><path d="M10.733 5.076a10.744 10.744 0 0 1 11.205 6.575 1 1 0 0 1 0 .696 10.747 10.747 0 0 1-1.444 2.49"/><path d="M14.084 14.158a3 3 0 0 1-4.242-4.242"/><path d="M17.479 17.499a10.75 10.75 0 0 1-15.417-5.151 1 1 0 0 1 0-.696 10.75 10.75 0 0 1 4.446-5.143"/><path d="m2 2 20 20"/></svg>'
        },

        /**
         * Strictly synchronize button icon, tooltip, and aria attributes to the input's current type
         * Status Mode:
         *   - Visible (type="text") -> Open Eye (icons.eye), title "Hide password"
         *   - Hidden (type="password") -> Crossed-Eye (icons.eyeOff), title "Show password"
         * @param {HTMLInputElement} input
         * @param {HTMLButtonElement} [btnEl]
         */
        sync(input, btnEl) {
            if (!input) return;
            let btn = btnEl;
            if (!btn && input.parentElement) {
                btn = input.parentElement.querySelector('.password-toggle-btn');
            }
            if (!btn) return;

            const isVisible = (input.type === 'text');
            // When visible, show Open Eye; when hidden, show Crossed-Eye (Eye-Off)
            btn.innerHTML = isVisible ? this.icons.eye : this.icons.eyeOff;
            const label = isVisible ? 'Hide password' : 'Show password';
            btn.setAttribute('title', label);
            btn.setAttribute('aria-label', label);
        },

        /**
         * Toggle visibility for an input element
         * @param {string|HTMLInputElement} inputOrId 
         * @param {HTMLButtonElement} [btnEl] 
         */
        toggle(inputOrId, btnEl) {
            const input = typeof inputOrId === 'string' ? document.getElementById(inputOrId) : inputOrId;
            if (!input) return;

            // Debounce rapid duplicate invocations (within 200ms)
            const now = Date.now();
            if (input._lastToggleTime && (now - input._lastToggleTime < 200)) {
                return;
            }
            input._lastToggleTime = now;

            // Toggle state: password -> text -> password
            if (input.type === 'password') {
                input.type = 'text';
            } else {
                input.type = 'password';
            }

            // Find or use button
            let btn = btnEl;
            if (!btn && input.parentElement) {
                btn = input.parentElement.querySelector('.password-toggle-btn');
            }

            this.sync(input, btn);
        },

        /**
         * Reset an input back to masked password mode
         * @param {string|HTMLInputElement} inputOrId 
         */
        reset(inputOrId) {
            const input = typeof inputOrId === 'string' ? document.getElementById(inputOrId) : inputOrId;
            if (!input) return;

            input.type = 'password';
            this.sync(input);
        },

        /**
         * Attach eye toggle button to a password input element
         * @param {HTMLInputElement} input 
         */
        attach(input) {
            if (!input || input.getAttribute('data-has-password-toggle') === 'true') return;

            // Mark as processed
            input.setAttribute('data-has-password-toggle', 'true');

            // Check if wrapper already exists
            let wrapper = input.parentElement;
            if (!wrapper) return;

            if (!wrapper.classList.contains('password-input-wrapper') && !wrapper.classList.contains('input-group')) {
                wrapper = document.createElement('div');
                wrapper.className = 'password-input-wrapper';
                input.parentNode.insertBefore(wrapper, input);
                wrapper.appendChild(input);
            }

            // Ensure input has right padding for the icon
            input.style.paddingRight = '42px';

            // Check if button already exists in wrapper
            let btn = wrapper.querySelector('.password-toggle-btn');
            if (!btn) {
                btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'password-toggle-btn';
                btn.setAttribute('tabindex', '-1');
                wrapper.appendChild(btn);
            }

            // Bind click event cleanly
            btn.onclick = (e) => {
                if (e) {
                    e.preventDefault();
                    e.stopPropagation();
                }
                this.toggle(input, btn);
            };

            // Ensure initial sync
            this.sync(input, btn);
        },

        /**
         * Scan root for any password inputs and attach toggles
         * @param {HTMLElement} [root] 
         */
        init(root = document) {
            const inputs = root.querySelectorAll('input[type="password"]');
            inputs.forEach(input => this.attach(input));
        },

        /**
         * Setup automatic DOM mutation observer to catch dynamically rendered password fields
         */
        setupObserver() {
            if (typeof MutationObserver === 'undefined' || !document.body) return;
            const observer = new MutationObserver((mutations) => {
                for (const mutation of mutations) {
                    if (mutation.addedNodes && mutation.addedNodes.length > 0) {
                        for (const node of mutation.addedNodes) {
                            if (node.nodeType === 1) { // ELEMENT_NODE
                                if (node.tagName === 'INPUT' && (node.type === 'password' || node.getAttribute('data-password-field') === 'true')) {
                                    this.attach(node);
                                } else if (node.querySelectorAll) {
                                    const pws = node.querySelectorAll('input[type="password"]');
                                    pws.forEach(input => this.attach(input));
                                }
                            }
                        }
                    }
                }
            });

            observer.observe(document.body, { childList: true, subtree: true });
        }
    };

    window.PasswordVisibility = PasswordVisibility;

    // Self-initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            PasswordVisibility.init();
            PasswordVisibility.setupObserver();
        });
    } else {
        PasswordVisibility.init();
        PasswordVisibility.setupObserver();
    }
})(window);
