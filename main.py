import requests
import sys
from bs4 import BeautifulSoup
import argparse
import csv

LICENCE_DIVISION_ADDR = "https://yokatlas.yok.gov.tr/lisans-bolum.php?b={}"
PROGRAMME_LAST_ADDR = "https://yokatlas.yok.gov.tr/{}/content/lisans-dynamic/1070.php?y={}"
PROGRAMME_MAIN_ADDR = "https://yokatlas.yok.gov.tr/{}/lisans.php?y={}"
PROGRAMME_ACCREDITATION_ADDR = "https://yokatlas.yok.gov.tr/{}/content/lightbox/akredite.php?y={}"

def get_programme_codes(general_prog_code):
    req = requests.get(LICENCE_DIVISION_ADDR.format(general_prog_code))
    if(req.status_code != 200):
        raise RuntimeError()

    soup = BeautifulSoup(req.content, "html.parser")
    output = []
    for panel in soup.find_all(attrs={'class': 'panel-title'})[:-1]:
        output.append((
            "https://yokatlas.yok.gov.tr/%s" % panel.a.get('href'), # programme addr
            int(panel.a.get('href').replace("lisans.php?y=", "")), # programme code
            panel.a.small.font.text[1:-1] # programme faculty
        ))

    return output

def get_programme_last(prog_code, year = ""):
    req = requests.get(PROGRAMME_LAST_ADDR.format(year, prog_code))
    if(req.status_code != 200):
        raise RuntimeError()

    soup = BeautifulSoup(req.content, "html.parser")

    return (
        soup.table.find_all("tr")[3].find_all("td")[1].text, # score
        soup.table.find_all("tr")[4].find_all("td")[1].text  # rank
    )

def get_programme_name(prog_code, year = ""):
    req = requests.get(PROGRAMME_MAIN_ADDR.format(year, prog_code))
    if(req.status_code != 200):
        raise RuntimeError()

    soup = BeautifulSoup(req.content, 'html.parser')

    prog_name = soup.find(attrs = {'class': 'panel panel-primary'}).h2.text.replace("\n", "").replace("\r","").replace("  ", "").replace("\t", "")
    return (
        soup.find(attrs={'class': 'panel-heading'}).h3.text.replace("\n", "").replace("\r","").replace("  ", "").replace("\t", ""),
        prog_name[prog_name.find('- ')+2:-1]
    )

def get_programme_accreditation(prog_code, year=""):
    req = requests.get(PROGRAMME_ACCREDITATION_ADDR.format(year, prog_code))
    if(req.status_code != 200):
        raise RuntimeError()

    if('MÜDEK'.encode("utf-8") in req.content):
        return 'mudek'
    elif(b'ABET' in req.content):
        return 'abet'
    else:
        return ''

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Scrape YOK Atlas.')
    parser.add_argument('programmecode', metavar='prog-code', type=int, nargs=1,
                        help='programme code from the addr https://yokatlas.yok.gov.tr/lisans-bolum.php?b={code here}')

    prog_code = parser.parse_args().programmecode[0]

    with open(f"{prog_code}.csv", "w", newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=';', quotechar='"')
        writer.writerow([
            'Ana Program Kodu',
            'Program Kodu',
            'Bölüm Adı',
            'Fakülte'
            'Üniversite',
            'İl',
            'Puan 2021',
            'Başarı Sırası 2021',
            'Puan 2020',
            'Başarı Sırası 2020',
            'Puan 2019'
            'Başarı Sırası 2019',
            'Akreditasyon',
            'Adres'
            ])

        for programme_info in get_programme_codes(prog_code):
            prog_name = get_programme_name(programme_info[1])

            writer.writerow([
                prog_code, # main programm code
                programme_info[1], # programme code
                prog_name[1], # Programme name
                programme_info[2],
                prog_name[0][:prog_name[0].find("(")], # University name
                prog_name[0][prog_name[0].find("(")+1:-1], # province
                *get_programme_last(programme_info[1]), # 2021 score and rank
                *get_programme_last(programme_info[1],2020), # 2020 score and rank
                *get_programme_last(programme_info[1],2019), # 2019 score and rank
                get_programme_accreditation(programme_info[1]), # accreditations
                programme_info[0] # http addr
            ])

            