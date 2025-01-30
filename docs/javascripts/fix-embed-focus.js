// Check and reset scroll position if page has been auto-scrolled to embed
document.addEventListener("DOMContentLoaded", function () {
  let checkCount = 0;
  const maxChecks = 100;

  const checkScrollPosition = function () {
    if (window.scrollY > 0) {
      window.scrollTo(0, 0);
      return;
    }

    checkCount++;
    if (checkCount < maxChecks) {
      setTimeout(checkScrollPosition, 10);
    }
  };

  setTimeout(checkScrollPosition, 10);
});
