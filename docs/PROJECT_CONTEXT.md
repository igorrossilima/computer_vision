# Computer Vision — contexto do projeto

## Objetivo

O projeto é uma base modular e reutilizável de visão computacional. O runtime deve aceitar fontes de vídeo, aplicar uma sequência de módulos independentes e permitir que novas funcionalidades sejam adicionadas sem acoplar suas regras ao core.

Casos existentes ou previstos incluem:

- desfoque facial;
- detecção de incêndio;
- detecção de uso de celular ao dirigir;
- monitoramento de área;
- detecção e conformidade de EPI;
- reconhecimento de cinto;
- novos problemas de visão computacional que surjam de casos reais.

Além do runtime, o projeto deve construir gradualmente um fluxo reutilizável de desenvolvimento de modelos: coleta, extração, curadoria, anotação, preparação de dataset, treinamento, validação, versionamento de experimentos e integração de modelos aprovados.

O projeto tem caráter de aprendizado. A evolução deve favorecer compreensão, entregas incrementais e abstrações motivadas por problemas concretos.

## Visão geral das duas áreas

```text
DESENVOLVIMENTO DO MODELO

dados -> extração -> curadoria -> anotação -> dataset
      -> treinamento -> validação -> modelo aprovado
                                      |
                                      v
RUNTIME

câmera/vídeo -> VisionApp -> ModuleManager -> plugin -> inferência
```

O ponto de encontro é o artefato de modelo validado. O pipeline de treinamento não deve ser executado dentro de um plugin do runtime.

## Estrutura relevante do repositório

```text
computer_vision/
├── AGENTS.md
├── config/
│   └── modules.yaml
├── docs/
│   └── PROJECT_CONTEXT.md
├── modules/
│   ├── face_blur/
│   ├── fire_detection/
│   ├── phone_drive_safe/
│   └── security/
├── training/
│   ├── configs/
│   ├── data/          # local e ignorado
│   ├── runs/          # local e ignorado
│   ├── scripts/
│   └── README.md
├── vision_core/
│   ├── app.py
│   ├── controls.py
│   ├── module.py
│   ├── module_manager.py
│   ├── plugin_loader.py
│   └── sources/       # placeholders atuais
├── testes/            # experimentos legados
├── main.py
├── requirements.txt
└── .gitignore
```

Esta árvore mistura arquivos versionados e diretórios locais ignorados. A presença local de dados ou runs não significa que o pipeline correspondente esteja implementado.

## Runtime atual

### `main.py`

Resolve `config/modules.yaml`, interpreta `--camera` ou `--video`, cria `ModuleManager` e `KeyboardControls`, carrega os plugins e inicia `VisionApp`.

### `VisionApp`

`vision_core/app.py` possui o loop principal. Ele abre a fonte com OpenCV, lê frames, passa cada frame pelo manager, mostra o resultado, interpreta teclado e libera os recursos ao sair.

O core não deve saber detalhes de YOLO, classes, ROI, EPI, fogo ou celular. Essas decisões pertencem aos plugins.

### `VideoModule`

`vision_core/module.py` define o contrato comum:

```python
id: str
name: str

start() -> None
process(frame) -> frame
stop() -> None
```

`start()` permite carregar recursos de forma tardia; `process()` transforma o frame; `stop()` libera recursos.

### `ModuleManager`

`vision_core/module_manager.py`:

- registra módulos por `id`;
- carrega um módulo na primeira ativação;
- ativa, desativa e alterna seu estado;
- processa somente os módulos ativos;
- encerra módulos carregados ao finalizar.

### `KeyboardControls`

`vision_core/controls.py` associa uma tecla a um `module_id` e delega o toggle ao manager. Os atalhos vêm da configuração, evitando alterações no core para cada plugin.

### `plugin_loader.py`

O loader lê a lista `modules` do YAML, importa cada caminho, procura uma fábrica `create_module()`, valida se o retorno é `VideoModule`, registra o módulo, associa o atalho e ativa itens marcados com `enabled: true`.

