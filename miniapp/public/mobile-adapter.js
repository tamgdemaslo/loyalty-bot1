/**
 * Модуль адаптации для мобильного интерфейса
 * Улучшает отображение на мобильных устройствах
 */

class MobileAdapter {
    constructor() {
        this.isMobile = window.innerWidth < 768;
        this.init();
    }

    /**
     * Инициализация адаптера
     */
    init() {
        // Слушаем изменение размера окна
        window.addEventListener('resize', this.handleResize.bind(this));
        
        // Применяем начальные настройки
        this.applyMobileOptimizations();
        
        // Добавляем обработчики для панели навигации
        this.setupMobileNavigation();
    }

    /**
     * Обработка изменения размера окна
     */
    handleResize() {
        this.isMobile = window.innerWidth < 768;
        this.applyMobileOptimizations();
    }

    /**
     * Применение оптимизаций для мобильных устройств
     */
    applyMobileOptimizations() {
        const root = document.documentElement;
        
        if (this.isMobile) {
            root.classList.add('mobile-view');
            this.enableSwipeNavigation();
            this.optimizeLayout();
        } else {
            root.classList.remove('mobile-view');
            this.disableSwipeNavigation();
            this.restoreLayout();
        }
    }

    /**
     * Настройка мобильной навигации
     */
    setupMobileNavigation() {
        const mobileMenu = document.getElementById('mobile-menu-btn');
        if (mobileMenu) {
            mobileMenu.addEventListener('click', this.toggleMobileMenu.bind(this));
        }
        
        // Добавление функциональности закрытия меню при клике вне его
        document.addEventListener('click', (e) => {
            const menu = document.getElementById('mobile-menu');
            const menuBtn = document.getElementById('mobile-menu-btn');
            
            if (menu && !menu.classList.contains('hidden') && 
                e.target !== menu && !menu.contains(e.target) && 
                e.target !== menuBtn && !menuBtn.contains(e.target)) {
                this.toggleMobileMenu(false);
            }
        });
    }

    /**
     * Переключение мобильного меню
     * @param {boolean|Event} showOrEvent - Показать меню или событие клика
     */
    toggleMobileMenu(showOrEvent) {
        const menu = document.getElementById('mobile-menu');
        const btn = document.getElementById('mobile-menu-btn');
        
        if (!menu || !btn) return;
        
        let show = showOrEvent;
        if (typeof showOrEvent !== 'boolean') {
            show = menu.classList.contains('hidden');
        }
        
        if (show) {
            menu.classList.remove('hidden');
            btn.innerHTML = '<span class="text-xl">✕</span>';
        } else {
            menu.classList.add('hidden');
            btn.innerHTML = '<span class="text-xl">☰</span>';
        }
    }

    /**
     * Включение свайп-навигации для мобильных устройств
     */
    enableSwipeNavigation() {
        let touchStartX = 0;
        let touchEndX = 0;
        
        const handleSwipe = () => {
            const swipeThreshold = 100; // минимальное расстояние для считывания свайпа
            
            if (touchStartX - touchEndX > swipeThreshold) {
                // Свайп влево - следующая страница
                this.navigateNext();
            } else if (touchEndX - touchStartX > swipeThreshold) {
                // Свайп вправо - предыдущая страница
                this.navigatePrevious();
            }
        };
        
        document.addEventListener('touchstart', (e) => {
            touchStartX = e.changedTouches[0].screenX;
        }, { passive: true });
        
        document.addEventListener('touchend', (e) => {
            touchEndX = e.changedTouches[0].screenX;
            handleSwipe();
        }, { passive: true });
    }

    /**
     * Отключение свайп-навигации
     */
    disableSwipeNavigation() {
        document.removeEventListener('touchstart', () => {});
        document.removeEventListener('touchend', () => {});
    }

    /**
     * Оптимизация макета для мобильных устройств
     */
    optimizeLayout() {
        // Увеличение размера кнопок для удобства нажатия
        document.querySelectorAll('.btn, button, .clickable').forEach(el => {
            el.classList.add('touch-friendly');
        });
        
        // Оптимизация форм
        document.querySelectorAll('input, select, textarea').forEach(el => {
            el.classList.add('mobile-input');
        });
        
        // Адаптация заголовков и текста
        document.querySelectorAll('h1').forEach(el => {
            el.classList.add('mobile-h1');
        });
        
        document.querySelectorAll('h2, h3').forEach(el => {
            el.classList.add('mobile-heading');
        });
    }

    /**
     * Восстановление стандартного макета
     */
    restoreLayout() {
        // Возврат размера кнопок к стандартному
        document.querySelectorAll('.btn, button, .clickable').forEach(el => {
            el.classList.remove('touch-friendly');
        });
        
        // Возврат стилей форм
        document.querySelectorAll('input, select, textarea').forEach(el => {
            el.classList.remove('mobile-input');
        });
        
        // Возврат стилей заголовков
        document.querySelectorAll('h1').forEach(el => {
            el.classList.remove('mobile-h1');
        });
        
        document.querySelectorAll('h2, h3').forEach(el => {
            el.classList.remove('mobile-heading');
        });
    }

    /**
     * Навигация к следующей странице
     */
    navigateNext() {
        const pages = ['dashboard', 'visits', 'transactions', 'maintenance', 'booking', 'profile'];
        const currentPage = window.currentPage || 'dashboard';
        const currentIndex = pages.indexOf(currentPage);
        
        if (currentIndex < pages.length - 1) {
            const nextPage = pages[currentIndex + 1];
            if (typeof window.showPage === 'function') {
                window.showPage(nextPage);
            }
        }
    }

    /**
     * Навигация к предыдущей странице
     */
    navigatePrevious() {
        const pages = ['dashboard', 'visits', 'transactions', 'maintenance', 'booking', 'profile'];
        const currentPage = window.currentPage || 'dashboard';
        const currentIndex = pages.indexOf(currentPage);
        
        if (currentIndex > 0) {
            const prevPage = pages[currentIndex - 1];
            if (typeof window.showPage === 'function') {
                window.showPage(prevPage);
            }
        }
    }
}

// Экспорт для использования в других модулях
window.MobileAdapter = MobileAdapter;

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.mobileAdapter = new MobileAdapter();
});
