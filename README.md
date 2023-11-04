# Web Scraping GSM Arena for Mobile Device Weights

This Python script is designed to scrape the [GSM Arena](https://www.gsmarena.com) website to find and collect the weights of various mobile devices. It takes a list of mobile devices from an Excel file, performs a search on GSM Arena, and extracts the weight information for each device. The collected data is then saved to another Excel file.

## Prerequisites

Before running the script, make sure you have the following dependencies installed:

- Python 3.7+
- [Pandas](https://pandas.pydata.org/)
- [Difflib](https://docs.python.org/3/library/difflib.html)
- [HTTPX](https://www.python-httpx.org/)
- [Asyncio](https://docs.python.org/3/library/asyncio.html)
- [Playwright](https://playwright.dev/python/)
- [Aiolimiter](https://github.com/sloria/aiolimiter)

You can install these dependencies using pip:

```bash
pip install pandas difflib httpx asyncio playwright aiolimiter
```

## Usage

1. Create an Excel file named `input.xlsx` with the following columns:

   - `OEM`: The manufacturer of the mobile device.
   - `MODEL`: The model name of the mobile device.
   - `TYPE`: The type of the mobile device.
   - `WEIGHT`: Leave this column empty.

2. Save the Excel file with the device list.

3. Run the script using the following command:

```bash
python weightcheck.py
```

The script will initiate a web driver for each device, search for the device on GSM Arena, extract its weight, and save the results to a new Excel file named `output.xlsx`. If a device cannot be found or an error occurs during scraping, the weight will be marked as 'UNKNOWN' in the output file.

## Example Excel Input (input.xlsx)

| OEM    | MODEL     | TYPE     | WEIGHT |
| ------ | --------- | -------- | ------ |
| Apple  | iPhone 12 | Smartphone |        |
| Samsung | Galaxy S21 | Smartphone |       |
| Google | Pixel 6 | Smartphone |        |
| ...    | ...       | ...      | ...    |

## Example Excel Output (output.xlsx)

| OEM    | MODEL     | TYPE     | WEIGHT |
| ------ | --------- | -------- | ------ |
| Apple  | iPhone 12 | Smartphone | 0.40   |
| Samsung | Galaxy S21 | Smartphone | 0.40   |
| Google | Pixel 6 | Smartphone | 0.37   |
| ...    | ...       | ...      | ...    |

Please note that this script relies on web scraping and might be subject to changes in the GSM Arena website structure. It's essential to use it responsibly and respect the website's terms of service.
