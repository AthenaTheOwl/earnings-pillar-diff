# A filing delta needs a comparable period and context

Method update: October 18, 2026. Proposed experiments below are not reported as executed results.

The memo pipeline maps line-item changes to named pillars. Before interpreting a delta, check the filing contexts: issuer, taxonomy tag, unit, duration or instant, fiscal period and dimensional members. A year-to-date cash-flow amount is not the same observation as a single quarter's spend. An amended filing can change a prior value without representing new economic activity.

For a synthetic regression fixture, let a nine-month cash-flow context report 90 and a six-month context report 55. The implied third-quarter flow is 35; comparing 90 directly with a three-month observation answers a different question. Add an instant balance-sheet obligation beside it to ensure the parser does not apply duration arithmetic to a stock.

The proposed acceptance record should identify both accession numbers and context ids, disclose any subtraction, and retain the originally reported baseline when an amendment arrives. A changed context queues the dependent delta, pillar mapping and memo for review. It does not retrospectively alter a recorded decision. This is a data-comparability protocol, not a fresh trading recommendation.

## References

- https://www.sec.gov/structureddata/osd-inline-xbrl.html
- https://github.com/3orionkings/ai-product-team/blob/main/workflows/process-change.md
