import argparse
import os
import requests
from bs4 import BeautifulSoup
import pandas as pd


def extract_table_from_html(html_content):
    # Parse the HTML content
    soup = BeautifulSoup(html_content, "html.parser")
    # Extract the table data
    table_data = []
    # Find all sections with transfer bonuses
    sections = soup.find_all(
        "div", class_="w-layout-blockcontainer container-51 w-container"
    )
    for section in sections:
        # Extract the bank name
        bank_name = section.find("div", class_="text-block-18").get_text(strip=True)
        # Find all list items in the section
        items = section.find_all("div", role="listitem")
        # Extract data from each list item
        for item in items:
            airline = item.find("div", class_="text-block-22").get_text(strip=True)
            transfer_bonus = item.find("div", class_="text-block-23").get_text(
                strip=True
            )
            expiration = item.find("div", class_="text-block-24").get_text(strip=True)
            table_data.append(
                {
                    "Bank": bank_name,
                    "Airline": airline,
                    "Transfer Bonus": float(transfer_bonus.rstrip("%")) / 100 + 1,
                    "Expiration": expiration,
                }
            )
    # Create a pandas DataFrame
    df = pd.DataFrame(table_data).set_index("Expiration")
    df.index = pd.to_datetime(df.index, errors="coerce")
    return df


def main(url):
    response = requests.get(url)
    response.raise_for_status()
    html_content = response.text
    df = extract_table_from_html(html_content)
    df.to_csv("bonuses.csv")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch transfer bonuses and save to CSV."
    )
    parser.add_argument("--url", type=str, help="URL to fetch the data from")
    args = parser.parse_args()
    main(args.url)
