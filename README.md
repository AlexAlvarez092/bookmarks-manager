# bookmarks-manager

Sincroniza automáticamente los marcadores (bookmarks) de **Safari** hacia otros
navegadores en macOS, de forma unidireccional: Safari es siempre la fuente de
verdad y los navegadores destino terminan con una copia exacta de su árbol de
marcadores (carpetas incluidas).

## Motivación

Safari es el navegador principal donde se gestionan los marcadores, pero se
usan otros navegadores (Chrome, Brave, ...) en el día a día. No existe una
sincronización nativa entre ellos, así que este proyecto automatiza:

- Leer la estructura completa de marcadores de Safari.
- Volcarla en el navegador destino, **sobrescribiendo** su archivo de
  marcadores para que quede idéntica a la de Safari (se añaden los nuevos, se
  actualizan los existentes y se eliminan los que ya no estén en Safari).

## Alcance actual

- Solo macOS.
- Sincronización unidireccional: Safari → otro navegador (nunca al revés).
- Navegadores destino soportados: **Chrome** y **Brave** (basados en
  Chromium).
- Pensado para ejecutarse periódicamente vía `cron`, una línea por cada
  navegador destino, pasando los parámetros necesarios (navegador, perfil,
  etc.) como argumentos de línea de comandos.
- No se gestionan backups del archivo de marcadores destino ni bloqueos si el
  navegador destino está abierto: si el navegador sobrescribe el archivo al
  cerrarse, la siguiente ejecución del job lo corrige automáticamente.

## Tecnología

- **Python 3** (incluido en macOS), sin dependencias externas:
  - `plistlib` para leer `~/Library/Safari/Bookmarks.plist`.
  - `json` para leer/escribir el archivo `Bookmarks` de Chrome/Brave.

## Uso (previsto)

```bash
python3 safari_bookmarks_sync.py --target chrome [--profile "Default"]
python3 safari_bookmarks_sync.py --target brave  [--profile "Default"]
```

Ejemplo de configuración en `cron` (cada 10 minutos):

```cron
*/10 * * * * /usr/bin/python3 /ruta/al/repo/safari_bookmarks_sync.py --target chrome
*/10 * * * * /usr/bin/python3 /ruta/al/repo/safari_bookmarks_sync.py --target brave
```

> Nota: para leer los marcadores de Safari puede ser necesario conceder
> "Acceso completo al disco" (Full Disk Access) al proceso que ejecute el
> script (por ejemplo, Terminal o `cron`), ya que el archivo de marcadores de
> Safari está protegido por macOS.

## Estado del proyecto

En desarrollo. Consulta los [issues](../../issues) del repositorio para ver
las historias de usuario planificadas y su progreso.
