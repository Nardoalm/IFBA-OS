# IFBA OS — Validação final da Etapa 08

22 de novembro de 2026 · Ubuntu 26.04 · Plasma 6.6.7 · Versão de produto 0.3.8

O código avaliado termina em `9b20894ab692fb1df3b4e6798c75e7b36ca9f853`. O ensaio gráfico usou a ISO histórica 0.3.8 ARM64 no UTM e aplicou os arquivos atuais sobre a sessão Live descartável. Essa mídia foi construída de `c9ec60405f4c0a560210cae34991c1354ced49e3`. O boot observado e as capturas da sessão com sobreposição correspondem a essas duas revisões, respectivamente.

## Mudanças e regressões

| Achado | Correção e evidência |
| --- | --- |
| Perfis novos ainda recebiam `wallpaper.png`, a variante metálica, enquanto login e bloqueio apontavam para Jacobina. | O Look-and-Feel passa a selecionar `campus-jacobina.jpg` na inicialização nativa. O asset anterior continua disponível para perfis que já tenham seu caminho salvo. O teste de Plasma iniciou um perfil novo, reiniciou o shell e verificou os mesmos containments. O ensaio Wayland mostrou a foto. |
| O rodapé do IFBA AI em modo Live impunha uma largura mínima que levava a janela para fora da tela. | A mensagem agora usa a quebra de texto do GTK/Pango. O teste GTK verificou a largura mínima e a captura ARM64 mostra o aviso em duas linhas com a janela dentro da área útil. O frontend padrão segue sendo o legado, com a prévia aberta separadamente. |
| O teste do IFBA Welcome dependia de VSCodium instalado no host. | A suíte AMD64 falhou inicialmente no contêiner mínimo. O teste agora controla a disponibilidade de executáveis, verifica a presença de VSCodium e a ausência da entrada do GCompris no cenário preparado. O Welcome continua detectando os aplicativos instalados. |
| A publicação do par substituía `latest/` inteira e podia remover um caminho em uso por VM. | O publicador verifica e arquiva o par em `versions/`, preserva caminhos e manifestos históricos e atualiza os links de `latest/`. Durante a atualização o status fica incompleto. Testes cobrem preservação de arquivo e manifesto, reativação do mesmo par e recusa de conteúdo divergente para uma versão arquivada. |
| O mínimo documentado de 30 GiB livres era conferido só por quem executava o build. | O script confere o espaço antes de preparar o staging. Em uma árvore limpa de `9b20894`, havia 22.310.544 KiB disponíveis. O comando saiu com código 2 e a pasta de staging permaneceu ausente nessa árvore. |

As etapas anteriores consolidaram barra, bandeja, relógio e tarefas nas implementações nativas do Plasma, removeram do layout a segunda entrada do menu e trocaram a ativação do dock Matt Anis por `org.kde.plasma.icontasks`. O pacote de compatibilidade do dock anterior continua no código. Saíram a central de controle própria, o QML próprio da tela de bloqueio e a limpeza recorrente de painéis no script de sessão. O perfil utiliza paleta e estilo Breeze, ativos do IFBA-WhiteSur-Dark, Aurorae, efeitos nativos do KWin, SDDM Breeze, KScreenLocker e System Settings com seus KCMs. Kvantum permanece como opção. A prévia do IFBA AI reutiliza GTK, markdown-it-py, Pygments e os contratos Python existentes. As etapas de estabilização também separaram o cache de bootstrap do rootfs recriado, explicitaram Wayland no Live e Plasma X11 como padrão inicial do instalado, e adicionaram a verificação Casper ao processo de empacotamento.

## Status por critério

