document.addEventListener('DOMContentLoaded', function() {
    const hero = document.querySelector('.hero');
    const layers = document.querySelectorAll('.hero__layer');
    
    function updateParallax() {
        const scrolled = window.pageYOffset;
        const rate = scrolled * 0.5;
        
        layers.forEach((layer, index) => {
            const speed = (index + 1) * 0.2;
            const yPos = -(rate * speed);
            layer.style.transform = `translate3d(0, ${yPos}px, ${-index}px) scale(${1 + index * 0.5})`;
        });
    }
    
    // Update on scroll
    window.addEventListener('scroll', updateParallax);
    
    // Initial update
    updateParallax();
    
    // Add hover effect
    hero.addEventListener('mousemove', (e) => {
        const { clientX, clientY } = e;
        const { offsetWidth, offsetHeight } = hero;
        
        const xPos = (clientX / offsetWidth - 0.5) * 20;
        const yPos = (clientY / offsetHeight - 0.5) * 20;
        
        layers.forEach((layer, index) => {
            const speed = (index + 1) * 0.2;
            layer.style.transform = `translate3d(${xPos * speed}px, ${yPos * speed}px, ${-index}px) scale(${1 + index * 0.5})`;
        });
    });
    
    // Reset on mouse leave
    hero.addEventListener('mouseleave', () => {
        updateParallax();
    });
});