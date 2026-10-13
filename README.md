# llororo.github.io

Web persoal de Miguel Guisantes-Alonso, investigador en sociolingüística.

[llororo.github.io](https://llororo.github.io/)

Áreas de traballo: ideoloxías lingüísticas, lingua e identidade, multilingüismo, linguas minorizadas e política lingüística.

## Arquivo automático de eventos

As comunicacións futuras inclúen os atributos `data-event-date` e `data-event-code` en `index.html`. A acción `archive-events.yml` comproba as datas cada día segundo o fuso horario `Europe/Berlin`.

O evento permanece en «Próximas comunicacións» durante a data indicada. Ó día seguinte, `scripts/archive_events.py` trasládao ó comezo do histórico co ano, o congreso, o título e a autoría, actualiza `sitemap.xml` e oculta o bloque de próximos eventos cando queda baleiro. A acción só crea un commit cando hai un cambio efectivo.
