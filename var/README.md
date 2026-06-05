# Local Runtime Data

Esta carpeta agrupa artefactos locales generados durante desarrollo.

- `db/`: base SQLite local (`db.sqlite3`).

El contenido de `var/` no se versiona. Si necesitas recrearlo, ejecuta:

```sh
make migrate
make insert-data
```

