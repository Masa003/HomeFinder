import requests
import re
import json

urlPages = "https://www.boligsiden.dk/kommune/broendby,roedovre,hvidovre,vallensbaek,ishoej,greve,solroed,herlev,ballerup,albertslund,glostrup,koebenhavn/tilsalg/villa?sortAscending=false&priceMin=1400000&priceMax=5500000&areaMin=100&sortBy=perAreaPrice&page={page}"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def extract_addresses(html_content):
    scripts = re.findall(r'<script>(.*?)</script>', html_content, re.DOTALL)

    print(f"✅ Found {len(scripts)} script blocks in the HTML content")

    if len(scripts) < 24:
        print("❌ Unable to find the expected script block in the HTML content.")
        return []

    house_number_script = scripts[21].replace('\', \'', '').replace('\\', '')
    print(house_number_script)

    road_names = re.findall(r'"road":\{"municipalityCode":\d+,"name":"(.*?)"', house_number_script)
    house_numbers = re.findall(r'"houseNumber":"(\d+[A-Za-z]*)"', house_number_script)
    zip_name_and_code = re.findall(r'"zip":\{"name":"(.*?)","slug":"","zipCode":(\d+)\}', house_number_script)
    housing_areas = re.findall(r'"housingArea":(\d+)', house_number_script)
    prices_cash = re.findall(r'"priceCash":(\d+)', house_number_script)
    per_area_prices = re.findall(r'"perAreaPrice":(\d+)', house_number_script)
    lot_areas = re.findall(r'"lotArea":(\d+)', house_number_script)

    print(f"✅ Extracted counts -> Roads: {len(road_names)}, House Numbers: {len(house_numbers)}, Zip Codes: {len(zip_name_and_code)}, Housing Areas: {len(housing_areas)}")

    if not (len(road_names) == len(house_numbers) == len(housing_areas)):
        print("❌ Mismatch in extracted data lengths")
        return []

    return [
        {
            "address": f"{road} {number}",
            "city": zip_name,
            "zipCode": zip_code,
            "housingArea": int(area),
            "lotArea": int(lot_area),
            "cashPrice": int(price_cash),
            "perAreaPrice": int(per_area_price),
        }
        for (road, number), (zip_name, zip_code), area, lot_area, price_cash, per_area_price in zip(zip(road_names, house_numbers), zip_name_and_code, housing_areas, lot_areas, prices_cash, per_area_prices)
    ]

all_addresses = []

for page in range(1, 6):
    url = urlPages.format(page=page)
    print(f"📡 Fetching data from: {url}")
    
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        addresses = extract_addresses(response.text)
        if addresses:
            all_addresses.extend(addresses)
            print(f"✅ Page {page} processed successfully with {len(addresses)} addresses.")
        else:
            print(f"⚠️ No addresses found on page {page}")
    else:
        print(f"❌ Failed to retrieve page {page}. Status code: {response.status_code}")

# Save all addresses to a JSON file
if all_addresses:
    with open("updated_addresses.json", "w", encoding="utf-8") as file:
        json.dump(all_addresses, file, indent=4, ensure_ascii=False)
    print(f"✅ Successfully saved {len(all_addresses)} addresses to updated_addresses.json")
else:
    print("❌ No addresses were collected.")
