# Swedish property data sources for a Python land-value-tax calculator

Research date: 2026-07-08.

This note summarizes publicly discoverable Swedish data sources that can support a land-value-tax (LVT) calculator. It focuses on sources for land, cadastral/geographic context, assessed/tax values, and observed housing transactions. It does **not** include secret or leaked API keys; any key-based access listed here requires registering with the provider.

## Short answer

There does not appear to be a generally public, no-registration API key for parcel-level Swedish property values or Hemnet/Booli transaction feeds. The most immediately usable open source is SCB's open API for aggregate statistics. Parcel-level property/tax data appears to require authorized access through Skatteverket and/or Lantmäteriet. Booli historically required registration for a caller id/API key, while Hemnet's official BostadsAPI is oriented toward brokers and broker systems rather than open market research access.

## Candidate sources

| Source | Data usefulness | Access/key status | LVT value |
| --- | --- | --- | --- |
| SCB Statistical Database API | Aggregate real-estate prices, title registrations, regional statistics, demographics, income, construction, etc. | Open data, free of charge, no API key noted. PxWebApi 2 supports GET, with limits of 150,000 data cells and 30 calls per 10 seconds; SCB's general open-data page also states CC0 licensing and older/general API limits. | Best first source for national/municipal/county modeling and validation. |
| Skatteverket API: Fastighetstaxering – taxeringsuppgifter | Assessed property-tax information, likely the closest official route to tax-assessment inputs. | Requires Skatteverket API onboarding. Authorization table lists Client Credential Grant with client ID and designated organization e-identification for `Fastighetstaxering – taxeringsuppgifter`. | High value if access is granted; likely not open anonymous public data. |
| Skatteverket API: Beskattningsunderlag – fastighet | Real-estate tax basis/tax data. | Requires Skatteverket API onboarding. Authorization table lists Client Credential Grant with client ID and client secret. | High value for official tax-base modeling, but access appears controlled. |
| Lantmäteriet geodata / API portal | Parcels, cadastral/geographic products, addresses, boundaries, map/geodata context. | API portal lets authorized users manage keys for direct-access services; some products are free, others need agreements/permissions. | Essential for mapping parcels/land areas, but likely separate from value data. |
| Booli | Listings and sold-price/slutpris style data may be useful for valuation models. Historical third-party wrappers show a caller ID/API-key model and sold/listing search concepts. | No current official open API key found. Older wrappers say users must request API credentials from Booli; current public search surfaced third-party scraping APIs instead of official public docs. | Useful market-observation data if credentials or compliant data access are obtained. |
| Hemnet BostadsAPI | Official API documentation exists, but it is described as a unified API for brokers, broker agencies, and broker systems to provide/query Hemnet data. Hemnet support also references reporting sale prices via API through broker systems. | Not a public research API; likely requires broker/system relationship. | Potentially useful for closing prices only through approved integration or licensed/partner access. |
| Third-party scraping/API services for Booli/Hemnet | Structured listing/sold data via vendors such as Apify actors. | Requires vendor API token/payment; terms and legality should be checked before use. | Can bootstrap experiments, but risky as a core official data dependency. |

## Recommended Python-first path

1. **Build the initial model on SCB open data**: start with aggregate price/lagfart tables by municipality/county, plus demographic and income controls. This gives a reproducible no-key baseline.
2. **Add geospatial scaffolding from Lantmäteriet/open geodata**: ingest municipality boundaries and, if available under acceptable terms, parcel or land-area datasets.
3. **Treat parcel-level assessed/tax data as an access project**: apply for Skatteverket API access if the project has an eligible organization/use case.
4. **Use transaction portals only with compliant access**: contact Booli/Hemnet for research/commercial terms or use broker/partner routes. Avoid depending on undocumented scraping for public policy estimates unless legal review approves it.
5. **Model land value separately from building value**: if only total sale prices are available, estimate land residuals using building attributes, tax assessments, zoning/land use, density, location, and replacement-cost proxies.

## Useful implementation notes

- SCB PxWebApi can be called with `requests`/`httpx` and loaded into `pandas`.
- Store raw API responses under `data/raw/<source>/` and normalized tables under `data/processed/`.
- Keep source metadata: source URL, retrieval timestamp, table id, geography level, license/access terms, and transformations.
- Do not commit provider API credentials. Use `.env` or environment variables for any future Skatteverket, Lantmäteriet, Booli, Hemnet, or vendor tokens.

## Source links checked

- SCB open data overview: https://www.scb.se/en/services/open-data-api/
- SCB PxWebApi: https://www.scb.se/en/services/open-data-api/pxwebapi/
- Skatteverket API overview for `fastighetstaxering-taxeringsuppgifter`: https://www7.skatteverket.se/portal/apier-och-oppna-data/utvecklarportalen/api/fastighetstaxering-taxeringsuppgifter/2.0.1/%C3%96versikt
- Skatteverket authorization flows per API: https://www.skatteverket.se/omoss/digitalasamarbeten/borjaanvandaapier/auktorisationsflodenperapi.4.7da1d2e118be03f8e4f8246.html
- Lantmäteriet API portal: https://www.lantmateriet.se/sv/geodata/vara-produkter/produktsupport/api-portalen/
- Hemnet BostadsAPI docs: https://integration.hemnet.se/documentation/v1
- Hemnet support note on sale-price reporting through API/broker systems: https://www.hemnet.se/kundservice/maklare/alla%20kategorier-category-all-categories/hur-jag-rapporterar-in-ett-slutpris-till-hemnets-andelsstatistik-pa-en-bostad-som-inte-annonserats-pa-hemnet-document-bf323d67-5c0c-4c96-a54b-24397e3f9333
- Historical Booli Python wrapper: https://github.com/filipsalo/booliapi
- Historical Booli R wrapper: https://github.com/reinholdsson/rbooli
