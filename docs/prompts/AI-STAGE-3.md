# IFBA OS — ETAPA 3/5
## Visão de tela, acessibilidade e orientação visual interativa

Continue o IFBA OS utilizando a arquitetura e os componentes das etapas anteriores.

### MISSÃO

Permitir que o assistente compreenda o contexto visual do desktop XFCE4 e ajude estudantes a utilizar aplicativos reais.

Exemplo:

O estudante abre o Eclipse e pergunta:

"Como faço para criar uma classe Java?"

O assistente deve identificar o aplicativo, analisar a interface e orientar o estudante, destacando visualmente os controles corretos.

Não implemente uma demonstração estática.

O sistema deve funcionar com aplicativos reais.

### 1. INSPEÇÃO

Leia a documentação e o roadmap.

Identifique:

- Sessão gráfica atual.
- Suporte a X11.
- Bibliotecas de acessibilidade.
- Serviços existentes do assistente.
- Interface GTK.
- Permissões de captura de tela.

Não assuma que a sessão utiliza Wayland.

### 2. DETECÇÃO DE JANELAS

Implemente um serviço capaz de identificar:

- Janela ativa.
- Aplicativo responsável.
- Título.
- Geometria.
- Estado da janela.
- Mudanças de foco.

Utilize interfaces adequadas ao X11 e ao ambiente XFCE4.

Evite polling excessivo.

### 3. ACESSIBILIDADE

Integre AT-SPI2.

Recursos:

- Consultar árvore de acessibilidade.
- Identificar botões.
- Identificar menus.
- Identificar campos de texto.
- Consultar nomes e descrições.
- Consultar posições quando disponíveis.
- Identificar controles desabilitados.
- Detectar mudanças na interface.

Trate aplicativos que não disponibilizam informações suficientes.

Não invente coordenadas.

### 4. CAPTURA DE TELA

Implemente captura sob demanda.

Requisitos:

- Autorização explícita do usuário.
- Captura da janela ativa quando possível.
- Opção de capturar área selecionada.
- Pré-visualização antes do envio.
- Aviso de compartilhamento com serviço remoto.
- Redução de resolução quando apropriado.
- Tratamento de falhas.
- Não capturar continuamente em segundo plano.
- Não salvar screenshots sem necessidade.

Não envie telas de login, campos de senha ou informações sensíveis sem controles específicos.

### 5. MODELO MULTIMODAL

Implemente suporte a modelos NVIDIA que aceitem imagens.

O assistente deverá combinar:

- Pergunta do estudante.
- Identidade do aplicativo.
- Elementos acessíveis.
- Captura de tela autorizada.
- Contexto da conversa.

O modelo deve retornar uma resposta estruturada contendo:

- Explicação.
- Próxima etapa.
- Identificador do elemento sugerido.
- Grau de confiança.
- Necessidade de confirmação.

Valide as respostas estruturadas antes de utilizá-las.

Não confie cegamente em coordenadas fornecidas pelo modelo.

### 6. OVERLAY VISUAL

Implemente um componente gráfico leve que possa destacar elementos reais.

Recursos:

- Contorno verde ao redor do controle.
- Destaque temporário.
- Tooltip com instruções.
- Reposicionamento quando a janela se mover.
- Atualização após redimensionamento.
- Encerramento automático.
- Botão para cancelar orientação.
- Não bloquear a interação com o aplicativo.

Utilize GTK/X11 ou outra solução compatível com a arquitetura existente.

O overlay não deve roubar foco indevidamente.

### 7. MODO TUTORIAL

Implemente orientação passo a passo.

Exemplo no Eclipse:

1. Identificar o projeto Java.
2. Localizar o menu ou ação de criação de classe.
3. Destacar o controle correto.
4. Esperar interação do estudante.
5. Detectar mudança na interface.
6. Orientar a próxima etapa.
7. Confirmar o resultado.

Considere que menus e layouts podem variar entre versões do Eclipse.

Não dependa exclusivamente de coordenadas fixas.

Não afirme que uma ação ocorreu sem confirmação.

### 8. PRIVACIDADE

Implemente:

- Indicador de captura ativa.
- Consentimento por sessão ou operação.
- Cancelamento.
- Exclusão de dados temporários.
- Bloqueio de captura quando necessário.
- Registro local mínimo de operações, sem conteúdo sensível.
- Controle de permissões nas configurações.

O modo padrão deve ser orientação, não controle automático.

### 9. TESTES

Teste:

- Detecção de janela.
- Identificação de controles.
- Alteração de foco.
- Movimentação de janelas.
- Redimensionamento.
- Overlay.
- Cancelamento.
- Falha do modelo visual.
- Aplicativos sem acessibilidade adequada.
- Coordenadas inválidas.
- Captura não autorizada.

Realize testes de integração no Eclipse quando disponível.

Se não estiver instalado, utilize um aplicativo GTK de teste e documente a limitação.

### 10. LOOP ENGINEERING

INSPECIONAR → IMPLEMENTAR → EXECUTAR → OBSERVAR → CORRIGIR → TESTAR NOVAMENTE.

Não considere concluído apenas porque uma captura foi enviada ao modelo.

O objetivo é destacar corretamente um controle real e acompanhar a interação.

Registre evidências e limitações.

Atualize o roadmap após cada ciclo.

### 11. GIT

Trabalhe em `development`.

Antes de cada commit, confirme:

`Leonardo de Almeida Silva <nardocontapc1234@gmail.com>`

Não reescreva o histórico.

### CRITÉRIOS DE ACEITAÇÃO

- [ ] Janela ativa identificada.
- [ ] Árvore de acessibilidade consultada.
- [ ] Captura autorizada funcionando.
- [ ] Modelo multimodal integrado.
- [ ] Respostas estruturadas validadas.
- [ ] Overlay funcional.
- [ ] Orientação passo a passo.
- [ ] Cancelamento funcionando.
- [ ] Privacidade implementada.
- [ ] Testes documentados.

Continue os ciclos até entregar uma implementação funcional e verificável.