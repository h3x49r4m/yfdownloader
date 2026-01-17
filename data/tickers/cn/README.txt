Chinese Stock Tickers
====================

This folder contains ticker symbols for Chinese companies across multiple exchanges.

Files:
- cn_adrs.txt: Chinese ADRs listed on US exchanges (BABA, JD, BIDU, etc.)
- cn_hk.txt: Chinese companies listed on Hong Kong Stock Exchange (0700.HK, etc.)
- cn_shanghai.txt: Chinese A-shares listed on Shanghai Stock Exchange (600519.SS, etc.)
- cn_shenzhen.txt: Chinese A-shares listed on Shenzhen Stock Exchange (000001.SZ, etc.)
- cn.txt: Index file with usage examples

Usage Examples:
# Download Chinese ADRs only
yfdownloader download --file data/tickers/cn/cn_adrs.txt --days 365

# Download Hong Kong listed Chinese companies
yfdownloader download --file data/tickers/cn/cn_hk.txt --days 365

# Download Shanghai A-shares
yfdownloader download --file data/tickers/cn/cn_shanghai.txt --days 365

# Download Shenzhen A-shares
yfdownloader download --file data/tickers/cn/cn_shenzhen.txt --days 365

# Download all Chinese stocks
yfdownloader download --country cn --days 365

Total tickers: ~500+ across all Chinese markets