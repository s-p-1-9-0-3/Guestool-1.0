// ===== BUTTON HIDER - Ocultar botones del nav una vez se renderizan =====
(function hideInvisibleButtons() {
    function hideBtnsNow() {
        const buttonsToHide = ['Wizard', 'Guestool', 'tab_nuevo', 'tab_editar', 'sub_sim', 'sub_rent'];
        const allButtons = document.querySelectorAll('button');
        
        allButtons.forEach(btn => {
            const btnText = btn.textContent.trim();
            if (buttonsToHide.includes(btnText)) {
                // Ocultar agresivamente
                btn.style.display = 'none !important';
                btn.style.visibility = 'hidden';
                btn.style.position = 'absolute';
                btn.style.left = '-9999px';
                btn.style.height = '0';
                btn.style.width = '0';
                btn.style.padding = '0';
                btn.style.margin = '0';
                btn.style.border = 'none';
                
                // Ocultar el contenedor del botón también
                const parent = btn.closest('[data-testid="stButton"]');
                if (parent) {
                    parent.style.display = 'none !important';
                    parent.style.visibility = 'hidden';
                    parent.style.height = '0';
                    parent.style.margin = '0';
                }
            }
        });
    }
    
    // Ejecutar inmediatamente
    hideBtnsNow();
    
    // Re-ejecutar periódicamente por si Streamlit re-renderiza
    setInterval(hideBtnsNow, 500);
    
    // También observar cambios en el DOM
    const obs = new MutationObserver(hideBtnsNow);
    obs.observe(document.body, { childList: true, subtree: true });
})();

// ===== CARD CLICK WIRING - Wirear clicks de tarjetas a botones =====
(function wireCardClicks() {
    const wireMap = {
        'nc-wizard': 'Wizard',
        'nc-guestool': 'Guestool',
        'wiz-tab-nuevo': 'tab_nuevo',
        'wiz-tab-editar': 'tab_editar',
        'sub-sim': 'sub_sim',
        'sub-rent': 'sub_rent'
    };
    
    function findButton(label) {
        const allButtons = document.querySelectorAll('button');
        for (const btn of allButtons) {
            if (btn.textContent.trim() === label) {
                return btn;
            }
        }
        return null;
    }
    
    function wireElement(elemId, btnLabel) {
        const element = document.getElementById(elemId);
        if (!element || element._wired) return;
        
        element._wired = true;
        element.style.cursor = 'pointer';
        
        element.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const btn = findButton(btnLabel);
            if (btn) {
                console.log('✓ Clicking:', btnLabel);
                btn.click();
            } else {
                console.warn('✗ Button not found:', btnLabel);
            }
        });
    }
    
    // Wire cada elemento
    Object.entries(wireMap).forEach(([elemId, btnLabel]) => {
        wireElement(elemId, btnLabel);
    });
    
    // Re-wire cada segundo para capturar elementos nuevos
    setInterval(() => {
        Object.entries(wireMap).forEach(([elemId, btnLabel]) => {
            wireElement(elemId, btnLabel);
        });
    }, 1000);
})();

// ===== PARALLAX SCROLL - Auto scroll suave cuando usuario interactúa =====
(function parallaxScroll() {
    document.addEventListener('click', function(e) {
        const target = e.target;
        
        // Detectar tarjetas y triggers
        const isCard = target.closest('.nav-card') || 
                      target.closest('.subnav-card') ||
                      target.closest('[id^="nc-"]') ||
                      target.closest('[id^="sub-"]') ||
                      target.closest('[id^="wiz-"]');
        
        if (isCard) {
            // Scroll más abajo (para ver contenido)
            setTimeout(() => {
                const cardElement = target.closest('.nav-card') || 
                                   target.closest('.subnav-card') ||
                                   target.closest('div[id]');
                
                if (cardElement) {
                    // Scroll con offset hacia abajo
                    const rect = cardElement.getBoundingClientRect();
                    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
                    const targetY = scrollTop + rect.top - 100; // 100px offset desde top
                    
                    window.scrollTo({
                        top: targetY,
                        behavior: 'smooth'
                    });
                }
            }, 100);
        }
    }, true);
    
    // Scroll al hacer foco en inputs
    const obs = new MutationObserver(() => {
        const activeInput = document.activeElement;
        if (activeInput && (activeInput.tagName === 'INPUT' || activeInput.tagName === 'SELECT')) {
            activeInput.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    });
    
    obs.observe(document.body, { childList: true, subtree: true, attributes: true });
})();
