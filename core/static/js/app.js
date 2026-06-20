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

    // Image gallery carousel (projet detail page).
    Alpine.data("imageCarousel", (total = 0) => ({
        current: 0,
        total: total,
        next() {
            this.current = (this.current + 1) % this.total;
        },
        prev() {
            this.current = (this.current - 1 + this.total) % this.total;
        },
        goTo(index) {
            this.current = index;
        },
    }));
});
