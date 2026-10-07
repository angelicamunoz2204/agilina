// Shows or hides the password of the box each `[data-password-toggle]` button controls
// (aria-controls). The button stays hidden until this runs, so that without JavaScript the
// page has no button that does nothing. It keeps one name and says whether it is on with
// aria-pressed, as a toggle button does.
for (const button of document.querySelectorAll('[data-password-toggle]')) {
  const input = document.getElementById(button.getAttribute('aria-controls'));
  if (input === null) {
    continue;
  }
  button.addEventListener('click', () => {
    const show = input.type === 'password';
    input.type = show ? 'text' : 'password';
    button.setAttribute('aria-pressed', String(show));
    button.querySelector('[data-icon="show"]').classList.toggle('hidden', show);
    button.querySelector('[data-icon="hide"]').classList.toggle('hidden', !show);
  });
  button.hidden = false;
}
