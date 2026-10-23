# llororo.github.io

Web persoal de Miguel Guisantes-Alonso, investigador en sociolingüística.

[llororo.github.io](https://llororo.github.io/)

Áreas de traballo: ideoloxías lingüísticas, lingua e identidade, multilingüismo, linguas minorizadas e política lingüística.

## Arquivo automático de eventos

As comunicacións futuras inclúen os atributos `data-event-date` e `data-event-code` en `index.html`. A acción `archive-events.yml` comproba as datas cada día segundo o fuso horario `Europe/Berlin`.

O evento permanece en «Próximas comunicacións» durante a data indicada. Ó día seguinte, `scripts/archive_events.py` trasládao ó comezo do histórico co ano, o congreso, o título e a autoría, actualiza `sitemap.xml` e oculta o bloque de próximos eventos cando queda baleiro. A acción só crea un commit cando hai un cambio efectivo.

Os elementos do CV usan identificadores permanentes e unha ligazón «#» xunto ó título. O arquivo automático conserva o identificador das comunicacións cando as move ó histórico, para que as ligazóns compartidas continúen funcionando.

## Informe diario de visitas

A web usa Cloudflare Web Analytics mediante o identificador público incluído en `index.html`. A acción `daily-analytics-report.yml` consulta cada mañá os datos do día anterior segundo o fuso horario `Europe/Berlin` e envía un correo cando se rexistraron visitas. O informe inclúe visitas, páxinas vistas, países, procedencias e páxinas consultadas.

O repositorio precisa os segredos `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN`, `REPORT_EMAIL`, `SMTP_USERNAME` e `SMTP_PASSWORD`. O token de Cloudflare debe ter unicamente o permiso de lectura `Account Analytics Read`. A execución manual envía o informe aínda que o total sexa cero, o que permite comprobar a configuración.
