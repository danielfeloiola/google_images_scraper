#! /usr/bin/env python3

# ------------------------------------------------------------------------------
# Simple script for scraping images from Google Images
# Edit configuration variables below according to instructions and examples
#
# Based on a similar script from André Mintz (2019)
#
# Daniel Loiola, 2020
# ------------------------------------------------------------------------------

import csv
import hashlib
import os
import requests
import sys
import time
from bs4 import BeautifulSoup

# ------------------------------------------------------------------------------
# CONFIGURATION VARIABLES
# ------------------------------------------------------------------------------

# Query term (can be overriden by command line parameters)
query = "puppy"

# Total number of images to download
max_images = 50

# ------------------------------------------------------------------------------

# optional: allows the query to be passed as argument
if len(sys.argv) > 1:
    query = sys.argv[1]

output_folder = ""
output_csv = ""

# ------------------------------------------------------------------------------

def main():
    """
    Main:
    - Verifica e cria uma pasta com o nome da query
    - Cria um arquivo CSV
    - Escreve o cabecalho no csv
    - Chama a scrape_stock para iniciar a raspagem
    """
    global output_csv
    global output_folder

    # If query container directory does not exist, create it
    output_folder = query

    # Warns if there is already a file about to be overwritten
    if not os.path.isdir(output_folder):
        os.makedirs(output_folder)

    # Set folder and filename
    output_csv_fn = query + "_image_list.csv"
    output_csv_fp = os.path.join(output_folder, output_csv_fn)

    # Create CSV file
    if not os.path.isfile(output_csv_fp):
        output_csv_f = open(output_csv_fp, 'w', encoding="utf-8")
        output_csv_fields = ["rank_pos", "image_url",
                             "image_info_url",
                             "download_file"]
        output_csv = csv.DictWriter(output_csv_f, fieldnames=output_csv_fields)
        output_csv.writeheader()
    else:
        print("Output CSV file already exists. Rename it or delete it first.")
        sys.exit()

    # Start scraper process...
    scrape_stock(query)

    # Warns when fineshed
    print("\nFinished.")

# ------------------------------------------------------------------------------

def scrape_stock(term):
    """
    Scrape:
    - Cria a pasta para o site de imagens
    - Faz o request
    - Faz um call para o scrape_images para pegar a lista de imagens
    - Coloca a informação de cada imagem no csv
    - faz o download da imagem
    """
    global output_csv

    # Get query URL
    url = query_url(term)

    # Create stocksite folder
    folderp = os.path.join(output_folder)
    if not os.path.exists(folderp):
        os.makedirs(folderp)

    # Keep track of processed images and pagination of the stock site
    num_images = 0
    cur_page = 1

    # Loop through the stocksite pages until finished
    while num_images < max_images:

        # Download page
        try:
            r = requests.get(url, allow_redirects=True, timeout=100)

        # In case of error, try 5 more times and if persistent, move on.
        except Exception:
            success = False
            for i in range(5):
                print("\nConnection problem. Sleeping to try again.")
                time.sleep(5)
                try:
                    r = requests.get(url, allow_redirects=True, timeout=100)
                    success = True
                    break
                except Exception:
                    pass
            if not success:
                print("\nUnresolved connection problem. Moving on")
                print("** Next page **", end=" ")
                sys.stdout.flush()
                url = scrape_next_link(soup, url, cur_page)
                cur_page += 1
                continue

        # Parse with BeautifulSoup
        page = r.content
        soup = BeautifulSoup(page, "html.parser")

        # Get an image list from the page
        image_list = scrape_images(soup)

        # For each imag
        for image in image_list:
            num_images += 1
            print(num_images, end=" ")
            sys.stdout.flush()

            # Set image metadata
            image_url = image['image_url']
            image_info_url = image['image_info_url']

            # Get hash of url, form image file path
            hash_url = hashlib.sha1(image_url.encode('utf-8')).hexdigest()
            image_fn = hash_url + '.jpg'
            image_fp = os.path.join(folderp, image_fn)

            # Create CSV row
            row = {"rank_pos": num_images,
                   "image_url": image_url,
                   "image_info_url": image_info_url,
                   "download_file":image_fp}
            output_csv.writerow(row)

            # If image has not been downloaded yet, download it
            if not os.path.isfile(image_fp):
                r = requests.get(image_url,allow_redirects=True,timeout=100)

                if len(r.content) > 0:
                    image_f = open(image_fp, "wb").write(r.content)
                else:
                    print("[/]", end=" ")
                    sys.stdout.flush()

        # After downloading all images in page, move on to the next
        print("** Next page **", end=" ")
        sys.stdout.flush()

        # Scrape next page's url
        url = scrape_next_link(soup, url, cur_page)
        cur_page += 1

# ------------------------------------------------------------------------------

def scrape_images(page):
    """
    Scraper:
    - Extrai a URL e as informações das imagens
    - Coloca os dados em uma lista
    (lista: image_list -> dict: image -> keys: 'image_url' e  'image_info_url')
    - Retorna a lista
    """

    # Get each element containig a search result
    elements = page.find_all("div", attrs={"class": "lIMUZd"})

    # Get image urls and image information page url from each element
    images_list = []

    for element in elements:

        # get img url and page result url
        image_url = element.img['src']
        image_info_url = element.a["href"][7:]

        # remove URL variables
        sep = '&sa=U&ved=2'
        stripped = image_info_url.split(sep, 1)[0]
        image_info_url = stripped

        # DEBUG
        #print(image_url)
        #print(image_info_url)

        image = {
            'image_url': image_url,
            'image_info_url': image_info_url
        }
        images_list.append(image)

    return images_list


def query_url(term):
    """URL para o site"""
    url_opening = "https://www.google.com/search?q="
    url_ending = "&source=lnms&tbm=isch&sa=X&ved=2ahUKEwie6f-DgLPsAhX0KLkGHd8HAvgQ_AUoA3oECBQQBQ&biw=1280&bih=726"
    url = url_opening + term + url_ending

    #print(url)
    return url

def scrape_next_link(page, url, pagination_index):
    """Encontrar a próxima página"""

    next_url = "https://www.google.com" + page.find("a", attrs={"class": "frGj1b"})['href']
    print("\n" + next_url)
    return next_url



if __name__ == "__main__":
    main()
