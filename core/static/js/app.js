// AOS (Animate On Scroll) : les éléments portant un attribut `data-aos`
// (ex. data-aos="fade-up") s'animent à leur entrée dans le viewport.
// Animation jouée une seule fois, désactivée si l'utilisateur préfère réduire
// les animations. aos.js est chargé avant ce fichier (cf. base.html).
if (window.AOS) {
    AOS.init({
        once: true,
        duration: 700,
        easing: "ease-out-cubic",
        disable: () =>
            window.matchMedia("(prefers-reduced-motion: reduce)").matches,
    });
}

// Alpine.js components for La tribu d'Oya.
// Registered on `alpine:init` so they are available before Alpine starts.

document.addEventListener("alpine:init", () => {
    // Full-screen home carousel (stages + projets), replaces Glide.js.
    // Autoplay every 5s; any manual control stops the autoplay (legacy behaviour).
    Alpine.data("homeCarousel", (total = 0) => ({
        current: 0,
        total: total,
        timer: null,
        autoplay: true,

        init() {
            if (this.total > 1 && this.autoplay) {
                this.start();
            }
        },
        start() {
            this.timer = setInterval(() => this.advance(), 5000);
        },
        stopAutoplay() {
            if (this.timer) {
                clearInterval(this.timer);
                this.timer = null;
            }
            this.autoplay = false;
        },
        advance() {
            this.current = (this.current + 1) % this.total;
        },
        next() {
            this.stopAutoplay();
            this.current = (this.current + 1) % this.total;
        },
        prev() {
            this.stopAutoplay();
            this.current = (this.current - 1 + this.total) % this.total;
        },
        goTo(index) {
            this.stopAutoplay();
            this.current = index;
        },
    }));
});
