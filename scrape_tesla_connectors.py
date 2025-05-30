import requests
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import urljoin

BASE_URL = "https://service.tesla.com/docs/Model3/ElectricalReference/prog-18/connector/g011/index.html"
ROOT_URL = "https://service.tesla.com"

# Set this to None to scrape all connectors, or to an integer for testing
CONNECTOR_LIMIT = None  # Set to None for no limit

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
    print("Fetching connector links...")
    try:
        connector_links = get_connector_links(BASE_URL)
    except Exception as e:
        print(f"Error: {e}")
        print("If the sidebar is loaded via JavaScript, use Selenium instead of requests.")
        return
    if CONNECTOR_LIMIT is not None:
        connector_links = connector_links[:CONNECTOR_LIMIT]
    print(f"Found {len(connector_links)} connectors.")
    all_data = []
    for i, url in enumerate(connector_links):
        print(f"Scraping {i+1}/{len(connector_links)}: {url}")
        try:
            data = parse_connector_page(url)
            all_data.append(data)
            time.sleep(0.5)  # Be polite
        except Exception as e:
            print(f"Failed to scrape {url}: {e}")
    with open("connectors.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    print("Saved to connectors.json")

if __name__ == "__main__":
    main() 