Lacuna conhecida: o loader chama `factory()` sem argumentos. O campo YAML `options` ainda não é encaminhado à fábrica. O módulo `security` já aceita `roi` e `confidence`, por isso é o primeiro caso concreto que poderá motivar essa evolução. Ela não deve ser implementada apenas por antecipação.

## Plugins existentes

### Face blur

Detecta rostos e aplica desfoque às regiões detectadas.

### Fire detection

Carrega um modelo Ultralytics YOLO próprio no `start()`, executa inferência em `process()` e libera a referência no `stop()`.

### Phone drive safe

Detecta celular com YOLO e também possui alerta sonoro.

### Security

Detecta pessoas, calcula se o centro da detecção está dentro de uma ROI normalizada e sinaliza possível intrusão. A implementação aceita `roi` e `confidence`, mas sua entrada no `config/modules.yaml` está comentada e as opções ainda não são propagadas pelo loader.

## Configuração dos módulos

O formato atual é semelhante a:

```yaml
modules:
  - import: modules.face_blur.plugin
    shortcut: b
    enabled: false

  - import: modules.fire_detection.plugin
    shortcut: f
    enabled: false

  - import: modules.phone_drive_safe.plugin
    shortcut: p
    enabled: false
```

A configuração planejada para plugins parametrizados é semelhante a:

```yaml
- import: modules.security.plugin
  shortcut: s
  enabled: false
  options:
    roi: [0.40, 0.32, 0.73, 0.97]
    confidence: 0.4
```

Esse exemplo descreve intenção arquitetural, não comportamento suportado hoje.

## Estado do treinamento

Existe uma estrutura inicial versionada:

```text
training/
├── scripts/
│   ├── extract_frames.py
│   ├── prepare_dataset.py
│   ├── train.py
│   └── validate.py
├── configs/
│   ├── epi_detection/v001.yaml
│   ├── fire_detection/v001.yaml
│   └── seatbelt_detection/v001.yaml
└── README.md
```

No estado documentado, esses scripts, configs e o README são placeholders vazios. Existem também diretórios e artefatos locais sob `training/data/` e `training/runs/`, mas eles estão ignorados e não provam que os scripts genéricos já tenham sido implementados.

Não preencher todos os placeholders em uma única mudança. Cada componente deve nascer quando seu contrato e seu primeiro caso real estiverem claros.

## Organização planejada dos dados

```text
training/data/<problema>/
├── raw/
│   ├── batch_001/
│   │   ├── videos/
│   │   └── images/
│   └── batch_002/
├── extracted/
│   ├── batch_001/
│   └── batch_002/
└── datasets/
    ├── v001/
    └── v002/
```

### Batch

Representa uma coleta. Pode identificar origem, conjunto de câmeras, período, condições ou propósito da coleta. Um novo batch deve normalmente buscar diversidade ou cobrir falhas observadas.

### Versão de dataset

É um snapshot curado e anotado usado em treinamento. Pode combinar dados de vários batches e preservar dados de versões anteriores.

```text
batch_001 != dataset v001
batch_002 != dataset v002
```

A correspondência numérica nunca deve ser presumida.

### Training run

É um experimento com uma versão de dataset, arquitetura e parâmetros. O mesmo dataset pode produzir vários runs:

```text
dataset v001
├── YOLO pequeno, configuração A
├── YOLO pequeno, configuração B
└── YOLO maior, configuração C
```

Assim, versão de dataset e versão de modelo ou nome do run também são conceitos separados.

## Dados cumulativos e matéria-prima

Arquivos em `raw/` são matéria-prima e não devem ser alterados. Vídeos passam por extração de frames; imagens já existentes seguem diretamente para curadoria e anotação.

Versões posteriores do dataset devem reutilizar imagens e anotações válidas. Se a primeira versão contém 1.500 exemplos e um novo batch traz 500 exemplos úteis, a versão seguinte pode combinar os 2.000; não se deve anotar novamente o material antigo sem motivo.

