document.addEventListener('DOMContentLoaded', function () {
    const titleEl = document.getElementById('siteTitle');

    // Հատվածներ. key = մշտական տառ, fill = անհետացող հատված
    const segments = [
        { type: 'key',  text: 'F' },
        { type: 'fill', text: 'uture ' },
        { type: 'key',  text: 'P' },
        { type: 'fill', text: 'ayments ' },
        { type: 'key',  text: 'S' },
        { type: 'fill', text: 'ystems' }
    ];

    const fillSpans = [];

    segments.forEach(function (seg) {
        const span = document.createElement('span');
        span.textContent = seg.text;
        span.className = seg.type;
        titleEl.appendChild(span);
        if (seg.type === 'fill') fillSpans.push(span);
    });

    // Չափում ենք fill հատվածների բնական լայնությունը՝ արդեն h1-ի ներսում, ճիշտ font-ով
    function lockNaturalWidths() {
        fillSpans.forEach(function (span) {
            const w = span.scrollWidth;
            span.dataset.naturalWidth = w;
            span.style.maxWidth = w + 'px';
        });
    }

    requestAnimationFrame(function () {
        lockNaturalWidths();
        requestAnimationFrame(function () {
            titleEl.classList.add('shown');
        });
    });

    function collapseToAcronym() {
        fillSpans.forEach(function (span) {
            span.style.maxWidth = '0px';
            span.style.opacity = '0';
        });
        titleEl.querySelectorAll('.key').forEach(function (k) {
            k.classList.add('highlight');
        });
    }

    function expandBack() {
        fillSpans.forEach(function (span) {
            span.style.opacity = '1';
            span.style.maxWidth = span.dataset.naturalWidth + 'px';
        });
        titleEl.querySelectorAll('.key').forEach(function (k) {
            k.classList.remove('highlight');
        });
    }

    const FULL_DURATION_MS = 8000;
    const SHORT_DURATION_MS = 60000;

    function loop() {
        setTimeout(function () {
            collapseToAcronym();
            setTimeout(function () {
                expandBack();
                loop();
            }, SHORT_DURATION_MS);
        }, FULL_DURATION_MS);
    }

    loop();
});


document.addEventListener('DOMContentLoaded', function () {
    const track = document.getElementById('terminalsTrack');
    track.innerHTML += track.innerHTML;
});