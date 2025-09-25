class Carousel {
    constructor() {
        this.index = 0;
        this.slides = document.querySelectorAll('.slide');
        this.dots = document.querySelectorAll('.dot');
        this.slidesContainer = document.querySelector('.slides');
        this.slideInterval = null;
        this.isTransitioning = false;
        
        this.init();
    }

    init() {
        this.updateActiveSlide();
        this.startAutoplay();
        this.bindEvents();
        this.addTouchSupport();
    }

    bindEvents() {
        // Navigation buttons
        document.querySelector('.carousel-btn.prev').addEventListener('click', () => {
            this.moveSlide(-1);
        });

        document.querySelector('.carousel-btn.next').addEventListener('click', () => {
            this.moveSlide(1);
        });

        // Dot navigation
        this.dots.forEach((dot, i) => {
            dot.addEventListener('click', () => {
                this.goToSlide(i);
            });
        });

        // Pause on hover
        const carousel = document.querySelector('.carousel-container');
        carousel.addEventListener('mouseenter', () => {
            this.pauseAutoplay();
        });

        carousel.addEventListener('mouseleave', () => {
            this.startAutoplay();
        });

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft') {
                this.moveSlide(-1);
            } else if (e.key === 'ArrowRight') {
                this.moveSlide(1);
            }
        });
    }

    addTouchSupport() {
        let startX = 0;
        let endX = 0;
        const carousel = document.querySelector('.carousel-container');

        carousel.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
        });

        carousel.addEventListener('touchend', (e) => {
            endX = e.changedTouches[0].clientX;
            this.handleSwipe(startX, endX);
        });
    }

    handleSwipe(startX, endX) {
        const threshold = 50;
        const diff = startX - endX;

        if (Math.abs(diff) > threshold) {
            if (diff > 0) {
                this.moveSlide(1); // Swipe left - next slide
            } else {
                this.moveSlide(-1); // Swipe right - previous slide
            }
        }
    }

    moveSlide(direction) {
        if (this.isTransitioning) return;

        this.index += direction;
        if (this.index < 0) {
            this.index = this.slides.length - 1;
        } else if (this.index >= this.slides.length) {
            this.index = 0;
        }

        this.updateActiveSlide();
        this.resetAutoplay();
    }

    goToSlide(slideIndex) {
        if (this.isTransitioning || slideIndex === this.index) return;

        this.index = slideIndex;
        this.updateActiveSlide();
        this.resetAutoplay();
    }

    updateActiveSlide() {
        this.isTransitioning = true;
        
        // Update slides
        this.slides.forEach((slide, i) => {
            slide.classList.toggle('active', i === this.index);
        });

        // Update dots
        this.dots.forEach((dot, i) => {
            dot.classList.toggle('active', i === this.index);
        });

        // Update transform
        this.slidesContainer.style.transform = `translateX(-${this.index * 100}%)`;

        // Reset transition flag after animation
        setTimeout(() => {
            this.isTransitioning = false;
        }, 600);
    }

    startAutoplay() {
        this.slideInterval = setInterval(() => {
            this.moveSlide(1);
        }, 5000);
    }

    pauseAutoplay() {
        if (this.slideInterval) {
            clearInterval(this.slideInterval);
            this.slideInterval = null;
        }
    }

    resetAutoplay() {
        this.pauseAutoplay();
        this.startAutoplay();
    }
}

// Initialize carousel when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new Carousel();
});
