# Data Directory

```text
data/raw/
    source-shaped data

data/processed/
    cleaned and agent-ready data
```

Raw files should not be manually edited.

# Raw Data

## `data/raw/sec_form4.csv`

Source: SEC EDGAR.

Typical fields:

```text
ticker
company_name
owner_name
owner_title
transaction_date
filing_date
transaction_code
acquired_disposed
shares
price
accession_number
source_url
```

## `data/raw/market_data.csv`

Source: Alpha Vantage.

Typical fields:

```text
ticker
date
open
high
low
close
volume
```

## `data/raw/news.csv`

Source: Marketaux.

Typical fields:

```text
ticker
published_at
title
description
content
source
url
```

This file preserves the raw API result before relevance filtering.

# Processed Data

## `data/processed/sec_form4_clean.csv`

Important fields:

```text
ticker
company_name
owner_name
owner_title
transaction_date
filing_date
transaction_code
acquired_disposed
shares
price
transaction_value
accession_number
source_url
```

## `data/processed/market_data_clean.csv`

Important fields:

```text
ticker
date
open
high
low
close
volume
daily_return
volume_change
```

## `data/processed/news_clean.csv`

Important fields:

```text
ticker
published_at
title
description
content
source
url
company_name
text
relevance_score
```

Relevance:

```text
2 = target company/ticker appears in title
1 = target company/ticker appears in description/content
0 = no direct company reference
```

Score-0 articles are removed during preprocessing.

## `data/processed/daily_evidence.csv`

Combined daily evidence aligned by `ticker + date`.

Possible fields:

```text
ticker
date
open
high
low
close
volume
daily_return
volume_change
news_count
news_titles
news_urls
insider_transaction_count
insider_names
insider_total_value
```

## `data/processed/news_research_results.csv`

Structured output from `03_news_processing_chain.ipynb`.

Fields:

```text
ticker
published_at
title
source
url
relevance_score
category
classification_reason
event
key_facts
people
organizations
financial_numbers
summary
```

This is the primary news handoff to the Planner and Router agents.

## `data/processed/preprocessing_manifest.json`

Records row counts, column names, dataset fingerprints, output locations, and seed.

# Data Flow

```text
external APIs
-> data/raw/
-> 01_data_preprocessing.ipynb
-> data/processed/
-> 02_evidence_assembly.ipynb
-> daily_evidence.csv
```

News flow:

```text
news.csv
-> news_clean.csv
-> 03_news_processing_chain.ipynb
-> news_research_results.csv
```

# Reproducibility

If raw snapshots already exist:

```text
01_data_preprocessing.ipynb
-> 02_evidence_assembly.ipynb
-> 03_news_processing_chain.ipynb
```

is sufficient to regenerate downstream outputs.
