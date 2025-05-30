import requests
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import urljoin

BASE_URL = "https://service.tesla.com/docs/Model3/ElectricalReference/prog-18/connector/g011/index.html"
ROOT_URL = "https://service.tesla.com"

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
    # Extract connector name (usually in <h1> or <h2>)
    title = soup.find(["h1", "h2"])
    data["name"] = title.get_text(strip=True) if title else None
    # Extract description (first <p> or summary block)
    desc = soup.find("p")
    data["description"] = desc.get_text(strip=True) if desc else None
    # Extract pinout table (if present)
    table = soup.find("table")
    if table:
        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        rows = []
        for tr in table.find_all("tr")[1:]:
            cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
            if cells:
                rows.append(dict(zip(headers, cells)))
        data["pinout_table"] = rows
    else:
        data["pinout_table"] = None
    # Extract image URLs
    images = soup.find_all("img")
    img_urls = [urljoin(ROOT_URL, img['src']) for img in images if img.get('src')]
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