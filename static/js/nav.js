document.addEventListener('DOMContentLoaded', function () {
    const header = document.querySelector('.header');
    const burger = document.getElementById('navBurger');
    const list = document.getElementById('navList');
    if (!header || !burger || !list) return;

    function isOpen() {
        return header.classList.contains('nav-open');
    }

    function setOpen(open) {
        header.classList.toggle('nav-open', open);
        document.body.classList.toggle('nav-locked', open);
        burger.setAttribute('aria-expanded', String(open));
    }

    burger.addEventListener('click', function (e) {
        e.stopPropagation();
        setOpen(!isOpen());
    });

    // close after choosing a section
    list.addEventListener('click', function (e) {
        if (e.target.closest('a.page-scroll')) setOpen(false);
    });

    // close on outside tap
    document.addEventListener('click', function (e) {
        if (isOpen() && !header.contains(e.target)) setOpen(false);
    });

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && isOpen()) {
            setOpen(false);
            burger.focus();
        }
    });

    // resizing / rotating past the breakpoint resets the panel
    // (reads the real state from CSS, so the breakpoint lives only in style.css)
    window.addEventListener('resize', function () {
        if (getComputedStyle(burger).display === 'none') setOpen(false);
    });
});
