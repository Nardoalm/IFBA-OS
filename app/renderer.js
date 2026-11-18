const apps = [
  ['python3', 'Python 3', 'Programação · Interpretador de Python', 'candidate'],
  ['thonny', 'Thonny', 'Programação · IDE para iniciantes', 'candidate'],
  ['git', 'Git', 'Programação · Controle de versão', 'candidate'],
  ['gimp', 'GIMP', 'Criação · Edição de imagens', 'candidate'],
  ['inkscape', 'Inkscape', 'Criação · Ilustração vetorial', 'candidate'],
  ['blender', 'Blender', 'Criação · Modelagem e animação 3D', 'candidate'],
  ['libreoffice', 'LibreOffice', 'Escritório · Documentos e apresentações', 'candidate'],
  ['gcompris', 'GCompris', 'Aprendizagem · Atividades educativas', 'candidate'],
  ['arduino', 'Arduino IDE', 'Avaliar · confirmar disponibilidade e licença', 'review'],
  ['scratch', 'Scratch Desktop', 'Avaliar · confirmar pacote e licença', 'review']
];

const STORAGE_KEY = 'ifba-os.selected-apps.v1';
const root = document.querySelector('#apps');
const status = document.querySelector('#count');
const saveButton = document.querySelector('#save');
const savedSelection = readSavedSelection();

function readSavedSelection() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
    return new Set(Array.isArray(saved) ? saved.filter(id => apps.some(app => app[0] === id && app[3] === 'candidate')) : []);
  } catch {
    status.textContent = 'Não foi possível carregar as escolhas salvas.';
    return new Set();
  }
}

for (const [id, name, description, reviewStatus] of apps) {
  const row = document.createElement('label');
  row.className = 'app';
  const checkbox = document.createElement('input');
  checkbox.type = 'checkbox';
  checkbox.value = id;
  checkbox.disabled = reviewStatus === 'review';
  checkbox.checked = !checkbox.disabled && savedSelection.has(id);
  const details = document.createElement('span');
  const title = document.createElement('strong');
  title.textContent = name;
  const note = document.createElement('small');
  note.textContent = description;
  details.append(title, note);
  row.append(checkbox, details);
  if (reviewStatus === 'review') {
    const tag = document.createElement('span');
    tag.className = 'tag';
    tag.textContent = 'Em avaliação';
    row.append(tag);
  }
  root.append(row);
}

function selectedIds() {
  return [...root.querySelectorAll('input:checked')].map(input => input.value);
}

function updateCount() {
  const count = selectedIds().length;
  status.textContent = count ? `${count} aplicativo${count === 1 ? '' : 's'} selecionado${count === 1 ? '' : 's'}` : 'Nenhum aplicativo selecionado';
}

root.addEventListener('change', updateCount);
saveButton.addEventListener('click', () => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(selectedIds()));
    status.textContent = 'Escolhas salvas neste usuário. Nenhum aplicativo foi instalado.';
  } catch {
    status.textContent = 'Não foi possível salvar. Verifique o armazenamento local do navegador.';
  }
});

function clearSelection(message) {
  root.querySelectorAll('input:checked').forEach(input => { input.checked = false; });
  try {
    localStorage.removeItem(STORAGE_KEY);
    status.textContent = message;
  } catch {
    status.textContent = 'Configuração ignorada nesta sessão.';
  }
}

document.querySelector('#skip').addEventListener('click', () => {
  clearSelection('Configuração ignorada. Você pode continuar usando o sistema.');
});
document.querySelector('#clear-selection').addEventListener('click', () => {
  clearSelection('Escolhas removidas deste usuário. Nenhum aplicativo foi instalado.');
});

document.querySelector('#configure').addEventListener('click', () => {
  status.textContent = 'O assistente de IA está desativado neste protótipo.';
});

updateCount();
