function toggleMenu() {
    const menuIcon = document.querySelector('.menu-icon');
    const navLinks = document.querySelector('.nav-links');

    // Тогл класу для відкриття/закриття меню
    navLinks.classList.toggle('active');

    // Тогл класу для повороту іконки
    menuIcon.classList.toggle('rotate');
}
