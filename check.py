import argparse
import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO

def get_span_table_pairs(html):
    soup = BeautifulSoup(html, "html.parser")
    spans = soup.find_all("span", id=lambda x: x and x.endswith("-transfer-partners"))
    tables = soup.find_all("table")
    span_table_pairs = []
    for span, table in zip(spans, tables):
        df = pd.read_html(StringIO(str(table)))[0]
        span_table_pairs.append((span.text.strip(), df))
    return span_table_pairs

def save_tables_to_csv(span_table_pairs, prefix="partners"):
    for name, df in span_table_pairs:
        safe_name = name.lower().replace(" ", "_").replace("/", "_")
        filename = f"{prefix}_{safe_name}.csv"
        df.to_csv(filename, index=False)
        print(f"Saved: {filename}")

def extract_table_from_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    table_data = []
    sections = soup.find_all("div", class_="w-layout-blockcontainer container-51 w-container")

    for section in sections:
        bank_name = section.find("div", class_="text-block-18").get_text(strip=True)
        items = section.find_all("div", role="listitem")

        for item in items:
            airline = item.find("div", class_="text-block-22").get_text(strip=True)
            transfer_bonus = item.find("div", class_="text-block-23").get_text(strip=True)
            expiration = item.find("div", class_="text-block-24").get_text(strip=True)
            table_data.append({
                "Bank": bank_name,
                "Airline": airline,
                "Transfer Bonus": float(transfer_bonus.rstrip("%")) / 100 + 1,
                "Expiration": expiration,
            })

    df = pd.DataFrame(table_data).set_index("Expiration")
    df.index = pd.to_datetime(df.index, errors="coerce")
    return df

def main(url_partners, url_bonuses):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        )
    }

    # Fetch and process partners data
    response_partners = requests.get(url_partners, headers=headers)
    response_partners.raise_for_status()
    html_partners = response_partners.text
    span_table_pairs = get_span_table_pairs(html_partners)
    save_tables_to_csv(span_table_pairs)

    # Fetch and process bonuses data
    response_bonuses = requests.get(url_bonuses, headers=headers)
    response_bonuses.raise_for_status()
    html_bonuses = response_bonuses.text
    df_bonuses = extract_table_from_html(html_bonuses)
    df_bonuses.to_csv("bonuses.csv")
    print("Saved: bonuses.csv")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch data and export to CSV files.")
    parser.add_argument(
        "--url-partners",
        type=str,
        required=True,
        help="URL to fetch the transfer partner data from"
    )
    parser.add_argument(
        "--url-bonuses",
        type=str,
        required=True,
        help="URL to fetch the transfer bonuses data from"
    )

    args = parser.parse_args()
    main(args.url_partners, args.url_bonuses)
