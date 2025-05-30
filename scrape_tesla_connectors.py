import requests
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT_URL = "https://service.tesla.com"

# Set this to None to scrape all connectors, or to an integer for testing
CONNECTOR_LIMIT = None  # Set to None for no limit

PROG_DETAILS_LISR_3 = [
    {
        "model": "Model3",
        "prog_id": "prog-233",
        "sop": "SOP8",
        "build_information": [
            "Shanghai: 2023-09-01 - Present",
            "Fremont: 2024-01-01 - Present"
        ]
    },
    {
        "model": "Model3",
        "prog_id": "prog-187",
        "sop": "SOP7",
        "build_information": [
            "Fremont: 2022-01-17 - 2023-12-31",
            "Shanghai: 2021-11-12 - 2023-08-31"
        ]
    },
    {
        "model": "Model3",
        "prog_id": "prog-219",
        "sop": "SOP6",
        "build_information": [
            "Shanghai: 2021-06-16 - 2021-11-11"
        ]
    },
    {
        "model": "Model3",
        "prog_id": "prog-56",
        "sop": "SOP5",
        "build_information": [
            "Fremont: 2020-10-05 - 2022-01-16",
            "Shanghai: 2020-12-28 - 2021-06-15"
        ]
    },
    {
        "model": "Model3",
        "prog_id": "prog-20",
        "sop": "SOP4",
        "build_information": [
            "Fremont: 2019-06-05 - 2020-10-04",
            "Shanghai: 2019-10-18 - 2020-12-27"
        ]
    },
    {
        "model": "Model3",
        "prog_id": "prog-220",
        "sop": "SOP3",
        "build_information": [
            "Fremont: 2019-01-05 - 2019-06-04"
        ]
    },
    {
        "model": "Model3",
        "prog_id": "prog-18",
        "sop": "SOP2",
        "build_information": [
            "Fremont: 2018-07-11 - 2019-01-04"
        ]
    },
    {
        "model": "Model3",
        "prog_id": "prog-13",
        "sop": "SOP1",
        "build_information": [
            "Fremont: 2017-07-01 - 2018-07-10"
        ]
    }
]

PROG_DETAILS_LIST_Y = [
    {
        "model": "ModelY",
        "prog_id": "prog-217",
        "sop": "SOP7",
        "build_information": [
            "Shanghai: 2025-02-17 - Present",
            "Berlin: 2025-02-17 - Present",
            "Austin: 2025-02-24 - Present",
            "Fremont: 2025-02-24 - Present"
        ]
    },
    {
        "model": "ModelY",
        "prog_id": "prog-202",
        "sop": "SOP6",
        "build_information": [
            "Structural Pack Vehicles",
            "Austin: 2023-06-04 - 2025-02-23",
            "Berlin: 2024-04-01 - 2025-02-16"
        ]
    },
    {
        "model": "ModelY",
        "prog_id": "prog-201",
        "sop": "SOP5",
        "build_information": [
            "Non-Structural Pack Vehicles",
            "Fremont: 2023-05-23 - 2025-02-23",
            "Austin: 2023-06-02 - 2025-02-23",
            "Berlin: 2024-05-07 - 2025-02-16",
            "Shanghai: 2024-02-15 - 2025-02-16"
        ]
    },
    {
        "model": "ModelY",
        "prog_id": "prog-196",
        "sop": "SOP4",
        "build_information": [
            "Structural Pack Vehicles",
            "Austin: 2022-03-28 - 2023-06-03",
            "Berlin: 2023-04-03 - 2024-03-31"
        ]
    },
    {
        "model": "ModelY",
        "prog_id": "prog-188",
        "sop": "SOP3",
        "build_information": [
            "Non-Structural Pack Vehicles",
            "Fremont: 2022-01-06 - 2023-05-22",
            "Berlin: 2022-01-06 - 2024-05-06",
            "Shanghai: 2021-11-15 - 2024-02-14",
            "Austin: 2022-06-13 - 2023-06-01"
        ]
    },
    {
        "model": "ModelY",
        "prog_id": "prog-63",
        "sop": "SOP2",
        "build_information": [
            "Fremont: 2021-01-13 - 2022-01-06",
            "Shanghai: 2020-12-14 - 2021-11-15",
            "Berlin: 2021-01-13 - 2022-01-06"
        ]
    },
    {
        "model": "ModelY",
        "prog_id": "prog-52",
        "sop": "SOP1",
        "build_information": [
            "Fremont: 2020-01-09 - 2021-01-12"
        ]
    }
]

#PROG_DETAILS_LIST = PROG_DETAILS_LISR_3 + PROG_DETAILS_LIST_Y
PROG_DETAILS_LIST = PROG_DETAILS_LIST_Y

headers = {
    "User-Agent": "curl/8.7.1",
    "Accept": "*/*"
}

def get_soup(url):
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")

def get_connector_links(main_url):
    soup = get_soup(main_url)
    # Find the sidebar navigation
    aside = soup.find("aside", class_="tds-layout-item tds-layout-aside")
    if not aside:
        raise Exception("Sidebar <aside> not found.")
    nav = aside.find("nav", class_="tds-sidenav")
    if not nav:
        raise Exception("Sidebar <nav> not found.")
    links = nav.find_all("a", class_="tds-site-nav-item", href=True)
    connector_links = []
    for link in links:
        href = link['href']
        # Join relative URLs to the current page's URL
        full_url = urljoin(main_url, href)
        connector_links.append(full_url)
    return connector_links

