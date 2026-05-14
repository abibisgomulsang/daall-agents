Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

python -m ai_company.main init-folders
python -m ai_company.main meeting --topic "고스틱 광고 효율 개선"
python -m ai_company.main ad --product GOSTICK01
python -m ai_company.main analyze-ads --csv data\naver_ads_sample.csv