Uma nova versão deve ter uma motivação observável, como aumentar recall em pessoas distantes, reduzir falsos positivos ou incluir novas condições de iluminação.

## Primeira versão de `extract_frames.py`

Responsabilidade:

> Transformar vídeos brutos em um conjunto menor, diverso e rastreável de imagens candidatas à anotação.

O extractor recupera imagens que já existem no vídeo; não cria imagens sintéticas. Salvar todos os frames de um vídeo de alta taxa gera muitas cópias quase idênticas e aumenta custo de revisão sem acrescentar diversidade.

A primeira estratégia deve combinar:

```text
intervalo mínimo
    + diferença visual simples
    + limite por vídeo
```

Fluxo conceitual:

```text
abrir vídeo
  -> ler frame
  -> verificar intervalo mínimo
  -> comparar com o último frame salvo
  -> descartar se for muito semelhante
  -> salvar se for suficientemente diferente
  -> respeitar o limite do vídeo
```

Antes da implementação, fechar:

- interface de entrada e saída;
- seleção do batch;
- unidades e valores padrão do intervalo;
- método e limiar de diferença;
- limite por vídeo;
- convenção de nomes;
- política para destino existente;
- dados mínimos de rastreabilidade;
- inclusão ou adiamento de manifest e hash.

Depois da extração, existe uma etapa humana de curadoria para remover blur, irrelevância, redundância e problemas técnicos.

Possíveis evoluções, somente quando justificadas, incluem detecção de blur, mudança de cena, similaridade mais robusta, deduplicação, hash do vídeo, limite adaptativo, priorização por modelo e active learning.

## Manifest e prevenção de reprocessamento

Uma evolução possível é registrar por frame:

```text
frame, video, timestamp, batch, camera, data, hash_do_video
```

Um hash de conteúdo permite reconhecer um vídeo já processado mesmo após renomeá-lo. Essa capacidade melhora rastreabilidade e idempotência, mas não é requisito automático para a primeira versão.

## Anotação e dataset YOLO

Após a curadoria, as imagens podem ser anotadas em formato de object detection. Antes de usar qualquer ferramenta cloud, é necessário confirmar que o envio de dados do cliente é permitido; caso contrário, deve-se usar uma solução local aprovada.

Não recortar manualmente cada EPI em uma nova imagem. Preserve o frame completo e desenhe bounding boxes para os objetos relevantes.

Formato conceitual:

```text
frame_001.jpg
frame_001.txt
```

O label YOLO registra classe e coordenadas normalizadas. Um dataset treinável pode seguir:

```text
datasets/v001/
├── images/
│   ├── train/
│   ├── val/
│   └── test/
├── labels/
│   ├── train/
│   ├── val/
│   └── test/
└── data.yaml
```

### Prevenção de vazamento

Frames consecutivos de um mesmo vídeo são correlacionados. Não divida aleatoriamente frames quase idênticos entre train, val e test. Sempre que possível, separe por vídeo, trecho, câmera, período ou cenário.

## Primeiro caso completo: EPI

A hipótese inicial é um detector multiclasses único, começando com transfer learning em uma variante pequena da família YOLO já conhecida pelo projeto. Isso reduz variáveis enquanto o fluxo completo é aprendido.

Classes candidatas incluem pessoa, capacete, colete, óculos e luvas, mas a lista não está fechada. A decisão depende de requisitos e de análise dos dados reais. Objetos pequenos podem ocupar poucos pixels e ser inviáveis em determinadas distâncias ou câmeras; primeiro crie um baseline e meça.

Detectar um capacete não é o mesmo que afirmar que uma pessoa está sem capacete. A estratégia inicial é:

```text
detector encontra pessoas e EPIs
    -> aplicação associa EPIs a cada pessoa
    -> regra de conformidade avalia presença/ausência
```

Não coloque toda a regra de conformidade dentro do modelo sem evidência de que isso seja necessário.

