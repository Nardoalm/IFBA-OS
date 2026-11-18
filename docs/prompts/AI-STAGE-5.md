# IFBA OS — ETAPA 5/5
## Modernização do XFCE4, Plymouth, integração e ISO

Você está na etapa final de integração do IFBA OS.

### MISSÃO

Transformar o ambiente XFCE4 em um desktop moderno, elegante e funcional, inspirado nas versões estáveis mais recentes do macOS e Windows 11, mantendo a identidade própria do IFBA OS.

Integrar o assistente de IA, as contas individuais, o sistema de memória e os recursos visuais à ISO.

### REGRA FUNDAMENTAL

Não crie um aplicativo que simule o desktop.

Não utilize Electron em tela cheia.

Não substitua o XFCE4 por HTML.

O próprio XFCE4 deverá receber as personalizações.

### 1. INSPEÇÃO

Leia:

- `AGENTS.md`
- `docs/ARCHITECTURE.md`
- `docs/PROJECT-ROADMAP.md`
- `docs/AI-ASSISTANT.md`
- `docs/SECURITY.md`

Inspecione:

- Temas atuais.
- Configurações XFCE4.
- Wallpapers.
- Ícones.
- Painéis.
- LightDM.
- Plymouth.
- Scripts de build.
- Componentes do assistente.

Preserve as funcionalidades existentes.

### 2. DIREÇÃO VISUAL

Inspire-se no macOS para:

- Fluidez.
- Minimalismo.
- Sombras.
- Tipografia.
- Transições.
- Organização visual.
- Aparência sofisticada.

Inspire-se no Windows 11 para:

- Organização de janelas.
- Barra de tarefas.
- Menus.
- Configurações.
- Controles rápidos.
- Notificações.
- Acessibilidade.

Não copie recursos proprietários.

Crie uma identidade visual própria para o IFBA OS.

### 3. TEMA GLOBAL

Implemente:

- Tema GTK escuro.
- Decoração moderna do xfwm4.
- Ícones consistentes.
- Tipografia adequada.
- Menus refinados.
- Notificações personalizadas.
- Terminal integrado visualmente.
- Thunar personalizado.
- Diálogos consistentes.

Utilize preto, grafite, branco suave e detalhes verdes discretos.

### 4. PAINEL INFERIOR

Configure o xfce4-panel com:

- Menu IFBA OS.
- Gerenciador de arquivos.
- Navegador.
- Terminal.
- Aplicativos educacionais.
- Lista de janelas.
- Indicadores de aplicativos ativos.
- Rede.
- Áudio.
- Energia.
- Data e hora.
- Acesso ao assistente.

Evite docks duplicados.

Mantenha o painel funcional em diferentes resoluções.

### 5. DESKTOP

Configure o wallpaper metálico do IFBA OS previamente criado.

O wallpaper deve conter a logo 3D central.

Os elementos interativos devem ser componentes reais do sistema.

Configure atalhos SUAP e AVA utilizando arquivos `.desktop`.

Não invente atividades acadêmicas.

Widgets de saudação, data e próximas atividades devem utilizar soluções leves e compatíveis com XFCE4.

Não sobreponha janelas convencionais ao desktop para simular widgets.

### 6. ASSISTENTE DE IA

Integre o assistente desenvolvido nas etapas anteriores.

Requisitos:

- Ícone no painel.
- Atalho de teclado.
- Interface GTK.
- Configurações individuais.
- Chave NVIDIA individual.
- Histórico.
- Memória.
- Captura de tela autorizada.
- Destaque visual de controles.
- Ferramentas do sistema.
- Inicialização automática do serviço.

O assistente não deve abrir uma janela de conversa automaticamente em todo boot.

### 7. TELA DE INICIALIZAÇÃO

Implemente um tema Plymouth personalizado.

Utilize a imagem preta já criada, contendo:

- Fundo preto.
- Logo IFBA discreta.
- Texto IFBA OS em cinza escuro.
- Sem elementos decorativos nos cantos.

Localize a imagem no projeto ou utilize o recurso fornecido.

Não recrie a arte desnecessariamente.

Configure:

- Tema Plymouth.
- Scripts necessários.
- Inclusão no initramfs.
- Parâmetros de boot adequados.
- Integração com a ISO.

Não esconda erros críticos.

Mantenha uma forma documentada de acessar logs técnicos de inicialização.

### 8. LIGHTDM

Personalize a tela de login com identidade visual coerente.

Preserve:

- Segurança.
- Seleção de usuário.
- Autenticação.
- Sessões.
- Acessibilidade.

Não habilite autologin para instalações permanentes.

Diferencie explicitamente o comportamento da ISO live.

### 9. CONSTRUÇÃO DA ISO

Incorpore todos os componentes ao processo de build.

Requisitos:

- Instalação dos pacotes necessários.
- Inclusão dos temas.
- Configuração do XFCE4.
- Instalação dos serviços.
- Configuração do Plymouth.
- Inclusão do assistente.
- Configurações padrão de novos usuários.
- Permissões corretas.
- Ausência de credenciais.
- Build reproduzível.

Não dependa de configurações feitas manualmente na VM.

Não inclua a ISO gerada no Git.

### 10. TESTES NO UTM

Reconstrua a ISO.

Valide:

1. Boot.
2. Plymouth.
3. Inicialização do XFCE4.
4. Wallpaper.
5. Painel.
6. Menu.
7. Navegador.
8. Thunar.
9. Terminal.
10. LightDM quando aplicável.
11. Serviço de IA.
12. Configuração individual.
13. Memória.
14. Captura de tela.
15. Overlay.
16. Permissões.
17. Reinicialização.
18. Encerramento.

Teste em resoluções diferentes quando possível.

Não declare testes realizados se não tiver executado a VM.

### 11. LOOP ENGINEERING FINAL

Execute:

BUILD → BOOT → OBSERVAR → IDENTIFICAR FALHAS → CORRIGIR → REBUILD → RETESTAR.

Continue os ciclos enquanto houver problemas corrigíveis e recursos disponíveis.

Não altere a arquitetura aleatoriamente para contornar falhas.

Registre bloqueios reais.

Não encerre após apenas gerar a ISO.

O objetivo é validar o sistema em execução.

### 12. GIT

Branch obrigatório: `development`.

Identidade:

`Leonardo de Almeida Silva <nardocontapc1234@gmail.com>`

Verifique autor e committer antes de cada commit.

Não use identidade de outra pessoa.

Não faça force push.

Não reescreva histórico.

Atualize documentação e roadmap.

### 13. CRITÉRIOS DE ACEITAÇÃO

- [ ] XFCE4 moderno e funcional.
- [ ] Tema consistente.
- [ ] Painel inferior.
- [ ] Wallpaper correto.
- [ ] Plymouth personalizado.
- [ ] LightDM integrado.
- [ ] Navegador funcional.
- [ ] Thunar funcional.
- [ ] Terminal funcional.
- [ ] Assistente integrado.
- [ ] Contas individuais.
- [ ] Chaves protegidas.
- [ ] Memória individual.
- [ ] Visão de tela.
- [ ] Destaque de botões.
- [ ] Ferramentas autorizadas.
- [ ] ISO construída.
- [ ] Boot validado.
- [ ] Testes documentados.
- [ ] Roadmap atualizado.
- [ ] Commits corretos.

### RESULTADO ESPERADO

O IFBA OS deve iniciar com sua identidade visual própria, carregar o XFCE4 modernizado e disponibilizar um assistente educacional profundamente integrado ao sistema operacional.

Não entregue apenas uma interface bonita.

Entregue uma distribuição Linux funcional, integrada, segura e verificável.

Continue os ciclos de desenvolvimento até concluir o escopo ou documentar bloqueios reais.