| Critério | Status | Evidência e escopo |
| --- | --- | --- |
| Suíte no macOS ARM64 | **PASSOU** | 155 casos descobertos, 142 executados com sucesso e 13 pulados por requisitos de ambiente Linux/gráfico. |
| Suíte no Ubuntu 26.04 AMD64 | **PASSOU** | 155 casos, 154 aprovados e 1 pulado. O caso XFCE legado exige UID distinto de root. Contêiner AMD64 emulado com Xvfb, D-Bus, Plasma, GTK e PyQt. |
| Configuração, integridade e empacotamento | **PASSOU** | Testes de layout, arquivos de integração, ambiente isolado, regressões de mídia e manifesto Casper, além de sintaxe do script de build. A inspeção das ISOs históricas conferiu hash, tamanho, volume, catálogo El Torito e arquitetura. |
| Casper na ISO histórica 0.3.8 ARM64 | **FALHOU** | No boot em UTM, `casper-md5check.service` saiu com status 1 e registrou `fopen md5_file: No such file or directory`. A mídia antecede a inclusão do manifesto em `f234b23`. |
| Boot Live e Plasma Wayland | **PASSOU** | Boot em UTM ARM64 da mídia histórica 0.3.8. Sessão Wayland e Plasma 6.6.7 observados, antes dos ensaios com arquivos atuais. |
| Primeiro início, segundo início e perfis existentes | **PASSOU** | Plasma real em perfis descartáveis de teste. Dois containments no perfil novo, persistência no segundo início, preservação de desktop existente sem painéis e recuperação de mapeamento sem containments. O UTM também renderizou o layout novo sobre o Live. |
| Barra, dock, wallpaper e ícones | **PASSOU** | Capturas reais ARM64 a 1280×800 nas escalas 100%, 150% e 200%. Uma barra de 32 px lógicos com menu, bandeja e relógio. Um dock flutuante de 56 px lógicos e cinco lançadores visíveis. A foto e o símbolo IFBA são visíveis. |
| Dock com mutações, teclado e múltiplos monitores | **NÃO EXECUTADO** | A sessão confirma o widget nativo. Fixação, reordenação, múltiplos monitores e toda a matriz de navegação por teclado continuam pendentes em VM. |
| IFBA AI padrão em Live | **PASSOU** | Captura ARM64 mostra estado demonstrativo e mensagem de privacidade sem extravasar. A suíte gráfica passou nos testes de frontend, modos e regressões do serviço. |
| Prévia do IFBA AI em Live | **PASSOU** | A ação opcional abriu a tela inicial em UTM ARM64, com navegação, histórico vazio e campos restritos no modo demonstrativo. Testes GTK cobrem a prévia com simulação do backend. |
| IFBA AI com conta real e NVIDIA | **NÃO EXECUTADO** | Envio e cancelamento no provedor real, disponibilidade de modelos pela credencial, persistência instalada e isolamento com dois usuários reais da VM. |
| Configurações do sistema | **PASSOU** | A janela nativa abriu em UTM com navegação por categorias, paleta escura e a página de configurações rápidas. |
| LibreOffice Writer e GCompris | **PASSOU** | O Writer chegou a um documento novo e exibiu o diálogo de dica. GCompris chegou ao menu de categorias em português. A captura do Writer mostra o dock escondido pela janela maximizada. O teste cobre abertura e renderização. |
| VSCodium, janela utilizável em ARM64 Live | **FALHOU** | O pacote 1.143.17232 informou arquitetura ARM64 e o lançador padrão iniciou os processos do aplicativo. O ensaio com opções de software capturou apenas o desktop. Com o lançador padrão, o log registrou falha ao inicializar VA-API e a captura ficou sem resposta por mais de dois minutos. A causa da falta de captura e o efeito sobre o editor permanecem em aberto. |
| Portais educacionais | **NÃO EXECUTADO** | Os lançadores SUAP e AVA são visíveis no Live. Abertura das páginas e autenticação externa ficaram fora do ensaio. |
| Login e bloqueio, evidência anterior | **PASSOU** | Etapa 07 em laboratório ARM64 com SDDM/PAM e KScreenLocker. Senha incorreta recusada e correta aceita, com teste separado de retomada pelo UTM. O Live atual também atingiu estado bloqueado e foi desbloqueado administrativamente para continuar a coleta. |
| Instalação e primeiro login pelo instalador | **NÃO EXECUTADO** | Calamares, boot do disco instalado, seleção X11/Wayland após login e retomada por suspensão interna do Linux. O RTC virtual recusou o alarme no ensaio anterior. |
| Efeitos acelerados e redução de movimento | **NÃO EXECUTADO** | UTM usou OpenGL llvmpipe. Overview foi listado como carregado. Blur, Magic Lamp, Scale e Slide estavam ausentes da lista de efeitos carregados. As capturas permitem avaliar o fallback em três escalas. Aceleração física, fluidez, curvas de animação e redução de movimento permanecem pendentes. |
| Boot e instalação AMD64 | **NÃO EXECUTADO** | A suíte AMD64 no contêiner e o catálogo AMD64 do arquivo ISO foram verificados. A mídia não foi inicializada em uma VM AMD64. |
| Novas ISOs e publicação | **NÃO EXECUTADO** | Espaço abaixo do pré-requisito confirmado em fonte limpa. Nenhuma versão avançada, geração de ISO, atualização de `latest/`, tag ou release. |

Consulte [VM-TESTING.md](VM-TESTING.md) para o histórico dos ensaios UTM.

## Comparação visual

O caminho `docs/design/reference-desktop.png` está ausente. A comparação usou o mockup aprovado fornecido como `docs/design/image.png` e a variante de wallpaper `assets/wallpapers/image copy.png`. As referências são arquivos locais. As capturas da sessão UTM foram registradas fora da árvore Git. A referência tem 1672×941 e a captura 1280×800.

