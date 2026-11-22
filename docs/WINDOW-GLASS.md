# Decorações, Glass e animações

## Implementado

- O KWin usa a decoração Aurorae nativa `IFBA-Window`, mantida em `packaging/plasma/window-decoration/IFBA-Window/`. A decoração define moldura fina, cantos SVG de 12 px, estados ativo/inativo, botões nativos de minimizar/maximizar/fechar e realce verde no controle de maximização. Aplicativos com decoração client-side continuam controlando a própria barra de título.
- Os efeitos usam o compositor e o blur nativos do KWin. O padrão do tema para perfis novos é equilibrado (`blurEnabled=true`, `BlurStrength=2`); o esquema Konsole `IFBA Glass` permanece com fundo opaco o bastante para leitura quando blur/composição não estão disponíveis.
- O seletor **Perfil visual do IFBA OS** grava apenas configurações KWin do usuário atual. `Leve` desativa blur e Magic Lamp; `Equilibrado` usa blur 2 e Magic Lamp a 180 ms; `Avançado` usa blur 4 e Magic Lamp a 240 ms. As durações vêm de `tokens.json` pelo arquivo INI gerado. Não instala efeitos, drivers ou plugins, não pede privilégios e não edita arquivos de outros usuários.
- Magic Lamp é efeito nativo do KWin 6.6. O KWin recebe a geometria do ícone da janela e usa a posição publicada pelo painel quando disponível. Sem essa geometria, o código upstream usa fallback ao cursor/borda da tela; portanto, direção ao ícone é condicional ao applet publicar a geometria. O efeito usa o suporte de animação do compositor e pode não ser ativado quando esse suporte não está disponível.
- Os perfis leem `kdeglobals` → `KDE/AnimationDurationFactor`. Quando está em zero, Magic Lamp permanece desativado mesmo ao selecionar o perfil Equilibrado/Avançado. O script nunca grava `AnimationDurationFactor` ou `AnimationSpeed`, preservando o ajuste global e o movimento reduzido. `AnimationDuration` é uma duração-base; o KWin a escala pela preferência global.
- `IfbaAnimationTokens.qml` é gerado a partir de `tokens.json` e centraliza durações e curvas QML do projeto. `Kirigami.Units.longDuration` escala os tokens pela preferência global de animações do KDE. Como o KDE limita esse valor a pelo menos 1 ms, o componente detecta esse piso e desativa explicitamente os Behaviors próprios quando movimento reduzido está ativo. Botões e botões de ícone da Central de Controle usam componentes reutilizáveis com escala curta ao passar o mouse/pressionar. O popup foi reduzido para 20–25 unidades de grade de largura e 18–30 de altura, mantendo rolagem para módulos que excedam o espaço. Launcher Kickoff, Overview, painel, notificações, tooltips, lock screen e SDDM continuam usando suas transições nativas; este código não substitui nem finge suas animações internas. O Dock nativo mantém `taskHoverEffect`; ampliação progressiva, deslocamento dos ícones e salto de inicialização não são oferecidos por esse plasmoid e não foram simulados.
- O perfil só é aplicado quando o usuário o escolhe. As configurações de Aurorae/blur no look-and-feel são padrões para primeira configuração/perfis novos; a rotina de sessão não reaplica o layout a cada login.
- O SDDM continua usando o tema Breeze mantido pelo Plasma, com `theme.conf.user` apontando para o wallpaper IFBA e para o símbolo institucional e usando o verde de destaque. A configuração do tema separada dos arquivos upstream evita substituir o tema nativo.

## Compatibilidade e escolhas

- Aurorae/KDecoration e Blur são mecanismos nativos do KDE, fornecidos pelo pacote `kwin-style-aurorae` e pelo KWin já instalados na imagem. A decoração é SVG/configuração, sem módulo compilado dependente de ABI ou arquitetura; o script funciona em ARM64 e AMD64.
- `plasma-liquid-glass` continua excluído. A auditoria local o classifica como rejeitado para KWin/Plasma 6.6 devido ao acoplamento ABI, foco no KWin 6.8.2, teste limitado a uma máquina/Wayland e falta de teste X11. Nenhum recurso externo desse projeto é copiado.
- `Leve` é o fallback previsto para renderização por software, máquinas virtuais lentas ou preferência visual por menos efeitos. O compositor pode ocultar/desabilitar efeitos que não suportar; o sistema não presume GPU ou blur funcional. Perfis não alteram a configuração global de velocidade nem garantem 60 FPS.
- Blur é apenas transparência desfocada nativa; não há refração, distorção de framebuffer ou dependência de extensão externa.

## Limites de validação

Os testes automatizados verificam sintaxe do script, geração reprodutível dos tokens, perfis, proteção de movimento reduzido, presença/empacotamento dos tokens e parsing QML quando o build executa `qmlformat`. Eles não provam execução do QML, renderização do KWin, taxa de quadros, aparência em Wayland/X11 ou integração entre apps. A captura em `output/latest/arm64/image.png` pertence a uma ISO anterior e não comprova este patch. Nenhuma ISO atualizada foi gerada nem validada em VM; a validação continua pendente para ARM64 e AMD64.

## Referências

- [Auditoria local de componentes externos](UPSTREAM-COMPONENTS-AUDIT.md): compatibilidade, licenças e decisão sobre Plasma Liquid Glass.
- [KWin Desktop Effects — documentação do KDE](https://docs.kde.org/stable_kf6/en/kwin/kcontrol/kwineffects/index.html): efeitos disponíveis dependem do backend de composição; efeitos incompatíveis não são expostos como suportados.
- [KWin 6.6 Magic Lamp source](https://github.com/KDE/kwin/blob/Plasma/6.6/src/plugins/magiclamp/magiclamp.cpp): duração, suporte a animações e uso de icon geometry.
- [KWin 6.6 animation settings source](https://github.com/KDE/kwin/blob/Plasma/6.6/src/options.cpp): fator global `AnimationDurationFactor`.
- [KDE Plasma Accessibility](https://docs.kde.org/stable_kf6/en/plasma-desktop/kcontrol/kcmaccess/): preferências de acessibilidade continuam sob controle do usuário.
- [Guia oficial de portabilidade Plasma 6](https://develop.kde.org/docs/plasma/widget/porting_kf6/): APIs de unidades devem usar Kirigami em plasmoids Plasma 6.
- [Registro de validação em VM](VM-TESTING.md).
