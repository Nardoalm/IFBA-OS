const userName = document.querySelector('#user-name');
const dateLabel = document.querySelector('#today');
const greetingTime = document.querySelector('#greeting-time');
const assistantToggle = document.querySelector('#assistant-toggle');
const assistantPanel = document.querySelector('#assistant-panel');

function updateClock() {
  const now = new Date();
  dateLabel.dateTime = now.toISOString();
  const formattedDate = new Intl.DateTimeFormat('pt-BR', {
    weekday: 'long', day: 'numeric', month: 'long'
  }).format(now);
  dateLabel.textContent = formattedDate.charAt(0).toLocaleUpperCase('pt-BR') + formattedDate.slice(1);

  const hour = now.getHours();
  greetingTime.textContent = hour < 12 ? 'Bom dia' : hour < 18 ? 'Boa tarde' : 'Boa noite';
}

if (window.ifbaOS?.getProfile) {
  window.ifbaOS.getProfile().then(profile => {
    if (profile?.displayName) userName.textContent = profile.displayName;
  }).catch(() => {
    userName.textContent = 'Estudante';
  });
}

updateClock();
setInterval(updateClock, 60_000);

function setAssistantOpen(open) {
  assistantPanel.hidden = !open;
  assistantToggle.setAttribute('aria-expanded', String(open));
}

assistantToggle.addEventListener('click', () => setAssistantOpen(assistantPanel.hidden));
document.querySelector('#assistant-close').addEventListener('click', () => setAssistantOpen(false));
document.addEventListener('keydown', event => {
  if (event.key === 'Escape') setAssistantOpen(false);
});
