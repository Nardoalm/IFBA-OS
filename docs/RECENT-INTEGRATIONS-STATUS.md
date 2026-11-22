# Entregas e pendências das integrações recentes

Estado do código em 22/11/2026. Nenhuma alteração desta revisão foi incorporada a uma ISO.

| Pedido | Implementação presente | Pendência real |
|---|---|---|
| Tema Qt/Plasma e decoração | WhiteSur selecionado, adaptado e licenciado; Kvantum Glass e variante opaca | Renderização na VM com mídia nova |
| Dock com ampliação e salto | Plasmoid Matt-Anis fixado por commit, no painel flutuante nativo; Kickoff oficial, favoritos, animação suave e superfície translúcida com blur opcional | Renderização, ações reais, Wayland e múltiplos monitores pendentes na VM |
| Animações prontas | KWin nativo: Magic Lamp, Scale, Maximize, Slide, Overview; perfis ajustados nesta revisão | Teste de execução e desempenho por GPU/arquitetura |
| Glass externo e arredondamento | Blur KWin, Aurorae e Kvantum existentes | Rounded Corners e Panel Colorizer ainda em revisão; Liquid Glass incompatível segundo auditoria |
| Central de Controle | Plasmoid IFBA retirado; applets nativos de rede, Bluetooth, áudio, bateria e notificações na bandeja KDE | Popups separados; screenshot/ação em sessão Plasma e nova ISO pendentes |
| Launcher/barra/notificações | Kickoff, KRunner, appmenu, system tray e notifications nativos, todos sob tema IFBA | Revisão visual em mídia nova e duas telas |
| Bloqueio/SDDM | Shell nativo Plasma/KScreenLocker com wallpaper IFBA; SDDM Breeze customizado | Renderização e autenticação na próxima ISO ainda não verificadas |
| Ethernet | Override NetworkManager e DHCP; VM histórica v0.3.3 conectada | HTTPS e instalação em mídia nova |
| IFBA AI | Cliente GTK, erro recuperável, serviço D-Bus sob demanda | Abrir e interagir em mídia nova |
| Persistência | Skeleton, defaults e setup inicial; correção de criação de painéis | Calamares e reboot reais |
| ISOs/releases | Par v0.3.5 anterior às mudanças atuais | Fonte limpa/commit autorizado para próximo build; `gh` sem autenticação |

## Animações: reutilização efetiva do KWin

Código oficial consultado: <https://invent.kde.org/plasma/kwin>, branch `Plasma/6.6`, commit `195130deb6a0d1cdf0e030fe0352d12a00fd5743`. Nenhum shader ou efeito KDE foi copiado ou reimplementado: os pacotes Ubuntu fornecem as implementações e suas licenças.

`src/plugins/scale/package/contents/config/main.xml` aceita `Duration`; Magic Lamp aceita `AnimationDuration`. O helper aplica os tempos dos tokens IFBA. Maximize chama `animationTime(250)`; Overview usa `animationTime(300ms)` e Slide calcula sua mola a partir de `animationTimeFactor()`. Estes três seguem a preferência global do KDE, que não é sobrescrita. Não há chave individual de duração para eles na versão examinada.

Fade e Scale pertencem à categoria exclusiva de abertura/fechamento; Squash e Magic Lamp à de minimização. A revisão desabilita Fade, Squash e Fade Desktop para impedir concorrência com Scale, Magic Lamp e Slide. Leve e movimento reduzido desabilitam as animações selecionadas pelo helper. Overview permanece disponível como função de navegação. O grupo correto é `Effect-overview`, conforme `overviewconfig.kcfg`; o antigo `Effect-Overview` foi corrigido.

Overview registra gestos nativos de quatro dedos no trackpad (cima/baixo) e três dedos em touchscreen. Não se instala daemon de gestos duplicado. O funcionamento exige uma sessão/dispositivo com suporte; a sessão Live X11 não comprova gestos Wayland. A política de desktops continua configurável pelo KDE.

