import argparse
import json
import os
import requests
from bs4 import BeautifulSoup
import cssutils

def extract_inline_styles(soup):
    """Extracts inline CSS styles from the given BeautifulSoup object."""
    styles = []
    style_tags = soup.find_all('style')
    for style in style_tags:
        styles.append(style.get_text())
    return styles

def extract_external_styles(soup, base_url):
    """Extracts external CSS styles from the given BeautifulSoup object and base URL."""
    styles = []
    link_tags = soup.find_all('link', rel='stylesheet')
    for link in link_tags:
        href = link.get('href')
        if href:
            if href.startswith('http') or href.startswith('//'):
                style_url = href
            else:
                style_url = base_url + href
            response = requests.get(style_url)
            if response.status_code == 200:
                styles.append(response.text)
    return styles

def create_style_report(inline_styles, external_styles):
    """Creates a dictionary structure containing extracted inline and external styles."""
    report = {
        "Inline Styles": inline_styles,
        "External Styles": external_styles
    }
    return report

def save_styles_to_file(styles, filename):
    """Saves extracted CSS styles to the specified file (optional)."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    if filename:
        with open(filename, 'w') as f:
            for style in styles:
                f.write(style.strip() + '\n')  # Add newline between styles
        print(f"Styles saved to: {filename}")

def main(url, output_dir="scraped_styles", output_format="report"):
    """Fetches the webpage content, extracts CSS styles, and generates a report or saves to file."""
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve the URL: {url}")
        return

    soup = BeautifulSoup(response.content, 'html.parser')
    base_url = '{uri.scheme}://{uri.netloc}/'.format(uri=requests.utils.urlparse(url))

    # Extract styles
    inline_styles = extract_inline_styles(soup)
    external_styles = extract_external_styles(soup, base_url)

    # Create style report
    report = create_style_report(inline_styles, external_styles)

    # Choose output format
    if output_format == "report":
        # Print report directly
        print("Scraped CSS Styles Report:")
        for section, styles in report.items():
            print(f"\n{section}:")
            for style in styles:
                print(style)
    elif output_format == "file":
        # Save to separate files (uncomment and adjust output_dir if needed)
        inline_filename = os.path.join(output_dir, "inline_styles.css")
        save_styles_to_file(inline_styles, inline_filename)
        #
        for i, style in enumerate(external_styles):
            external_filename = os.path.join(output_dir, f"external_style_{i + 1}.css")
            save_styles_to_file([style], external_filename)  # Fix the function call
        print("Choose 'file' output format with appropriate output_dir for separate file saving.")
    elif output_format == "json":
        # Save report as JSON (uncomment and choose a filename)
        report_json = json.dumps(report, indent=4)  # Formatted JSON output
        with open("scraped_styles.json", 'w') as f:  # Adjust filename
            f.write(report_json)
        print("Choose 'json' output format with appropriate filename for JSON saving.")
    else:
        print(f"Invalid output format: {output_format}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Web scrape CSS styles from a given URL.")
    parser.add_argument('url', type=str, help="The URL of the webpage to scrape.")
    parser.add_argument('--output_dir', type=str, default="scraped_styles",
                        help="Path to the output directory (default: scraped_styles).")
    parser.add_argument('--output_format', type=str, default="report", choices=["report", "file", "json"],
                        help="Output format (default: report). Choose from 'report', 'file', or 'json'.")
    args = parser.parse_args()
    main(args.url, args.output_dir, args.output_format)

# how to use it: python css_scapper.py "https://www.example.com" --output_dir --output_format  