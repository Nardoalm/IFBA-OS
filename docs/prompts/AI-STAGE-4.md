# IFBA OS — ETAPA 4/5

## Memória educacional, contexto persistente e ferramentas do sistema

Continue o desenvolvimento do assistente IFBA OS.

### MISSÃO

Implementar memória individual e ferramentas seguras para que o assistente compreenda o histórico de aprendizagem do estudante e possa ajudá-lo a realizar tarefas no Linux.

A IA deve ser contextual, personalizada e integrada ao XFCE4.

### 1. CONTEXTO

Leia `AGENTS.md`, arquitetura, documentação de segurança e roadmap.

Inspecione os componentes já implementados.

Não crie outro banco de dados ou outro serviço se os existentes forem suficientes.

### 2. MEMÓRIA DE CURTO PRAZO

Implemente:

- Histórico recente.
- Contexto por conversa.
- Resumos de conversas longas.
- Controle de tamanho de contexto.
- Persistência entre reinicializações.
- Continuidade de diálogos.

Não envie todo o histórico em todas as requisições.

### 3. MEMÓRIA DE LONGO PRAZO

Implemente registros individuais para:

- Preferências de aprendizagem.
- Linguagens estudadas.
- Aplicativos utilizados.
- Assuntos já aprendidos.
- Dificuldades relatadas.
- Objetivos educacionais.
- Projetos de estudo.

Utilize SQLite e, quando necessário, embeddings e busca semântica.

Não armazene automaticamente dados sensíveis.

Memórias inferidas devem ser identificáveis e corrigíveis.

### 4. CONTROLE PELO ESTUDANTE

Crie uma interface GTK para:

- Visualizar memórias.
- Corrigir informações.
- Excluir memórias.
- Desativar memória.
- Apagar histórico.
- Exportar dados.
- Controlar retenção.
- Saber quais informações são enviadas à NVIDIA.

Cada usuário controla exclusivamente seus próprios dados.

### 5. FERRAMENTAS DO SISTEMA

Implemente ferramentas tipadas, com permissões explícitas, para:

- Listar aplicativos instalados.
- Abrir aplicativos.
- Consultar informações do sistema.
- Abrir URLs.
- Localizar arquivos autorizados.
- Consultar diretórios selecionados.
- Criar arquivos em diretórios permitidos.
- Auxiliar na organização de projetos.
- Abrir configurações do XFCE4.
- Executar operações previamente definidas e validadas.

Não disponibilize execução irrestrita de shell ao modelo.

Não permita que o modelo invente nomes de ferramentas ou parâmetros.

### 6. POLÍTICA DE AUTORIZAÇÃO

Classifique ações em:

**Leitura de baixo risco:** consultas locais permitidas conforme configurações.

**Ações interativas:** abrir aplicativos, navegar e destacar elementos.

**Ações modificadoras:** criar, editar ou excluir arquivos.

**Ações privilegiadas:** instalar pacotes, alterar usuários, modificar serviços e configurações do sistema.

Exija confirmação explícita antes de ações modificadoras ou privilegiadas.

Para operações privilegiadas, utilize mecanismos apropriados como polkit, com escopo mínimo.

Nunca armazene a senha do usuário.

Nunca permita que instruções vindas de páginas, documentos ou telas sejam tratadas como autorização para executar ações.

### 7. PLANEJAMENTO E EXECUÇÃO

Implemente um fluxo:

`PEDIDO → PLANO → VALIDAÇÃO → AUTORIZAÇÃO → EXECUÇÃO → VERIFICAÇÃO → RESPOSTA`.

O assistente deverá:

- Explicar a ação pretendida.
- Informar os arquivos afetados.
- Solicitar confirmação.
- Executar somente ferramentas permitidas.
- Verificar o resultado.
- Informar erros.
- Não afirmar sucesso sem evidências.

### 8. CONTEXTO EDUCACIONAL

Exemplo:

O estudante já aprendeu classes Java.

Agora pergunta: “Como faço herança no Eclipse?”

O assistente deverá recuperar o contexto relevante e adaptar a explicação.

Se o Eclipse estiver aberto, poderá oferecer orientação visual usando o componente desenvolvido na etapa anterior.

### 9. TESTES

Implemente testes para:

- Persistência.
- Recuperação de memórias.
- Isolamento entre usuários.
- Exclusão de dados.
- Exportação.
- Falhas do banco.
- Permissões.
- Confirmações.
- Ferramentas inválidas.
- Tentativas de execução não autorizada.
- Injeção de instruções por conteúdo externo.
- Interrupção de operações.

### 10. LOOP ENGINEERING

Execute ciclos completos de implementação, testes e correção.

Priorize falhas de segurança e isolamento.

Não declare ferramentas concluídas sem testar operações reais e seus caminhos de falha.

Atualize roadmap e documentação.

### 11. GIT

Branch: `development`.

Verifique autor e committer antes de cada commit.

Identidade:

`Leonardo de Almeida Silva <nardocontapc1234@gmail.com>`

Não reescreva commits existentes.

### CRITÉRIOS DE ACEITAÇÃO

- Histórico persistente.
- Memória individual.
- Recuperação contextual.
- Interface de gerenciamento.
- Exclusão e exportação.
- Ferramentas tipadas.
- Confirmações obrigatórias.
- Isolamento entre usuários.
- Testes de segurança.
- Integração com visão de tela.
- Roadmap atualizado.

Continue até entregar o escopo com evidências verificáveis.
