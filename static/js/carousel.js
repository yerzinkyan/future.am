document.addEventListener('DOMContentLoaded', function () {
    const track = document.getElementById('slidesTrack');
    if (!track) return;

    const slides = track.querySelectorAll('.slide');
    const dotsContainer = document.getElementById('dotsContainer');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const wrapper = document.getElementById('homeCarousel');

    let current = 0;
    const total = slides.length;
    let autoplayTimer = null;
    const AUTOPLAY_MS = 5000;

    slides.forEach((_, i) => {
        const dot = document.createElement('button');
        dot.className = 'carousel-dot' + (i === 0 ? ' active' : '');
        dot.addEventListener('click', () => goTo(i));
        dotsContainer.appendChild(dot);
    });
    const dots = dotsContainer.querySelectorAll('.carousel-dot');

    function render() {
        track.style.transform = `translateX(-${current * 100}%)`;
        dots.forEach((d, i) => d.classList.toggle('active', i === current));
    }

    function goTo(index) {
        current = (index + total) % total;
        render();
        resetAutoplay();
    }

    function next() { goTo(current + 1); }
    function prev() { goTo(current - 1); }

    function startAutoplay() {
        autoplayTimer = setInterval(next, AUTOPLAY_MS);
    }
    function resetAutoplay() {
        clearInterval(autoplayTimer);
        startAutoplay();
    }

    prevBtn.addEventListener('click', prev);
    nextBtn.addEventListener('click', next);

    // hover-pause only where a real pointer exists (touch emulates mouseenter and would freeze autoplay)
    if (window.matchMedia('(hover: hover)').matches) {
        wrapper.addEventListener('mouseenter', () => clearInterval(autoplayTimer));
        wrapper.addEventListener('mouseleave', startAutoplay);
    }

    // swipe left / right on touch screens
    let touchX = null;
    let touchY = null;
    wrapper.addEventListener('touchstart', (e) => {
        touchX = e.touches[0].clientX;
        touchY = e.touches[0].clientY;
        clearInterval(autoplayTimer);
    }, { passive: true });
    wrapper.addEventListener('touchend', (e) => {
        if (touchX === null) return;
        const dx = e.changedTouches[0].clientX - touchX;
        const dy = e.changedTouches[0].clientY - touchY;
        touchX = null;
        if (Math.abs(dx) > 40 && Math.abs(dx) > Math.abs(dy)) {
            dx < 0 ? next() : prev();
        } else {
            resetAutoplay();
        }
    }, { passive: true });

    render();
    startAutoplay();
});