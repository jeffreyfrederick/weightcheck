import asyncio
import pandas as pd
from httpx import AsyncClient
from aiolimiter import AsyncLimiter
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

    async with throttler:
        print(f"starting web driver #{index}")
        async with async_playwright() as driver:
            try:
                # load gsmarena page
                browser = await driver.chromium.launch(headless=True)

                print(f"(web driver #{index}) loading gsmarena...")
                page = await browser.new_page()
                await page.goto("https://www.gsmarena.com/")
                await page.wait_for_load_state()

                # enter the model and click the 'go' button
                await asyncio.sleep(1)
                print(f"(web driver #{index}) looking up {unit_oem} {unit_model} {unit_type}...")
                await page.locator('#topsearch-text').type(f"{unit_oem} {unit_model}")
                await asyncio.sleep(1)
                await page.locator('#topsearch-text').click()
                await asyncio.sleep(3)
                await page.locator('.go').click()
                await page.wait_for_load_state()

                # if there is more than one search result; raise an exception. otherwise, click on the first result 
                await asyncio.sleep(3)
                choices = await page.locator('xpath=//html/body/div[2]/div[1]/div[2]/div/div[2]/div[1]/div/ul/li[*]/a/strong/span').all_text_contents()
                if len(choices) > 1:
                    raise Exception
                else:
                    await page.locator('.makers').locator(f'a:below(:text("Specs"))').nth(0).click()

                # grab the weight
                await asyncio.sleep(1)
                grams = await page.locator('xpath=//html/body/div[2]/div[1]/div[2]/div/div[2]/table[3]/tbody/tr[2]/td[2]').inner_text()
                grams = grams.split('g')[0]
                pounds = float(grams) / 453.6
                weight = "{:.2f}".format(round(pounds, 2))

                # grab the real OEM
                p_oem = await page.locator('.specs-phone-name-title').inner_text()
                real_oem = p_oem.split(' ')[0]

                # grab the real model
                res = p_oem.split(" ", 1)
                real_model = res[1]
            except:
                # just add 'unknown' to the weight list, leave the rest alone
                oem_list.append(unit_oem)
                model_list.append(unit_model)
                type_list.append(unit_type)
                weight_list.append('UNKNOWN')
                print(model_list)
                print(weight_list)

                # close browser driver
                print(f"(web driver #{index}) finished. closing driver...")
                await browser.close()
                print(f"driver #{index} closed")
            else:
                # append weight to list for saving to excel sheet
                oem_list.append(real_oem)
                model_list.append(real_model)
                type_list.append(unit_type)
                weight_list.append(weight)
                print(model_list)
                print(weight_list)

                # close browser driver
                print(f"(web driver #{index}) finished. closing driver...")
                await browser.close()
                print(f"driver #{index} closed")

async def run():
    model_length = (len(models))
    print(f"looking up \033[36m{model_length}\033[0m models...")

    # slow down tasks using a limiter so we don't overload our system
    throttler = AsyncLimiter(max_rate=1, time_period=18)

    # start loop
    async with AsyncClient() as session:
        tasks = []
        for i in range(0, model_length):
            tasks.append(scrape(i, oem[i], models[i], types[i], weights[i], throttler=throttler))
        results = await asyncio.gather(*tasks)

    # add everything back into the data frame
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