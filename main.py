import json
import os
import csv
import pathlib
import string
import sys
import argparse
import bs4
# This is a sample Python script.

# Press Maiusc+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import requests

cardmarket_price_parser = argparse.ArgumentParser(description="Parse your CSV with MTG cards to retrieve their cardmarket price")
cardmarket_price_parser.add_argument('path',
                                     metavar='path',
                                     type=str,
                                     help='the path to CSV file')
cardmarket_price_parser.add_argument('-s',
                                     '--save',
                                     metavar='save_to',
                                     type=str,
                                     help='the path to save new generated CSV file with cardmarket prices',
                                     required=False)

cardmarket_price_parser.add_argument('--name-col',
                                     action='store',
                                     type=int,
                                     required=True)
cardmarket_price_parser.add_argument('--num-col',
                                     action='store',
                                     type=int,
                                     required=True)
cardmarket_price_parser.add_argument('--expansion-col',
                                     action='store',
                                     type=int,
                                     required=True)
cardmarket_price_parser.add_argument('--starting-row',
                                     action='store',
                                     type=int,
                                     default=1)
cardmarket_price_parser.add_argument('--separator',
                                     action='store',
                                     type=str,
                                     default=',')
cardmarket_price_parser.add_argument('--overwrite',
                                     action='store_true')
cardmarket_price_parser.add_argument('--no-header',
                                     action='store_true')
cardmarket_price_parser.add_argument('--use-decimals-dot',
                                     action='store_true')
cardmarket_price_parser.add_argument('-a',
                                     '--append',
                                     action='store_true')

# Retrieve CLI arguments
args = cardmarket_price_parser.parse_args()


def check_file_exists(path):
    return os.path.isfile(path)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print(args)
    if not check_file_exists(args.path):
        exit(2)
    cardmarket_expansions_id_file = open('cardmarket_expansions_id.json', 'r')
    cardmarket_expansions_id = json.load(cardmarket_expansions_id_file)
    cardmarket_expansions_id_file.close()
    with open(args.path, mode='r+', newline='') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=args.separator)
        row_to_skip = args.starting_row
        header = []
        if not args.no_header:
            row = next(csv_reader)
            header = row
            header.append('CardMarket Price')
        while row_to_skip > 0:
            next(csv_reader)
            row_to_skip -= 1
        save_file = csv_file
        if not args.overwrite:
            if args.save:
                new_file_path = args.save
            else:
                csv_file_path = pathlib.PurePath(csv_file.name)
                new_file_path = csv_file_path.name
                suffixes_length = 0
                for suffix in csv_file_path.suffixes:
                    suffixes_length += len(suffix)
                if suffixes_length:
                    new_file_path = new_file_path[:-suffixes_length] + '_cardmarket' + new_file_path[-suffixes_length:]
                else:
                    new_file_path += '_cardmarket'
            save_file = open(new_file_path, 'a' if args.append else 'w', newline='', encoding='UTF8')
        csv_writer = csv.writer(save_file, delimiter=args.separator)
        if not args.append and not args.overwrite and not args.no_header:
            csv_writer.writerow(header)
        saved_rows = 0
        for row in csv_reader:
            print(row)
            expansion = row[args.expansion_col].translate(str.maketrans('', '', string.punctuation))
            card_name = row[args.name_col].translate(str.maketrans('', '', string.punctuation))
            search_params = {
                'idCategory': '0',
                'idExpansion': cardmarket_expansions_id[expansion],
                'searchString': '{}'.format(row[args.name_col]),
                'sortBy': 'collectorsnumber_desc',
            }
            print(search_params['searchString'])
            search_redirected = False
            response = requests.get("https://www.cardmarket.com/en/Magic/Products/Search", params=search_params, allow_redirects=False)
            if response.status_code >= 300 and response.status_code < 400:
                search_redirected = True
            if search_redirected:
                response = requests.get("https://www.cardmarket.com" + response.headers['Location'], params={'isPlayset': 'N'})
            soup = bs4.BeautifulSoup(response.text, 'lxml')
            print('Response History:', response.history)
            if not search_redirected:
                no_found_el = soup.find('div', string='Sorry, no matches for your query')
                if no_found_el:
                    print('NOT FOUND!')
                search_table = soup.select_one('div.table-body')
                card_number_cols = search_table.select('div.col-number > span:last-child')
                print(card_number_cols)
                card_number_col = None
                for el in card_number_cols:
                    if el.get_text() == row[args.num_col] or args.num_col == -1:
                        card_number_col = el
                        break
                response = requests.get("https://www.cardmarket.com" + el.parent.parent.find('a')['href'], params={'isPlayset': 'N'})
                soup = bs4.BeautifulSoup(response.text, 'lxml')
            card_number_select = soup.select_one('dl > .d-none.d-md-block')
            if card_number_select and not args.num_col != -1 and row[args.num_col]:
                print(card_number_select)
            if search_redirected:
                print('Redirect')
            print(soup)
            min_price = soup.select_one('.col-offer > .price-container').get_text()
            print('CardMarket Price:', min_price[-1:] + min_price[:-2])
            row.append(min_price[-1:] + min_price[:-2])
            if args.overwrite:
                pass
            else:
                csv_writer.writerow(row)
            saved_rows += 1
            if saved_rows % 10 == 0:
                save_file.flush()
                print("Flushing 10 rows!")
            print()
        if not args.overwrite:
            save_file.close()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
