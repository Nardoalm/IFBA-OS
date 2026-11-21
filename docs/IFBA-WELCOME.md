# IFBA Welcome

O IFBA Welcome é o aplicativo Qt 6 nativo do KDE Plasma que aparece ao entrar pela primeira vez em uma sessão. Ele reúne links para os sites públicos do SUAP e AVA, abertura do IFBA AI, documentação local, atualizações no Discover e atalhos para ferramentas educacionais instaladas.

## Preferência de abertura

Na parte inferior da janela, marque **Não mostrar novamente ao entrar** para desativar a abertura automática. A preferência é salva apenas no perfil local do usuário em `~/.config/ifba-os/welcome.ini`. O atalho **Boas-vindas do IFBA OS** continua disponível no menu para abrir a tela manualmente.

## Atalhos e limites

- SUAP e AVA abrem os sites HTTPS públicos já usados pelos atalhos do projeto. O Welcome não lê contas, atividades, notas, cookies ou APIs acadêmicas.
- IFBA AI abre o aplicativo local. O Welcome não solicita, armazena ou inclui chave da API.
- Atualizações abre a página de atualizações do Discover; a instalação das atualizações continua dependendo da revisão e confirmação do usuário.
- Thonny, LibreOffice Writer e GCompris são instalados pelo build para ARM64 e AMD64 e aparecem na tela quando seus executáveis estão disponíveis.
- Documentação básica permanece instalada em `/usr/share/doc/ifba-os/welcome.html` e pode ser consultada sem conexão.

O aplicativo não coleta nome de estudante nem tenta inferi-lo do nome da conta. A identidade IFBA OS é comunitária; o sistema não afirma endosso institucional.

## Validação

Testes de configuração e execução Qt serão registrados em `VM-TESTING.md`. Uma janela aberta com Qt offscreen ou em contêiner não conta como prova de integração visual em uma sessão Plasma. O app só deve ser considerado validado nas arquiteturas efetivamente executadas em uma sessão gráfica Linux.
