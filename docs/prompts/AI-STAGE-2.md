# IFBA OS — ETAPA 2/5

## NVIDIA API, conversação e integração nativa com XFCE4

Continue o desenvolvimento do IFBA OS a partir da implementação da etapa anterior.

### MISSÃO

Implementar um assistente educacional funcional, utilizando a API NVIDIA, integrado ao ambiente XFCE4.

A IA deverá ser acessível diretamente pelo sistema operacional, com interface moderna e configurações individuais.

Não crie um desktop fictício em Electron ou HTML.

### 1. CONTEXTO OBRIGATÓRIO

Leia:

- `AGENTS.md`
- `docs/ARCHITECTURE.md`
- `docs/AI-ASSISTANT.md`
- `docs/SECURITY.md`
- `docs/PROJECT-ROADMAP.md`

Inspecione a implementação existente. Esses documentos ainda não existiam quando a etapa foi solicitada; crie-os ou atualize-os.

Reutilize os componentes já desenvolvidos.

Não substitua a arquitetura sem necessidade.

### 2. CLIENTE NVIDIA

Implemente um cliente para a API NVIDIA NIM hospedada.

Endpoint de referência: `https://integrate.api.nvidia.com/v1`

Utilize a documentação oficial atual para validar endpoints, autenticação e capacidades.

Requisitos:

- Chave individual obtida do cofre de credenciais.
- Seleção de modelo.
- Streaming de respostas, quando suportado.
- Timeouts.
- Cancelamento de requisições.
- Tratamento de erros HTTP.
- Tratamento de rate limits.
- Retries limitados com backoff.
- Tratamento de indisponibilidade.
- Controle de contexto.
- Limites de tokens configuráveis.
- Validação de compatibilidade do modelo.

Não presuma que todos os modelos aceitam imagens ou ferramentas.

Não exponha a chave nos logs.

### 3. INTERFACE GTK

Implemente uma interface moderna para conversação:

- Histórico de mensagens.
- Campo de entrada.
- Streaming visual.
- Botão de interromper geração.
- Indicador de processamento.
- Mensagens de erro compreensíveis.
- Seleção de conversas.
- Nova conversa.
- Configurações.
- Estado sem API key.
- Suporte a tema escuro.
- Acessibilidade por teclado.

A interface deve combinar com a identidade visual do IFBA OS e não precisa permanecer aberta continuamente.

### 4. INTEGRAÇÃO COM XFCE4

Implemente:

- Atalho global configurável para abrir o assistente.
- Entrada no menu de aplicativos.
- Ícone no painel, quando tecnicamente viável.
- Integração com notificações.
- Inicialização do serviço junto à sessão.
- Abertura rápida da janela de conversa.

Evite conflitos com atalhos existentes. O assistente não deve impedir o funcionamento de outros aplicativos.

### 5. CONTEXTO DO SISTEMA

Permita que o assistente receba informações não sensíveis e autorizadas:

- Nome do aplicativo ativo.
- Versão do sistema.
- Idioma.
- Aplicativos instalados.
- Ambiente gráfico.
- Preferências configuradas.

Implemente mecanismos para controlar quais informações são compartilhadas.

Não envie automaticamente arquivos pessoais ou capturas de tela.

### 6. ASSISTENTE EDUCACIONAL

Configure instruções para que o assistente explique conceitos, ajude com programação e aplicativos, adapte explicações ao nível informado, trabalhe com Java/Python/redes e outras disciplinas, incentive compreensão, reconheça incertezas e não invente ações no sistema.

Diferencie claramente orientações de ações efetivamente realizadas.

### 7. TESTES

Teste cliente HTTP, autenticação, limites de uso, streaming, cancelamento, ausência de internet, modelo inválido, persistência, isolamento por usuário e integração com o serviço local. Use respostas simuladas somente nos testes.

### 8. LOOP ENGINEERING

Execute ciclos de inspeção, implementação, testes, correção, integração, documentação e commit. Após cada ciclo, revise o roadmap e continue com a próxima pendência. Não declare a API funcional sem um teste real autorizado com credenciais disponíveis. Sem chave, valide com mocks e registre que a integração real está pendente. Não interrompa componentes independentes por falta de uma chave.

### 9. GIT E DOCUMENTAÇÃO

Preserve `development`. Confira identidade antes de commits:

`Nardoalm <nardocontapc1234@gmail.com>`

Não altere commits antigos, a menos que pertençam a um usuário GitHub chamado `leonardo`. Atualize documentação, testes e roadmap.

### CRITÉRIOS DE ACEITAÇÃO

- Cliente NVIDIA implementado.
- Interface GTK funcional.
- Streaming implementado quando suportado.
- Conversas persistentes.
- Atalho de abertura funcional.
- Integração com XFCE4.
- Tratamento de erros.
- Chave protegida.
- Testes executados.
- Documentação atualizada.

Continue implementando e corrigindo até atingir os critérios verificáveis.
