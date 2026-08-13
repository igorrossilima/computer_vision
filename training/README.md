# Pipeline de treinamento

Esta pasta reúne as ferramentas genéricas de preparação, treinamento e validação
de modelos. Os dados locais em `training/data/` não devem ser adicionados ao Git.

## Extração seletiva de frames

`extract_frames.py` transforma os vídeos brutos de um batch em um conjunto menor
de imagens candidatas à curadoria e à anotação. Os vídeos originais não são
alterados.

Exemplo:

```bash
python training/scripts/extract_frames.py --problem epi_detection --batch batch_001
```

O comando lê:

```text
training/data/epi_detection/raw/batch_001/videos/
```

e grava os JPGs e um `manifest.csv` em:

```text
training/data/epi_detection/extracted/batch_001/
```

Por padrão, o primeiro frame é salvo e os próximos candidatos são avaliados a
cada segundo. Uma imagem é aceita quando pelo menos 5% dos pixels da cópia de
análise apresentam diferença de intensidade igual ou superior a 25 em relação
ao último frame salvo. A comparação usa uma cópia reduzida em tons de cinza; o
JPG salvo permanece colorido e na resolução original.

Parâmetros disponíveis:

- `--min-interval`: intervalo mínimo entre candidatos, em segundos (padrão: `1.0`);
- `--changed-ratio`: proporção mínima de pixels alterados, entre 0 e 1 (padrão: `0.05`);
- `--pixel-threshold`: diferença mínima de intensidade por pixel, de 1 a 255 (padrão: `25`);
- `--max-frames`: limite de imagens selecionadas por vídeo (padrão: `10`).

Exemplo com ajuste de sensibilidade:

```bash
python training/scripts/extract_frames.py \
  --problem epi_detection \
  --batch batch_001 \
  --min-interval 0.5 \
  --changed-ratio 0.03 \
  --max-frames 20
```

Reexecutar o comando com os mesmos parâmetros não sobrescreve imagens nem
duplica registros no manifest. Parâmetros diferentes podem acrescentar novos
candidatos. A extração é apenas uma pré-seleção: blur, irrelevância e redundância
residual ainda devem ser removidos durante a curadoria humana.
