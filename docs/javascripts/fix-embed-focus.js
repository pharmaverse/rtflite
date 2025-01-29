// Scroll to the top after the page has loaded to prevent jumping to the embed element
document.addEventListener("DOMContentLoaded", function () {
  setTimeout(function () {
    window.scrollTo(0, 0);
  }, 250);
});
