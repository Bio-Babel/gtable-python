# gtable_py

[![PyPI](https://img.shields.io/pypi/v/gtable-python)](https://pypi.org/project/gtable-python/)

Python port of the R **gtable** package (tracks R gtable 0.3.6.9000).

Depends on [`rgrid-python`](https://pypi.org/project/rgrid-python/) (R's grid
graphics re-implemented in Python).

## Installation

```bash
pip install gtable-python
```

Or, for a local development checkout:

```bash
git clone https://github.com/R2pyBioinformatics/gtable_py.git
cd gtable_py
pip install -e ".[dev]"
```

## Quick Start

```python
import gtable_py
```

## Documentation

```bash
pip install -e ".[docs]"
mkdocs serve
```
