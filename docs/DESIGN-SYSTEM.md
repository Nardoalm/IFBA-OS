# IFBA OS Design System

O IFBA OS mantém uma linguagem visual própria, baseada em superfícies verdes profundas, texto claro e acento esmeralda. A referência é a consistência e o acabamento de desktops modernos; não se reproduzem logos, imagens, ícones proprietários ou elementos de marca da Apple. A logo do Instituto Federal continua sendo o ativo institucional original, sem alterações em geometria, disposição ou cor.

## Fonte única de tokens

[`packaging/design-system/tokens.json`](../packaging/design-system/tokens.json) é a fonte canônica da paleta, tipografia, escala de espaçamento, raios, opacidades, sombras e movimento. Os ativos seguintes são gerados com `python3 tools/generate_design_system.py` e a atualização pode ser conferida sem gravar arquivos por `python3 tools/generate_design_system.py --check`:

- `packaging/color-schemes/IFBA-OS-Dark.colors`: cores nativas do KDE/Qt, usadas pelo tema global Plasma.
- `packaging/konsole/IFBA Glass.colorscheme`: esquema compartilhado do Konsole.
- `packaging/gtk/gtk.css` e `packaging/gtk/settings.ini`: acentos e superfícies GTK 3/4 alinhados com KDE.
- `packaging/ifba-ai.css`: CSS da interface GTK própria do IFBA AI, gerado com os mesmos tokens.
- `packaging/design-system/ifba-welcome.qss`: stylesheet da janela nativa Qt IFBA Welcome.

A decoração Aurorae em `packaging/plasma/window-decoration/IFBA-Window/` usa as mesmas cores semânticas dos tokens. Aurorae não oferece uma variável de cor global para SVG; por isso, testes verificam que os valores semânticos da decoração permanecem alinhados com a fonte canônica. Espaçamento, radius, sombra e motion são tokens de projeto: Plasma nativo não dispõe de API global para aplicar cada valor uniformemente a qualquer aplicativo de terceiros; componentes implementados pelo IFBA devem consultá-los e respeitar movimento reduzido.

## Aplicação e persistência

O script de geração de ISO instala esquema KDE, CSS/configuração GTK e defaults do Plasma no sistema e em `/etc/skel`. O primeiro perfil Live recebe as mesmas configurações se ainda não as tiver. Arquivos GTK e `kdeglobals` já existentes no perfil não são substituídos. O setup Plasma conserva marcadores de primeira aplicação e não reaplica layout ou tema a perfis já inicializados. Uma instalação pelo Calamares copia o rootfs da sessão Live; depois da instalação, `/etc/skel` fornece esses defaults aos usuários criados.

O CSS do sistema dá um padrão consistente a GTK; configurações CSS/GTK locais do usuário continuam prioritárias. O tema Breeze GTK nativo é mantido como base. Aplicativos Qt recebem o esquema KDE e Breeze escuro, sem instalar Kvantum ou temas globais de terceiros. O tema nativo do Plasma, seu painel e Kickoff, blur padrão do KWin e lock screen IFBA continuam sendo os componentes visuais do produto.

## Dependências e reutilização externa

Esta fundação não copia arquivos externos. Segue a auditoria [`UPSTREAM-COMPONENTS-AUDIT.md`](UPSTREAM-COMPONENTS-AUDIT.md): painéis e widgets nativos KDE são preferidos; os projetos WhiteSur e MacSequoia foram aprovados somente com adaptações e verificação de licença por arquivo; XMacTahoe requer investigação adicional; o efeito plasma-liquid-glass foi rejeitado para a versão atual por incompatibilidade de KWin e escopo de desempenho. Não foram adicionadas fontes ou logos externos. Inter e Noto já são dependências do build Ubuntu.

## Validação

Testes automatizados cobrem geração/reprodutibilidade dos arquivos, contraste WCAG AA para texto e pares interativos, alinhamento de cores Qt/GTK/Konsole/Aurorae, instalação no build e proteção de preferências existentes. Esses testes verificam contratos em arquivos, não o resultado gráfico real. A aparência, blur, fallback sem aceleração e compatibilidade GTK/Qt ainda devem ser observados em VM com screenshots antes de declarar validação visual.
