# Decorações, Glass e animações

## Implementado

- O KWin usa a decoração Aurorae nativa `IFBA-Window`, mantida em `packaging/plasma/window-decoration/IFBA-Window/`. A decoração define moldura fina, cantos SVG de 12 px, estados ativo/inativo, botões nativos de minimizar/maximizar/fechar e realce verde no controle de maximização. Aplicativos com decoração client-side continuam controlando a própria barra de título.
- Os efeitos usam o compositor e o blur nativos do KWin. O padrão do tema para perfis novos é equilibrado (`blurEnabled=true`, `BlurStrength=2`); o esquema Konsole `IFBA Glass` permanece com fundo opaco o bastante para leitura quando blur/composição não estão disponíveis.
- O seletor **Perfil visual do IFBA OS** grava somente duas chaves no `kwinrc` do usuário que o executou: ativação do blur e intensidade. `Leve` desativa blur; `Equilibrado` usa intensidade 2; `Avançado` usa intensidade 4. Não instala efeitos, drivers ou plugins, não pede privilégios e não edita arquivos de outros usuários. Se KWin não responder ao pedido de reconfiguração, as chaves ficam salvas e serão lidas na próxima inicialização/reconfiguração.
- A ferramenta não toca em velocidade/duração de animação nem na preferência de movimento reduzido. Mantém intactas as preferências de acessibilidade configuradas pelo usuário. A configuração padrão de animação do KWin distribuída aos novos perfis permanece no pacote de look-and-feel.
- O perfil só é aplicado quando o usuário o escolhe. As configurações de Aurorae/blur no look-and-feel são padrões para primeira configuração/perfis novos; a rotina de sessão não reaplica o layout a cada login.
- O SDDM continua usando o tema Breeze mantido pelo Plasma, com `theme.conf.user` apontando para o wallpaper IFBA e para o símbolo institucional e usando o verde de destaque. A configuração do tema separada dos arquivos upstream evita substituir o tema nativo.

## Compatibilidade e escolhas

- Aurorae/KDecoration e Blur são mecanismos nativos do KDE, fornecidos pelo pacote `kwin-style-aurorae` e pelo KWin já instalados na imagem. A decoração é SVG/configuração, sem módulo compilado dependente de ABI ou arquitetura; o script funciona em ARM64 e AMD64.
- `plasma-liquid-glass` continua excluído. A auditoria local o classifica como rejeitado para KWin/Plasma 6.6 devido ao acoplamento ABI, foco no KWin 6.8.2, teste limitado a uma máquina/Wayland e falta de teste X11. Nenhum recurso externo desse projeto é copiado.
- `Leve` é o fallback previsto para renderização por software, máquinas virtuais lentas ou preferência visual por menos efeitos. O compositor pode também ocultar/desabilitar efeitos que não suportar; o sistema não presume GPU ou blur funcional.
- Blur é apenas transparência desfocada nativa; não há refração, distorção de framebuffer ou dependência de extensão externa.

## Limites de validação

Os testes desta etapa verificam sintaxe do script, opções permitidas, instalação no build e que os perfis só escrevem chaves de blur. Eles não provam que o KWin 6.6 aplica cada valor, que a aparência é consistente entre Wayland/X11, nem que sombras, cantos, foco, animações, SDDM, bloqueio, Dolphin, menus e notificações foram visualmente verificados. Essas verificações exigem boot das imagens atuais em ARM64 e AMD64. Até lá, decoração e efeitos são implementados em fonte, aguardando validação na VM.

## Referências

- [Auditoria local de componentes externos](UPSTREAM-COMPONENTS-AUDIT.md): compatibilidade, licenças e decisão sobre Plasma Liquid Glass.
- [KWin Desktop Effects — documentação do KDE](https://docs.kde.org/stable_kf6/en/kwin/kcontrol/kwineffects/index.html): efeitos disponíveis dependem do backend de composição; efeitos incompatíveis não são expostos como suportados.
- [KDE Plasma Accessibility](https://docs.kde.org/stable_kf6/en/plasma-desktop/kcontrol/kcmaccess/): preferências de acessibilidade continuam sob controle do usuário.
- [Registro de validação em VM](VM-TESTING.md).
