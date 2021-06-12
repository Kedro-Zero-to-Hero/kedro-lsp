# kedro-lsp

A [Language Server](https://microsoft.github.io/language-server-protocol/) for the latest version(s) of [Kedro](https://kedro.readthedocs.io/en/latest/). It provides features to enable IDE support for Kedro. For example, you can jump to dataset and parameter definition when constructing the pipeline.

**Note**: This is pre-alpha software.

## Features

* [x] Provide dataset and parameter definition when constructing the pipeline.

> **Note**: I need your help! If you think this project is a good idea, please submit features request via Github Issue.

## Compatibility

Kedro Language Server aims to be compatible with Kedro 0.17.x and above. Currently it is restricted to 0.17.3 and above during pre-alpha phase.

## Installation

```shell
pip install kedro-lsp
```

## Usage

### Standlone

```
python -m kedro_lsp
```

### Visual Studio Code

To use it with visual studio code, install the Kedro extension from Visual Studio Code Marketplace.

### Pycharm

TBD

## Todos

* [ ] Provide diagnostic when there is a typo in dataset or parameter name in the pipeline.
* [ ] Be Kedro environment-aware

## License

MIT
