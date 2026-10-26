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

    wrapper.addEventListener('mouseenter', () => clearInterval(autoplayTimer));
    wrapper.addEventListener('mouseleave', startAutoplay);

    render();
    startAutoplay();
});