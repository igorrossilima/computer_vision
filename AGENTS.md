# Instruções do projeto para agentes

## Escopo e fonte de verdade

Este arquivo vale para todo o repositório. Antes de alterar arquitetura, módulos do runtime, pipeline de treinamento, datasets ou integração de modelos, leia também `docs/PROJECT_CONTEXT.md`.

O código e a configuração presentes no repositório são a fonte de verdade sobre o estado atual. O documento de contexto descreve também intenções futuras; não trate itens planejados como se já estivessem implementados nem como autorização automática para implementá-los.

Ao encontrar divergência entre documentação e código:

1. confirme o comportamento no código;
2. explique a divergência;
3. faça apenas a mudança necessária para a tarefa atual;
4. atualize a documentação se a tarefa alterar uma decisão registrada.

## Propósito do projeto

Este projeto deve evoluir como uma plataforma modular e reutilizável de visão computacional, e não como uma aplicação isolada de YOLO. Ele possui duas áreas separadas:

- runtime de vídeo e inferência, composto pelo core e por plugins;
- desenvolvimento de modelos, composto por coleta, extração, curadoria, anotação, preparação de datasets, treinamento e validação.

O projeto também é didático. Prefira implementações incrementais, código simples e explicações claras. Antes de criar uma abstração, verifique se existe mais de um caso real que a justifique.

## Arquitetura do runtime

O fluxo principal é:

```text
câmera ou vídeo
    -> VisionApp
    -> ModuleManager
    -> módulos ativos
    -> frame processado
```

Responsabilidades:

- `vision_core/app.py`: controla captura, loop de frames, exibição, teclado e liberação de recursos. Não deve conter lógica específica de modelos ou domínios como incêndio, EPI ou celular.
- `vision_core/module.py`: define o contrato `VideoModule`, com `id`, `name`, `start()`, `process(frame)` e `stop()`.
- `vision_core/module_manager.py`: registra módulos, controla ativação, executa apenas módulos ativos e encerra módulos carregados.
- `vision_core/controls.py`: associa teclas à ativação e desativação dos módulos.
- `vision_core/plugin_loader.py`: lê `config/modules.yaml`, importa plugins e chama `create_module()`.
- `modules/<nome>/plugin.py`: contém a lógica específica de cada funcionalidade e deve expor `create_module()` retornando um `VideoModule`.

Preserve estes limites:

- não coloque lógica específica de plugin dentro de `VisionApp` ou do core;
- não acople o pipeline de treinamento aos plugins do runtime;
- mantenha modelos, recursos e ciclo de vida sob responsabilidade do módulo que os utiliza;
- use configuração para diferenças entre casos quando isso permanecer simples;
- não duplique scripts por domínio quando um script genérico mais uma configuração resolver o caso real.

## Estado atual relevante

Já existem:

- core modular com `VisionApp`, `VideoModule`, `ModuleManager`, `KeyboardControls` e carregamento de plugins;
- plugins de desfoque facial, incêndio, celular ao dirigir e monitoramento de área;
- `config/modules.yaml` com face blur, fire detection e phone drive safe; o módulo security está comentado;
- estrutura inicial de `training/`, com scripts e configurações versionados, porém ainda vazios;
- dados e resultados de experimentos locais sob `training/`, ignorados pelo Git.

Dívida conhecida: `plugin_loader.py` chama atualmente `factory()` sem encaminhar o campo `options` do YAML. O plugin `security` aceita `roi` e `confidence`, mas essa configuração ainda não chega até `create_module()`. Não corrija isso fora de uma tarefa que realmente necessite de plugins parametrizados.

Os arquivos em `vision_core/sources/` são placeholders vazios; atualmente `VisionApp` usa `cv2.VideoCapture` diretamente. Não apresente essa abstração como implementada.

Os arquivos em `testes/` são experimentos e provas de conceito legadas. Não presuma que formem uma suíte automatizada.

## Regras do pipeline de treinamento

Os scripts de `training/scripts/` devem ser genéricos enquanto isso permanecer simples. Regras específicas de um problema devem ficar em configurações ou dados do problema, não codificadas diretamente em ferramentas como `extract_frames.py` e `train.py`.

Mantenha estes conceitos distintos:

