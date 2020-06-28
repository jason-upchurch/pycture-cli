import os
import sys
import re
import requests
from io import BytesIO
import pytesseract
import github3 as gh
from PIL import Image
from PIL import ImageEnhance
from PIL import UnidentifiedImageError
from requests import ConnectionError

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
GITHUB_USERNAME = os.environ.get('GITHUB_USERNAME', '')

if GITHUB_TOKEN and GITHUB_USERNAME:
    gh = gh.login(GITHUB_USERNAME, password=GITHUB_TOKEN)
    print('logged in!\n')
else:
    sys.exit('login failed\n')

def find_text(text, exclude=None):
    results = gh.search_issues("{} in:body,comments,code user:fecgov".format(text))
    flagged_issues = {'body': [], 'comments': []}
    for result in results:
        if result.comments:
            for comment in result.issue.comments():
                if re.findall(text.lower(), comment.body.lower()):
                    if result.issue.html_url not in flagged_issues['comments']:
                        flagged_issues['comments'].append(result.issue.html_url)
        if re.findall(text.lower(), result.body.lower()):
            if result.issue.html_url not in flagged_issues['body']:
                flagged_issues['body'].append(result.issue.html_url)
        print('\nflagged_issues so far...\n')
        print(flagged_issues, '\n')


    
