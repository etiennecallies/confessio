# Welcome to Confessio repository

## Local env with pyenv
```
pyenv virtualenv 3.9.11 confessio
pyenv activate confessio
pip install -r requirements.txt
```

### Install GIS dependencies
Follow instructions [here](https://mits003.github.io/studio_null/2021/07/install-gdal-on-macos/)

## Run unit tests
```shell
python -m unittest
```