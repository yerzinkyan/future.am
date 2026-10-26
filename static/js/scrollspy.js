document.addEventListener('DOMContentLoaded', function () {
    const sectionIds = ['home', 'about_us', 'Terminals', 'Arcus', 'Cards', 'Embosser', 'Contact'];
    const sections = sectionIds
        .map(id => document.getElementById(id))
        .filter(Boolean);

    const links = Array.from(document.querySelectorAll('.nav-link.page-scroll'));

    function setActive(id) {
        links.forEach(link => {
            const isMatch = link.getAttribute('href') === '#' + id;
            link.classList.toggle('active', isMatch);
        });
    }

    // Header height in px — must match the fixed header's actual height
    const headerOffset = 100;

    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    setActive(entry.target.id);
                }
            });
        },
        {
            root: null,
            // shrink the viewport window used for intersection so a section
            // only "counts" once its top has cleared the fixed header
            rootMargin: `-${headerOffset}px 0px -60% 0px`,
            threshold: 0
        }
    );

    sections.forEach(section => observer.observe(section));

    // Set initial active link right away (in case page is loaded mid-scroll or with a hash)
    const hash = window.location.hash.replace('#', '');
    if (hash && sectionIds.includes(hash)) {
        setActive(hash);
    } else {
        setActive('home');
    }
});