# kedro-lsp

A [Language Server](https://microsoft.github.io/language-server-protocol/) for the latest version(s) of [Kedro](https://kedro.readthedocs.io/en/latest/). It provides features to enable IDE support for Kedro. For example, you can jump to dataset and parameter definition when constructing the pipeline.

![](./assets/demo.gif)

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
usage: kedro-lsp [-h] [--version] [--tcp] [--host HOST] [--port PORT] [--log-file LOG_FILE] [-v]

Kedro Language Server: an LSP wrapper for Kedro.

optional arguments:
  -h, --help           show this help message and exit
  --version            display version information and exit
  --tcp                use TCP server instead of stdio
  --host HOST          host for TCP server (default 127.0.0.1)
  --port PORT          port for TCP server (default 2087)
  --log-file LOG_FILE  redirect logs to the given file instead of writing to stderr
  -v, --verbose        increase verbosity of log output

Examples:
    Run from stdio: kedro-lsp
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
