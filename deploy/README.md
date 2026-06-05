# Deploy

Archivos de despliegue y runtime fuera del código Django.

## Docker

- `docker/Dockerfile`: imagen de producción.
- `docker/docker-compose.yml`: stack local con PostgreSQL y web.

Usa los comandos del `Makefile` desde la raíz:

```sh
make docker-build
make docker-up
make docker-down
```

`.dockerignore` permanece en la raíz porque Docker lo evalúa desde el contexto de build del repositorio.

