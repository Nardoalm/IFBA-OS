# Controles do sistema no Plasma

## Implementação atual

A interface nova usa a bandeja e os applets mantidos pelo KDE Plasma, em vez do plasmoid IFBA que agregava todos os controles numa janela própria. O layout configura NetworkManager, BlueDevil, volume, bateria e notificações na barra superior. O relógio permanece como applet independente. Cada módulo apresenta o estado real do serviço e abre o popup nativo correspondente; hardware ausente não é representado como disponível.

O tema Plasma IFBA, as cores Qt e o KWin aplicam a aparência escura esmeralda e blur quando suportado. Se a composição não oferecer blur, os mesmos componentes continuam usando superfícies e texto do tema nativo. Essa opção conserva menus, foco, atalhos e acessibilidade que acompanham os applets de origem.

Há uma diferença funcional deliberada em relação ao mockup original: os módulos não são reunidos num painel único. Bluetooth é exibido somente quando o serviço/applet estiver instalado e a disponibilidade do adaptador é indicada pelo próprio BlueDevil. Não existe controle de brilho, modo noturno, energia, MPRIS ou Não Perturbe dentro de um painel agregado; essas funções continuam acessíveis pelos controles e configurações KDE que as fornecem.

## Retirada do plasmoid próprio

O antigo `org.ifbaos.controlcenter` QML foi retirado do build e removido da fonte ativa nesta revisão. Ele importava APIs privadas de NetworkManager, áudio, brilho, bateria, BlueZ, notificações e MPRIS. `qmlformat` validava a sintaxe, mas não resolvia essas importações nem comprovava criação do applet em uma sessão Plasma. Não houve teste de runtime que justificasse torná-lo parte do ambiente padrão.

O histórico dessa implementação e a análise de APIs permanecem nos registros de [`FINAL-AUDIT.md`](FINAL-AUDIT.md), [`VM-TESTING.md`](VM-TESTING.md) e versões anteriores desta documentação. O build verifica os plugins dos applets nativos, incluindo `org.kde.plasma.bluetooth`, e falha se algum deles não estiver presente.

## Validação

Os testes automatizados confirmam que o layout não ativa nem empacota o plasmoid removido, lista os applets nativos e seleciona o tema IFBA nos perfis novos. Testes de sintaxe e empacotamento não substituem teste de popup em sessão Plasma. A alteração ainda precisa ser incluída numa ISO e verificada visualmente em uma VM ARM64; AMD64 também deve ser testada separadamente. Não há screenshot ou validação de runtime desta alteração.
