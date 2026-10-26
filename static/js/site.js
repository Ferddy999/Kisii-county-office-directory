(function () {
  var EYE = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>';
  var EYE_OFF = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>';

  /* show / hide password */
  document.querySelectorAll('input[type="password"]').forEach(function (input) {
    var wrap = document.createElement('span');
    wrap.className = 'pw-wrap';
    input.parentNode.insertBefore(wrap, input);
    wrap.appendChild(input);

    var button = document.createElement('button');
    button.type = 'button';
    button.className = 'pw-toggle';
    button.setAttribute('aria-label', 'Show password');
    button.setAttribute('aria-pressed', 'false');
    button.innerHTML = EYE;
    button.addEventListener('click', function () {
      var show = input.type === 'password';
      input.type = show ? 'text' : 'password';
      button.innerHTML = show ? EYE_OFF : EYE;
      button.setAttribute('aria-label', show ? 'Hide password' : 'Show password');
      button.setAttribute('aria-pressed', show ? 'true' : 'false');
    });
    wrap.appendChild(button);
  });

  /* phone menu */
  var header = document.querySelector('.site-header');
  var menuButton = document.querySelector('.nav-toggle');
  if (header && menuButton) {
    menuButton.addEventListener('click', function () {
      var open = header.classList.toggle('menu-open');
      menuButton.setAttribute('aria-expanded', open ? 'true' : 'false');
      menuButton.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    });
  }

  /* directory filters on phones */
  var filterButton = document.querySelector('.filters-toggle');
  var filterBox = document.getElementById('filter-more');
  if (filterButton && filterBox) {
    var counter = filterButton.querySelector('[data-filter-count]');
    var recount = function () {
      var n = 0;
      filterBox.querySelectorAll('select, input[type="text"], input[type="search"]').forEach(function (el) {
        if (el.value) { n += 1; }
      });
      counter.textContent = n;
    };
    recount();
    filterBox.addEventListener('change', recount);
    filterBox.classList.add('is-collapsed');
    filterButton.addEventListener('click', function () {
      var collapsed = filterBox.classList.toggle('is-collapsed');
      filterButton.setAttribute('aria-expanded', collapsed ? 'false' : 'true');
    });
  }
})();