Como referência operacional, 300–500 frames diversos podem sustentar um primeiro experimento de viabilidade. Uma primeira versão mais séria pode buscar aproximadamente 1.500–3.000 imagens anotadas e diversas. São referências, não garantias nem requisitos rígidos.

Busque diversidade de pessoas, câmeras, distâncias, iluminação, ângulos, oclusões, quantidade de pessoas, uso correto, ausência de EPI, casos negativos e objetos visualmente semelhantes.

## Scripts planejados

### `prepare_dataset.py`

Deve organizar dados anotados no formato utilizado pelo treinamento. Seu contrato depende do formato real de exportação da ferramenta de anotação e não deve ser fechado antecipadamente.

### `train.py`

Deve permanecer genérico enquanto isso for simples, com uso futuro semelhante a:

```bash
python training/scripts/train.py --config training/configs/epi_detection/v001.yaml
```

O mesmo código poderá receber a configuração de outro problema. Não crie um framework multi-engine antes de existir um segundo mecanismo real que torne o script difícil de manter.

### `validate.py`

Deve avaliar o modelo por métricas e por comportamento real. A existência de pesos gerados não representa aprovação. Analise Precision, Recall, mAP, matriz de confusão, falsos positivos, falsos negativos e vídeos representativos.

## Integração ao runtime

Somente um modelo minimamente validado deve originar `modules/epi_detection/`. O novo módulo deverá implementar `VideoModule`, carregar seu próprio modelo e manter as regras específicas fora do core.

Estrutura possível, quando chegar o momento:

```text
modules/epi_detection/
├── __init__.py
├── plugin.py
└── models/
```

Essa árvore é uma intenção futura e não deve ser criada antes da etapa de integração.

## Versionamento e privacidade

O `.gitignore` atual exclui novos pesos `*.pt`, `training/data/**/raw/`, `training/data/**/extracted/`, `training/data/**/datasets/` e `training/runs/`.

Devem ser versionados código, configurações e documentação. Não devem ser adicionados novos vídeos, imagens de cliente, datasets, runs ou pesos.

Algumas mídias e pesos antigos continuam rastreados porque precedem as regras atuais. Isso é estado legado; qualquer remoção do índice precisa ser uma tarefa explícita e revisada.

## Estado implementado e roadmap

### Implementado no código

- core modular do runtime;
- contrato e manager de módulos;
- atalhos de teclado configuráveis;
- carregamento dinâmico de plugins;
- plugins de face blur, fire detection, phone drive safe e security;
- esqueleto versionado de `training/`;
- regras de ignore para novos dados, runs e pesos.

### Presente apenas como placeholder ou planejamento

- scripts reais de extração, preparação, treinamento e validação;
- configurações preenchidas de treinamento;
- classes definitivas de EPI;
- dataset versionado de EPI como conceito reproduzível;
- modelo EPI treinado e validado;
- plugin de EPI;
- manifest e prevenção por hash;
- model registry;
- múltiplos engines de treinamento;
- automação avançada de anotação.

### Ordem recomendada para EPI

```text
1. analisar o material real e suas restrições
2. organizar a primeira coleta em um batch
3. definir e implementar a primeira versão de extract_frames.py
4. extrair candidatos e realizar curadoria
5. definir classes viáveis
6. anotar bounding boxes
7. preparar dataset v001 sem vazamento
8. configurar e treinar um baseline
9. validar métricas e comportamento real
10. analisar erros
11. coletar novo batch direcionado aos erros
12. criar nova versão cumulativa do dataset
13. repetir treinamento e validação
14. integrar o modelo aprovado ao runtime como plugin
```

## Regra de evolução

Antes de introduzir uma nova abstração, pergunte:

```text
Existe hoje mais de um caso real que precisa dela?
```

Se não existir, mantenha a solução simples e local. Se existir, extraia o comportamento comum com base nas diferenças observadas, não nas diferenças imaginadas.