def parse_connector_page(url):
    soup = get_soup(url)
    data = {"url": url}
    # Extract connector name from the main content section
    main_section = soup.find("section", class_="tds-layout-item tds-layout-main")
    if main_section:
        name_tag = main_section.find("h1")
        data["name"] = name_tag.get_text(strip=True) if name_tag else None
    else:
        data["name"] = None

    # Extract connector meta fields
    data["tesla_part_number"] = None
    data["connector"] = None
    data["color"] = None
    meta = soup.find("div", class_="connector-meta")
    if meta:
        for wrapper in meta.find_all("div", class_="wrapper"):
            label = wrapper.find("div", class_="label")
            value = wrapper.find("div", class_="value")
            if not label or not value:
                continue
            label_text = label.get_text(strip=True).lower()
            value_text = value.get_text(strip=True)
            if "part number" in label_text:
                data["tesla_part_number"] = value_text if value_text else None
            elif label_text == "connector":
                data["connector"] = value_text if value_text else None
            elif label_text == "color":
                data["color"] = value_text if value_text else None

    # Extract description from figcaptions in connector-images
    description_parts = []
    images_section = soup.find("div", class_="connector-images")
    if images_section:
        for figcaption in images_section.find_all("figcaption"):
            description_parts.append(figcaption.get_text(" ", strip=True))
    data["description"] = " ".join(description_parts) if description_parts else None

    # Extract pinout table (if present)
    table = soup.find("table")
    if table:
        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        rows = []
        for tr in table.find_all("tr")[1:]:
            tds = tr.find_all("td")
            if len(tds) == 2 and tds[1].has_attr("colspan") and "unused" in tds[1].get_text(strip=True).lower():
                # Unused row
                row = {headers[0]: tds[0].get_text(strip=True)}
                for h in headers[1:]:
                    row[h] = "unused"
                rows.append(row)
            else:
                cells = [td.get_text(strip=True) for td in tds]
                if cells:
                    row = dict(zip(headers, cells))
                    # Ensure all headers are present
                    for h in headers:
                        if h not in row:
                            row[h] = None
                    rows.append(row)
        data["pinout_table"] = rows
    else:
        data["pinout_table"] = None
    # Extract image URLs, only include valid image extensions
    valid_exts = ('.jpg', '.jpeg', '.png', '.svg', '.gif', '.bmp', '.webp')
    images = soup.find_all("img")
    img_urls = [urljoin(url, img['src']) for img in images if img.get('src') and urljoin(url, img['src']).lower().endswith(valid_exts)]
    data["image_urls"] = img_urls
    return data

def main():
    for prog_info in PROG_DETAILS_LIST:
        model_name = prog_info["model"]
        current_prog_id = prog_info["prog_id"]
        sop_info = prog_info["sop"]
        build_info = prog_info["build_information"]

        print(f"\n--- Processing {model_name} {current_prog_id} ({sop_info}) ---")
        base_url_for_prog = f"https://service.tesla.com/docs/{model_name}/ElectricalReference/{current_prog_id}/connector/g011/index.html"

        print(f"Fetching connector links for {model_name} {current_prog_id} from {base_url_for_prog}...")
        try:
            connector_links = get_connector_links(base_url_for_prog)
        except requests.exceptions.RequestException as e:
            print(f"HTTP Error fetching links for {current_prog_id}: {e}. Skipping this PROG.")
            continue
        except Exception as e:
            print(f"Generic error fetching links for {current_prog_id}: {e}. Skipping this PROG.")
            continue
        
        if not connector_links:
            print(f"No connector links found for {current_prog_id}. Skipping.")
            continue

        if CONNECTOR_LIMIT is not None:
            print(f"Limiting to {CONNECTOR_LIMIT} connectors for {current_prog_id}.")
            connector_links = connector_links[:CONNECTOR_LIMIT]
        
        print(f"Found {len(connector_links)} connectors for {current_prog_id}.")

        scraped_connectors_data = [] # Initialize list for current_prog's connector data
        max_workers = 8  # Adjust based on your CPU/network

        def scrape(url_to_scrape):
            try:
                return parse_connector_page(url_to_scrape)
            except Exception as e:
                # Pass current_prog_id to the logging message
                print(f"Failed to scrape {url_to_scrape} for {current_prog_id}: {e}")
                return None

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            if not connector_links:
                print(f"No links to scrape for {current_prog_id}.")
                continue

            future_to_url = {executor.submit(scrape, link_url): link_url for link_url in connector_links}
            for i, future in enumerate(as_completed(future_to_url), 1):
                processed_url = future_to_url[future]
                data = future.result()
                if data:
                    scraped_connectors_data.append(data)
                
                connector_name_for_log = "Unknown"
                if data and data.get('name'):
                    connector_name_for_log = data['name']
                elif processed_url:
                    path_parts = [part for part in processed_url.split('/') if part]
                    if len(path_parts) >= 2 and path_parts[-1].lower() == "index.html":
                        connector_name_for_log = path_parts[-2]
                    elif path_parts:
                         connector_name_for_log = path_parts[-1]
                print(f"Scraped {i}/{len(connector_links)} for {current_prog_id}: {connector_name_for_log} ({processed_url})")
        
        if not scraped_connectors_data:
            print(f"No data successfully scraped for {current_prog_id}. Skipping file save.")
            continue

        # Prepare the final JSON structure
        output_data = {
            "model": model_name,
            "prog_id": current_prog_id,
            "sop": sop_info,
            "build_information": build_info,
            "connectors": scraped_connectors_data
        }

        output_filename = f"connectors/connectors_{model_name}_{current_prog_id}.json"
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"Saved data for {model_name} {current_prog_id} to {output_filename}")

if __name__ == "__main__":
    main()
