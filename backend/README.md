# Backend

Contiene los servicios de servidor del proyecto. Cada servicio debe ser autónomo, documentar su
contrato y conservar sus pruebas junto a su código.

## Convención para un servicio

```text
backend/<servicio>/
├── README.md
├── <código del servicio>
└── tests/
    └── README.md o pruebas ejecutables
```

Actualmente `assistant/` contiene el chatbot. Los servicios futuros deben crearse dentro de
`services/` hasta que tengan nombre y alcance definidos.
