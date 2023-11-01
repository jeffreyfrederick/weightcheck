import asyncio
import pandas as pd
from httpx import AsyncClient
from aiolimiter import AsyncLimiter
from tenacity import retry
from playwright.async_api import async_playwright

oem_list = []
model_list = []
type_list = []
weight_list = []

df = pd.read_excel("input.xlsx")

oem = df['OEM'].values.tolist()
models = df['MODEL'].values.tolist()
types = df['TYPE'].values.tolist()
weights = df['WEIGHT'].values.tolist()

async def scrape(index, unit_oem, unit_model, unit_type, unit_weight, throttler):
    index += 1
    global models

    async with throttler:
        print(f"starting web driver #{index}")
        async with async_playwright() as driver:
            try:
                browser = await driver.chromium.launch(headless=True)

                # load gsmarena page
                print(f"(web driver #{index}) loading gsmarena...")
                page = await browser.new_page()
                await page.goto("https://www.gsmarena.com/")
                await page.wait_for_load_state()

                # enter the model and click the 'go' button
                print(f"(web driver #{index}) looking up {unit_oem} {unit_model} {unit_type}...")
                await page.locator('#topsearch-text').type(unit_model)
                await asyncio.sleep(1)
                await page.locator('#topsearch-text').click()
                await asyncio.sleep(1)
                await page.locator('.go').click()

                # click on the first search result
                await page.locator('.makers').locator(f'a:below(:text("Specs"))').nth(0).click()

                await asyncio.sleep(1)

                # grab the weight
                grams = await page.locator('xpath=//html/body/div[2]/div[1]/div[2]/div/div[2]/table[3]/tbody/tr[2]/td[2]').inner_text()
                grams = grams.split('g')[0]
                pounds = float(grams) / 453.6
                weight = "{:.2f}".format(round(pounds, 2))

                # append weight to list for saving to Excel sheet
                oem_list.append(unit_oem)
                model_list.append(unit_model)
                type_list.append(unit_type)
                weight_list.append(weight)
                print(model_list)
                print(weight_list)

                # close browser driver
                print(f"(web driver #{index}) finished. closing driver...")
                await browser.close()
                print(f"driver #{index} closed")
            except:
                oem_list.append(unit_oem)
                model_list.append(unit_model)
                type_list.append(unit_type)
                weight_list.append('UNKNOWN')
                print(model_list)
                print(weight_list)



async def run():
    model_length = (len(models))
    print(f"\u001b[32mEPC Mobile Lookup\u001b[0m")
    print(f"looking up \033[36m{model_length}\033[0m models...")

    # slow down tasks using a limiter so we don't overload our system
    throttler = AsyncLimiter(max_rate=1, time_period=8)

    # start loop
    async with AsyncClient() as session:
        tasks = []
        for i in range(0, model_length):
            tasks.append(scrape(i, oem[i], models[i], types[i], weights[i], throttler=throttler))
        results = await asyncio.gather(*tasks)

    # add weights to data frame column
    data = {
    'OEM': oem_list,
    'MODEL': model_list,
    'TYPE': type_list,
    'WEIGHT': weight_list,
    }
    ndf = pd.DataFrame(data)
    ndf.set_index('OEM', inplace=True)

    # output results to excel file
    ndf.to_excel('output.xlsx')

if __name__ == "__main__":
    # lets go!
    asyncio.run(run())