- batch: uma coleta de dados, por exemplo uma câmera, período ou condição específica;
- versão de dataset: um snapshot curado e anotado que pode combinar vários batches;
- training run: um experimento executado sobre uma versão de dataset com modelo e parâmetros definidos.

Portanto, não presuma `batch_001 == dataset v001`, nem `dataset v001 == um único treinamento`.

Princípios obrigatórios:

- preserve arquivos brutos; não os modifique no lugar;
- preserve anotações já produzidas e faça versões posteriores cumulativas quando apropriado;
- priorize diversidade sobre volume de frames quase idênticos;
- evite vazamento entre treino, validação e teste; prefira separar por vídeo, trecho, câmera, período ou cenário;
- trate previsões usadas na anotação como sugestões sujeitas a revisão humana;
- não considere a geração de `best.pt` como validação suficiente;
- avalie Precision, Recall, mAP, matriz de confusão, falsos positivos, falsos negativos e comportamento em vídeos reais;
- integre um modelo ao runtime somente após existir validação mínima adequada.

Para EPI, as classes ainda não são definitivas. Não assuma que objetos pequenos, como luvas e óculos, sejam detectáveis sem analisar resolução, distância e ângulo do material real. A estratégia inicial separa detecção de pessoas e EPIs da lógica de conformidade: ausência de EPI deve ser inferida pela associação na aplicação, não presumida automaticamente como uma classe de detecção.

## Extração de frames

`training/scripts/extract_frames.py` é a próxima implementação planejada. Antes de codificá-la, defina com o usuário:

1. entrada e saída;
2. estrutura e identificação do batch;
3. intervalo mínimo entre candidatos;
4. método simples de diferença visual;
5. limite por vídeo;
6. nomenclatura dos frames;
7. comportamento quando o destino já contém arquivos;
8. rastreabilidade necessária;
9. se manifest e hash pertencem à primeira versão.

A primeira versão deve permanecer simples: intervalo mínimo, diferença visual e limite por vídeo, seguidos de curadoria humana. Detecção de blur, mudança de cena robusta, deduplicação avançada, priorização por modelo e active learning são evoluções, não requisitos implícitos.

## Dados, privacidade e versionamento

- Nunca adicione ao Git vídeos, imagens, datasets, runs ou pesos novos contendo material de cliente.
- Não envie dados de cliente a serviços externos de anotação ou armazenamento sem autorização explícita e confirmação das políticas aplicáveis.
- Evite expor nomes, caminhos ou conteúdo sensível em documentação, logs e respostas quando isso não for necessário.
- Respeite o `.gitignore`, que cobre `*.pt`, dados brutos, frames extraídos, datasets e `training/runs/`.
- Há mídias e pesos legados já rastreados porque foram adicionados antes das regras atuais. Não os remova do índice nem os apague sem solicitação explícita.

## Forma de trabalhar

- Explique o problema, a decisão e os trade-offs antes de mudanças arquiteturais relevantes.
- Faça a menor mudança coesa que resolva o caso atual; evite refatorações ou formatação sem relação com a tarefa.
- Não preencha placeholders nem implemente todo o roadmap antecipadamente.
- Não crie `engines/`, model registry ou frameworks genéricos antes de existir um segundo caso concreto que exija essa separação.
- Preserve compatibilidade com os módulos existentes ao alterar contratos do core.
- Use type hints e nomes claros quando forem compatíveis com o estilo do arquivo alterado.
- Para validação, execute o menor conjunto de verificações que cubra a mudança. Não inicie treinamentos longos, downloads de modelos, câmera, GUI ou processamento de mídia de cliente sem necessidade explícita.
- Ao concluir, informe o que foi verificado e qualquer validação que não pôde ser executada.

## Prioridade atual

O caminho pretendido para o primeiro ciclo completo de EPI é:

```text
dados reais
    -> extração de frames
    -> curadoria
    -> definição das classes
    -> anotação
    -> dataset v001
    -> treinamento baseline
    -> validação e análise de erros
    -> novos batches orientados por evidências
    -> nova versão do dataset e treinamento
    -> integração do modelo aprovado como plugin
```

Não pule diretamente para `modules/epi_detection/` antes de validar o modelo.
