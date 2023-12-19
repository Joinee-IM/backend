# Jöinee Backend Service
## Prerequisites
Please make sure you have installed `python 3.10` and `poetry`
## Setup
1. Python environment
   ```shell
   make install
   ```
   and paste environment variables
2. Put `gcp-service-account.json` under `config` directory (you may need to `mkdir` yourself).
3. Run backend service
    ```shell
    make run
    ```
4. Backend openapi documents should be accessed through http://localhost:8000/api/docs
5. For development usage, you may use
   ```shell
   make dev
   ```
   to start server with auto-reload.
## Tests
```shell
make test
```

Note: you may check other usages through `make help` command.
