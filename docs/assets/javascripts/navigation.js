(() => {
  let lastScroll = 0;
  let scrollTimer = null;
  let header, tabs;
  let scrollHandler;
  const SCROLL_THRESHOLD = 50;
  let scrollingToAnchor = false;

  function updateHeaderVisibility(shouldShow) {
    if (!header) {
      header = document.querySelector('.md-header');
      if (!header) return;
    }
    
    if (shouldShow) {
      header.classList.remove('header--hidden');
    } else {
      header.classList.add('header--hidden');
    }
  }

  function updateTabsVisibility(shouldShow) {
    if (!tabs) {
      tabs = document.querySelector('.md-tabs');
      if (!tabs) return;
    }
    
    if (shouldShow) {
      tabs.classList.remove('tabs--hidden');
    } else {
      tabs.classList.add('tabs--hidden');
    }
  }

  function createScrollHandler() {
    return function handleScroll() {
      const currentScroll = window.pageYOffset;
      
      if (!header || !tabs) {
        header = document.querySelector('.md-header');
        tabs = document.querySelector('.md-tabs');
        if (!header || !tabs) return;
      }
      
      if (scrollingToAnchor) {
        updateHeaderVisibility(false);
        updateTabsVisibility(false);
        return;
      }
      
      if (currentScroll <= 0) {
        updateHeaderVisibility(true);
        updateTabsVisibility(true);
      } else if (currentScroll > lastScroll) {
        updateHeaderVisibility(false);
        updateTabsVisibility(false);
        if (scrollTimer) {
          clearTimeout(scrollTimer);
          scrollTimer = null;
        }
      } else if (lastScroll - currentScroll > SCROLL_THRESHOLD) {
        if (!scrollTimer) {
          scrollTimer = setTimeout(() => {
            updateHeaderVisibility(true);
            updateTabsVisibility(true);
            scrollTimer = null;
          }, 850);
        }
      }
      
      lastScroll = currentScroll;
    };
  }

  function cleanupListeners() {
    if (scrollHandler) {
      window.removeEventListener('scroll', scrollHandler);
    }
  }

  function initNavigation() {
    cleanupListeners();

    header = document.querySelector('.md-header');
    tabs = document.querySelector('.md-tabs');
    lastScroll = window.pageYOffset;

    scrollHandler = createScrollHandler();
    
    if (header && tabs) {
      if (lastScroll <= 0) {
        updateHeaderVisibility(true);
        updateTabsVisibility(true);
      } else {
        updateHeaderVisibility(false);
        updateTabsVisibility(false);
      }
      
      window.addEventListener('scroll', scrollHandler, { passive: true });
      
      // Handle mouse leave event - only show header
      document.addEventListener('mouseleave', () => {
        if (lastScroll > 0) {
          updateHeaderVisibility(true);
        }
      });

      // Handle mouse enter to restore scroll-based state
      document.addEventListener('mouseenter', () => {
        scrollHandler();
      });
      
      document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', (e) => {
          scrollingToAnchor = true;
          setTimeout(() => {
            scrollingToAnchor = false;
          }, 1000);
        });
      });
      
      scrollHandler();
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    initNavigation();

    document.body.addEventListener('click', (e) => {
      if (e.target.closest('a[href]')) {
        setTimeout(initNavigation, 50);
      }
    });

    const observer = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        if (mutation.type === 'childList' && 
            (mutation.target.matches('.md-content') || 
             mutation.target.matches('.md-main'))) {
          setTimeout(initNavigation, 50);
          break;
        }
      }
    });

    const content = document.querySelector('.md-content');
    const main = document.querySelector('.md-main');
    if (content) observer.observe(content, { childList: true, subtree: true });
    if (main) observer.observe(main, { childList: true, subtree: true });
  });

  window.addEventListener('popstate', initNavigation);

  if (document.readyState !== 'loading') {
    initNavigation();
  }
})();