Os defaults e o helper já fazem parte do pipeline da ISO. Usuários novos recebem os defaults; perfis existentes só mudam pelo seletor explicitamente acionado pelo usuário. Testes automatizados não comprovam desempenho, interação gráfica nem compatibilidade do driver.

### Segunda revisão: recuperação e fallback

O setup agora só grava o marcador de layout depois de encontrar um painel salvo pelo Plasma. Uma aplicação que termina sem criar painéis permite nova tentativa no próximo login. O wallpaper também só é marcado depois do comando bem-sucedido. O teste de regressão executa duas sessões simuladas sem painéis e confirma duas tentativas, sem marcador falso. Perfis pessoais com containments continuam preservados.

O perfil Leve passa a selecionar `IFBA-Glass-Opaque` usando a implementação Kvantum já distribuída; Equilibrado/Avançado selecionam `IFBA-Glass`. Isso só ocorre quando o tema atual é IFBA-Glass ou IFBA-Glass-Opaque. Temas pessoais não são substituídos. Aplicativos Qt abertos precisam ser reiniciados para recarregar o tema. Testes cobrem ambos os temas IFBA e a preservação de tema pessoal.

## Revisão adicional dos componentes externos

- **Panel Colorizer**, commit `ad928a42bfc0b929afffcfa552e98aa880b736db`, versão 8.1.0: GPL-3.0, QML e plugin opcional. Não aprovado para ativação padrão nesta revisão. `package/contents/ui/configHideWidgets.qml:172` interpola JSON de configuração em `echo '…'` executado pelo componente RunCommand. Um apóstrofo em dados configuráveis pode quebrar a citação do shell. Os caminhos `configDir` também são interpolados. Isso exige correção/testes de todos os caminhos de importação/exportação antes de distribuir a personalização. Não foi demonstrada exploração remota; o risco observado é a composição insegura de comandos com dados locais. Não foi executado código upstream.
- **KDE Rounded Corners**, commit `c0a1b8e510a1c2e2fa4edbaa65b88a129d44a279`, versão 0.7.2: C++/OpenGL, GPL conforme metadados e licença do projeto. `CMakeLists.txt` separa KWin Wayland e KWinX11 via `KWIN_X11`; para Qt >= 6.10 exige Qt CorePrivate. Portanto são necessários dois builds por arquitetura e compatibilidade com a ABI exata do compositor, não apenas copiar um plasmoid. Ainda não aprovado para ativação; Aurorae arredondado é o fallback existente. A fonte não comprova funcionamento em software rendering do UTM.
- **XMacTahoe**, commit `7ffdaab099220c603c39fbb4503739beee17768c`: `THIRD_PARTY.md` confirma que AppGrid, Rounded Corners e Glass são instalados de repositórios externos/COPR, não fornecidos como componentes prontos redistribuíveis na árvore. Flex Hub é um componente distinto GPL-3.0+; bloqueio contém `NoPasswordUnlock.qml` e `PasswordSync.qml`, exigindo revisão de autenticação específica. Não substituir os fluxos KDE/PAM existentes por cópia integral do tema.

As árvores foram clonadas em diretórios temporários para leitura, sem executar instaladores, alterar a sessão do host ou criar dependências obrigatórias de boot. Não se afirma ausência de CVEs ou segurança completa.

O Dock pronto foi integrado após a avaliação descrita em `DOCK-UPSTREAM-EVALUATION.md`. As linhas anteriores de auditoria refletem o estado original, não aprovação genérica dos demais projetos.


### Simplificação por componentes nativos — 2026-11-22

O plasmoid de Central de Controle e o shell customizado de KScreenLocker foram removidos da fonte ativa e do pipeline; os substitutos são os popups da bandeja Plasma e o shell oficial do KDE, com tema/wallpaper IFBA. O Dock upstream auditado e o visual IFBA permanecem. Nenhuma ISO ou captura visual foi produzida nesta revisão.
