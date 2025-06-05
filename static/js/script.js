document.addEventListener('DOMContentLoaded', function() {
    // Mobile Navigation
    const burger = document.querySelector('.burger');
    const nav = document.querySelector('.nav-links');
    const navLinks = document.querySelectorAll('.nav-links li');
    
    if (burger) {
        burger.addEventListener('click', function() {
            // Toggle Nav
            nav.classList.toggle('nav-active');
            
            // Animate Links
            navLinks.forEach((link, index) => {
                if (link.style.animation) {
                    link.style.animation = '';
                } else {
                    link.style.animation = `navLinkFade 0.5s ease forwards ${index / 7 + 0.3}s`;
                }
            });
            
            // Burger Animation
            burger.classList.toggle('toggle');
        });
    }
    
    // Flash Messages
    const flashMessages = document.querySelectorAll('.flash-message');
    const closeBtns = document.querySelectorAll('.close-btn');
    
    closeBtns.forEach((btn, index) => {
        btn.addEventListener('click', function() {
            flashMessages[index].style.display = 'none';
        });
    });
    
    // Auto-hide flash messages after 5 seconds
    setTimeout(() => {
        flashMessages.forEach(message => {
            message.style.display = 'none';
        });
    }, 5000);
});