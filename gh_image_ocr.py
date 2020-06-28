import os
import sys
import argparse
import re
import requests
from io import BytesIO
import pytesseract
import github3 as gh
from PIL import Image
from PIL import ImageEnhance
from PIL import UnidentifiedImageError
from requests import ConnectionError
import pandas as pd

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
GITHUB_USERNAME = os.environ.get('GITHUB_USERNAME', '')

parser = argparse.ArgumentParser(
    description='Program to traverse GitHub repo under "user"\n' +\
    'and review occurences of indicated keywords (currently one keyword ' +\
    'at a time')
parser.add_argument('--ext', metavar='.<ext>', type=str,
                    help='file extension to be searched for (include the ".")',
                    default='.png')
parser.add_argument('--user', metavar='GitHub user', type=str,
                    default=GITHUB_USERNAME)
parser.add_argument('--save', metavar='path to save', type=str, default='',
                    help='path for saving output to csv')
parser.add_argument('keyword', metavar='keyword', type=str)
args = parser.parse_args()

if GITHUB_TOKEN and GITHUB_USERNAME:
    gh = gh.login(GITHUB_USERNAME, password=GITHUB_TOKEN)
    print('logged into GitHub, and beginning review ',
          'of {} for file type {} for user: {}'.format(args.keyword,args.ext,args.user))
else:
    sys.exit('login to GitHub failed, please verify credentials are\n',
             'stored as environmental variables, i.e.,\n',
             '"echo $GITHUB_TOKEN" and "echo $GITHUB_USERNAME"\n',
             'show non-null values')

i = 0
flagged = {}
skipped = {}
skipped_flag = False
results = gh.search_issues("{} in:body,comments user:{}".format(args.ext,args.user))
for result in results:
    if args.ext in result.body or any(args.ext in r.body for r in result.issue.comments()):
        matches = re.findall(r'http[^\s]+'+args.ext, result.body)
        if result.comments:
            for r in result.issue.comments():
                more_matches = re.findall(r'http[^\s\(\)\[\]]+'+args.ext, r.body)
                matches.extend(more_matches)
        for match in matches:
            print('Performing OCR on image ', match.strip())
            try:
                response = requests.get(match.strip())
                img = Image.open(BytesIO(response.content))
                img = img.resize((img.width*3, img.height*3))
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(5)
                text = pytesseract.image_to_string(img).lower()
                if (args.keyword.lower() in text or "api key" in text):
                    i+=1
                    print('\n', i, ' possible secret found: ', match.strip(), '\n')
                    if result.issue.html_url in flagged.keys():
                        flagged[result.issue.html_url].append(match.strip())
                    else:
                        flagged[result.issue.html_url] = [match.strip()]
            except UnidentifiedImageError as e:
                print('\n', 'UnidentifiedImageError for', match, ', skipping...\n')
                skipped_flag = True
                continue
            except ValueError as e:
                print('\n', 'ValueError for ', match, ', skipping...\n')
                skipped_flag = True
                continue
            except ConnectionError as e:
                print('\n', 'ConnectionError for ', match, ', skipping\n')
                skipped_flag = True
                continue
            if skipped_flag:
                if result.issue.html_url in skipped.keys():
                    skipped[result.issue.html_url].append(match.strip())
                else:
                    skipped[result.issue.html_url] = [match.strip()]
                skipped_flag = False
if args.save:
    dff = pd.DataFrame.from_dict(flagged)
    dff.to_csv(args.save+'/flagged.csv')
    dfs = pd.DataFrame.from_dict(skipped)
    dfs.to_csv(args.save+'/skipped.csv')

