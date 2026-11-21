# Central de controle do IFBA OS

## Implementação

`packaging/plasma/ifba-control-center` contém o plasmoid `org.ifbaos.controlcenter`, carregado por um botão compacto na barra superior definida em `packaging/plasma/ifba-os/contents/layouts/org.kde.plasma.desktop-layout.js`. O pacote é instalado em `/usr/share/plasma/plasmoids/` para a sessão Live e para a instalação feita a partir da mesma imagem. Como o layout do Plasma é aplicado pelo mecanismo de primeira sessão já existente, preferências de painel de perfis previamente inicializados não são reescritas em cada login.

O popup usa `PlasmoidItem` e `PlasmaExtras.Representation`, controles Plasma/Kirigami e o tema da sessão. O fundo translúcido e blur dependem do compositor e da configuração do KWin. O conteúdo é rolável, mantém foco/teclado e usa nomes acessíveis nos controles. O pipeline instala `bluedevil`, `bluez`, `libspa-0.2-bluetooth`, `kscreen` e `power-profiles-daemon` para fornecer os componentes e serviços nativos correspondentes em ARM64 e AMD64.

## Serviços e disponibilidade

| Módulo | API consultada/acionada | Condição para exibir/ativar |
|---|---|---|
| Rede | `org.kde.plasma.networkmanagement`: `EnabledConnections`, `AvailableDevices`, `NetworkStatus`, `Handler` | Cartão quando há dispositivo cabeado ou Wi-Fi; alternância Wi-Fi só com rádio e hardware disponíveis |
| Bluetooth | `org.kde.bluezqt`: estado do `Manager` e `connectedDevices` | Cartão somente quando BlueZ está operacional e há adaptador |
| Áudio | `org.kde.plasma.private.volume`: `Context`, `SinkModel`, `PreferredDevice` | Cartão quando o serviço está pronto e há saída real; seleção só aparece com múltiplas saídas |
| Brilho e luz noturna | `ScreenBrightnessControl`, `NightLightInhibitor` e propriedades D-Bus do KWin | Sliders vêm do modelo real de displays; sem suporte, não são criados. Luz noturna depende da interface KWin e pode ser suspensa pelo mecanismo PowerDevil |
| Energia e bateria | `PowerProfilesControl` do PowerDevil e `BatteryControlModel` do Plasma | Perfis são mostrados apenas se o daemon oferecer opções; bateria só aparece quando detectada |
| Não perturbe | `Notifications.Globals` do applet nativo de notificações | Estado e alternância são os do gerenciador de notificações do Plasma |
| Multimídia | `Mpris2Model` do Plasma Workspace | Cartão e botões aparecem conforme jogador e capacidades MPRIS disponíveis |

Links de configuração abrem os módulos nativos do System Settings. O plasmoid não executa shell, sudo ou comandos privilegiados e não contém estados simulados. Todos os modelos notificam atualizações de estado à interface.

## Proveniência técnica

As APIs foram conferidas no código-fonte KDE da branch `Plasma/6.6`, sem copiar scripts ou componentes gráficos de temas externos: [plasma-nm `2572bcb`](https://invent.kde.org/plasma/plasma-nm/-/tree/2572bcb978ce932ec322634eb9cfef64bc5495d9), [plasma-pa `042e7f2`](https://invent.kde.org/plasma/plasma-pa/-/tree/042e7f21edcbd5859946d5af11f58bdd4dfdc386), [bluedevil `772a1c6`](https://invent.kde.org/plasma/bluedevil/-/tree/772a1c63e5ef7105a8fe722a58dcc9028bb32b8f), [powerdevil `7e72310`](https://invent.kde.org/plasma/powerdevil/-/tree/7e723103b8ab0e9434d336a5b0abbca1eae67b87) e [plasma-workspace `7899936`](https://invent.kde.org/plasma/plasma-workspace/-/tree/78999364c18b14388c3a56ddd07cf239e92766f8). O uso é de APIs fornecidas pelo Plasma 6 já incluído na imagem.

## Validação e limites

Os testes automatizados validam metadados e caminho de empacotamento, registro único no painel, módulos nativos, ações disponíveis, gates de hardware e ausência de execução privilegiada. O pipeline executa o parser `qmlformat` do Qt como dependência de build temporária e a remove antes de gerar a imagem final. `bash -n`, `node --check` e `git diff --check` também são executados. A imagem ISO não é gerada nesta etapa. Resolução de imports QML dentro de uma sessão Plasma, estados reais de hardware, interação, blur e screenshots ainda exigem boot em VM; não são inferidos pelo parser.
