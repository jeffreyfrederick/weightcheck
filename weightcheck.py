import asyncio
import pandas as pd
import difflib
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

    def print_lists():
        print(oem_list)
        print(model_list)
        print(weight_list)

    def append_success():
        oem_list.append(real_oem)
        model_list.append(real_model)
        type_list.append(unit_type)
        weight_list.append(weight)
        print_lists()

    def append_fail():
        oem_list.append(unit_oem)
        model_list.append(unit_model)
        type_list.append(unit_type)
        weight_list.append('UNKNOWN')
        print_lists()

    async with throttler:
        print(f"starting web driver #{index}")
        async with async_playwright() as driver:
            try:
                # load gsmarena page and search for our mobile device
                browser = await driver.chromium.launch(headless=True)
                print(f"(web driver #{index}) loading gsmarena...")
                page = await browser.new_page()
                search_query = (unit_oem + " " + unit_model)
                search_query = search_query.replace(" ", "+")
                await page.goto(f"https://www.gsmarena.com/res.php3?sSearch={search_query}")

                # find the best match for our search query and click on it
                await asyncio.sleep(4)
                print(f"(web driver #{index}) looking up {unit_oem} {unit_model} {unit_type}...")
                result_choices = await page.locator('xpath=//html/body/div[2]/div[1]/div[2]/div/div[2]/div[1]/div/ul/li[*]/a/strong/span').all_text_contents()
                best_choice = difflib.get_close_matches(unit_model, result_choices, cutoff=.35)
                await page.get_by_role("strong").get_by_text(best_choice[0], exact=True).click()

                # grab the weight
                await asyncio.sleep(4)
                grams = await page.locator('xpath=//html/body/div[2]/div[1]/div[2]/div/div[2]/table[3]/tbody/tr[2]/td[2]').inner_text()
                grams = grams.split('g')[0]
                pounds = float(grams) / 453.6
                weight = "{:.2f}".format(round(pounds, 2))

                # grab the real OEM
                page_oem = await page.locator('.specs-phone-name-title').inner_text()
                real_oem = page_oem.split(' ')[0]

                # grab the real model
                page_model = page_oem.split(" ", 1)
                real_model = page_model[1]
            except:
                # just add 'unknown' to the weight list, leave the rest alone
                append_fail()
                await browser.close()
                print(f"driver #{index} closed")
            else:
                # append weight to list for saving to excel sheet
                append_success()
                await browser.close()
                print(f"driver #{index} closed")

async def run():
    model_length = (len(models))
    print(f"looking up \033[36m{model_length}\033[0m models...")

    # slow down tasks using a limiter so we don't overload our system
    throttler = AsyncLimiter(max_rate=1, time_period=14)

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