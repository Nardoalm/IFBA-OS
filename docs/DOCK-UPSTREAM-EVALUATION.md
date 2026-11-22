# Avaliação de Dock para o Plasma 6

Avaliação estática de 21/11/2026. Nenhum instalador externo foi executado e nenhuma ISO foi gerada.

## Ambiente do IFBA OS

O build usa Ubuntu 26.04 e Plasma 6.6 (ver `DESIGN-SYSTEM.md`). A sessão Live é configurada em `scripts/build-iso-container.sh` como `plasmax11.desktop`. O layout atual cria um painel inferior flutuante com Kickoff e `org.kde.plasma.icontasks`; ele é aplicado apenas no primeiro acesso, preservando configurações pessoais posteriores.

## Projeto solicitado: DomiLuebben/macOS-Dock-Plasmoid-Plasma-6

- Fonte: <https://github.com/DomiLuebben/macOS-Dock-Plasmoid-Plasma-6>, commit `60d011bd9b1004169e5e7c4b0ef0f7591b362756` (28/10/2026), versão declarada 1.18.0.
- Licença: `metadata.json` declara GPL-2.0-or-later; o repositório inclui a GPL v2. A redistribuição do binário exigiria disponibilizar o código-fonte correspondente e preservar os avisos.
- Implementação verificada: `contents/ui/DockItem.qml` contém ampliação por integração a cada quadro e animação de salto; `main.qml` usa `TaskManager.TasksModel`, indicadores, janela de revelação e ocultação; `native/` compila módulo C++17 com Qt 6 e KF6. Não há binário por arquitetura no código-fonte: AMD64 e ARM64 precisariam de compilações separadas.
- Dependências de build: Qt6 Core/DBus/Gui/Qml e KF6 Service/WindowSystem/Solid/I18n/KIO, CMake e compilador C++17. O QML importa `org.kde.layershell`, TaskManager e módulos privados do Plasma. O script `install.sh` compila e instala no perfil do usuário; não foi executado. O código nativo usa D-Bus da sessão, Solid, KIO e, para abrir o Dolphin, `QProcess::startDetached` com programa fixo. Não foi identificado download automático no instalador.
- **Incompatibilidade decisiva:** `main.qml` cria janelas independentes e posiciona Dock, overlay e revelador com `LayerShell.Window`. O layer-shell-qt implementa o protocolo `wl-layer-shell` do Wayland. A sessão Live atual inicia em X11. Nessa sessão, o posicionamento e a ocultação não têm a garantia requerida. Alterar a sessão padrão para Wayland seria uma mudança de boot e compatibilidade fora do escopo desta integração.
- **Múltiplos monitores:** as janelas usam `LayerShell.Window.wantsToBeOnActiveScreen: true`; a fonte não demonstra seleção persistente por saída nem um Dock por monitor. O modelo de tarefas global usa `filterByScreen: false`. Assim, a exigência de Dock estável em cada monitor não está comprovada.

**Decisão: REJEITADO para integração como Dock padrão no estado atual do IFBA OS.** Não remover o Dock atual antes de haver substituto validado em X11 e Wayland. Essa decisão pode ser revista se a sessão padrão migrar, a seleção de monitor for resolvida e testes reais forem feitos.

## Alternativa pronta encontrada

<https://github.com/Matt-Anis/plasma-macos-dock>, commit `ba4f0551ac9c71e9a777451aa1c43db144a10156`. O código usa o painel nativo do Plasma e traz ampliação (`contents/ui/main.qml` e `Task.qml`), salto (`Task.qml`), indicadores e ações reais de tarefas. A ocultação é delegada ao painel do Plasma. Há caminhos separados para miniaturas X11 e Wayland. Isso elimina a dependência de `wl-layer-shell` para posicionar o Dock e permite usar a política de monitores dos painéis nativos.

**Decisão: REQUER INVESTIGAÇÃO ADICIONAL.** A árvore não inclui um arquivo de licença integral, embora `metadata.json` declare GPL-2.0+ e os arquivos usem cabeçalhos GPL/LGPL. Antes de empacotar, conferir a origem/licença de todos os arquivos e recursos, verificar a API QML contra o Plasma 6.6 do rootfs, executar testes do plasmoid nas duas arquiteturas e validar X11, Wayland e múltiplas saídas em VM. Não há evidência de runtime nesta avaliação.

## Critério para a próxima integração

Substituir somente `org.kde.plasma.icontasks` no painel inferior, manter o Kickoff com o símbolo institucional oficial e os lançadores IFBA AI, Firefox, Dolphin, Konsole e Configurações. Fixar o commit e distribuir código-fonte/licenças. O painel do Plasma deve continuar sendo criado apenas para usuários novos e sessões Live; não reaplicar layout em cada inicialização. Antes de publicar, comprovar build AMD64/ARM64, funcionamento X11/Wayland e comportamento com duas telas reais ou virtuais. Até lá, o layout atual permanece como fallback funcional.
