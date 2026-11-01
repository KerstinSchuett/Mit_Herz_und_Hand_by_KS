(function () {
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var ziele = [].slice.call(document.querySelectorAll('.figur, .faden'));
  if (reduce || !('IntersectionObserver' in window)) {
    ziele.forEach(function (z) { z.classList.add('da'); });
  } else {
    ziele.forEach(function (z) { if (z.classList.contains('faden')) z.classList.add('wartet'); });
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('da'); e.target.classList.remove('wartet'); io.unobserve(e.target); }
      });
    }, { threshold: 0.35 });
    ziele.forEach(function (z) { io.observe(z); });
  }
  if (reduce) return;
})();
