let index = 0;
const slides = document.querySelectorAll('.slide');
let slideInterval = setInterval(showSlides, 4000);

function showSlides() {
    index++;
    if (index >= slides.length) {
        index = 0;
    }
    console.log('Automatic slide index:', index);
    document.querySelector('.slides').style.transform = `translateX(-${index * 100}%)`;
}

function resetInterval() {
    clearInterval(slideInterval);
    slideInterval = setInterval(showSlides, 4000);
}

function moveSlide(direction) {
    index += direction;
    if (index < 0) {
        index = slides.length - 1;
    } else if (index >= slides.length) {
        index = 0;
    }
    console.log('Manual slide index:', index);
    document.querySelector('.slides').style.transform = `translateX(-${index * 100}%)`;
    resetInterval();
}

document.querySelector('.prev').addEventListener('click', function () {
    moveSlide(-1);
});

document.querySelector('.next').addEventListener('click', function () {
    moveSlide(1);
});