| Elemento | Resultado observado |
| --- | --- |
| Barra superior | A barra ocupa cerca de 4% da altura nos dois casos e deixa a data legível. O Plasma tem texto de menu e relógio mais compactos, menos espaçamento entre ícones à direita e nenhum nome de aplicativo ou menu visível no desktop ocioso. A transparência deixa o azul do fundo aparecer. O blur não foi validado no renderizador de software. |
| Dock | Centralizado, escuro e arredondado. Ocupa cerca de 27% da largura contra cerca de 44% do mockup. Há cinco ícones, com os desenhos dos próprios aplicativos, em vez dos dez elementos ilustrados no mockup. O contorno é mais marcado e o dock está mais perto da borda inferior. |
| Wallpaper | A fachada, faixa vermelha e vegetação são reconhecíveis. O 16:10 corta mais das laterais do que a imagem de referência. A foto renderizada é mais clara no céu e no lado direito. O contraste da barra com a foto foi legível na captura. |
| Desktop | Quatro atalhos visíveis do Live, incluindo o instalador experimental, acrescentam elementos no canto superior esquerdo. Essa área está livre no mockup. |
| Escalas | A barra, a bandeja, a data e os cinco ícones do dock ficaram visíveis às três escalas com llvmpipe. A 200%, o dock e os quatro atalhos ocupam mais espaço do que no mockup. |
| IFBA AI padrão | Abre na configuração do modo demonstrativo. A barra lateral estreita, os cartões de configuração verdes, a moldura GTK e o rodapé visível diferem da tela inicial, lateral larga e superfícies azul-escuras translúcidas da referência. Os botões da janela respeitam os controles do ambiente, com símbolos neutros no padrão capturado. |
| Prévia do IFBA AI | A moldura tem os três botões coloridos, o logotipo e o título ficam no centro e a barra lateral ocupa cerca de 22% da janela, proporção próxima à referência. A janela ocupa aproximadamente 89% da largura da tela contra 70% no mockup. A caixa de composição é opaca, com dois atalhos da prévia visíveis contra quatro na referência. O modo Live mantém as ações restritas e o histórico vazio. |
| System Settings | A captura confirma barra lateral com busca, grupos de categorias, prévias de tema e controles nativos. A decoração arredondada e os botões coloridos correspondem à moldura da prévia. A área de controle e o espaçamento seguem o KCM, e a referência de desktop fornecida mostra o IFBA AI. |
| Aplicativos educacionais | Writer tem espaço de edição claro e menus em inglês na sessão de teste, com barra de título escura. GCompris usa moldura escura e preserva as cores e a tipografia próprias das atividades. |
| Login e bloqueio | Nas capturas da Etapa 07, ambos usam a mesma foto. O login escurece mais o fundo e mostra relógio, usuário, senha e energia no centro. O bloqueio ocioso dá mais destaque ao relógio e deixa a foto mais clara. A data do bloqueio e parte dos rótulos do login saíram em inglês no laboratório. A referência fornecida mostra somente o desktop. |
| Tipografia, ícones e decoração | Traços de ícones Breeze menores no painel. A janela padrão do IFBA AI tem texto mais denso e menos margens que o mockup. As capturas disponíveis não validam sombras, blur e espessura de contorno em diferentes escalas ou toolkits. |

## Mídia histórica preservada

Ambos os arquivos abaixo foram verificados e continuam no caminho original sob `output/versions/v0.3.8/`, com um manifesto por arquitetura. O ARM64 foi o meio de boot do ensaio Live. A verificação estrutural da mídia AMD64 mantém o status de runtime pendente.

O xorriso encontrou `vmlinuz`, `initrd`, `filesystem.squashfs` e `filesystem.size` nos dois arquivos. O `md5sum.txt` usado pelo Casper está ausente nessas mídias históricas. O teste automatizado do manifesto passou no código atual. A validação Casper em uma mídia gerada com a correção segue pendente.

| Arquitetura | Arquivo | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| ARM64 | `ifba-os-ubuntu-26.04-arm64-v0.3.8.iso` | 2.151.831.552 | `01b5cbe0938fb186588d699aeb16e01f38885da68e19e7d9afbe3a1af9fed7e1` |
| AMD64 | `ifba-os-ubuntu-26.04-amd64-v0.3.8.iso` | 2.219.005.952 | `d41b9a4b0b5acd6933477bc6c3362bb88f469391d36609d65863f4b4e34cd2dc` |

`latest/` ainda contém a mídia ARM64 legada v0.3.6 e um manifesto AMD64 sem a ISO correspondente. O par v0.3.8 arquivado e as referências à mídia anterior foram preservados. Os commits de correção `af75d9939e554f35258a0a5ce40f9cd437587685` e `9b20894ab692fb1df3b4e6798c75e7b36ca9f853` tiveram identidade de autor e committer verificada e foram publicados em `origin/development`.
