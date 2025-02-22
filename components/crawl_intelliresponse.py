import requests
from bs4 import BeautifulSoup 

class IntelliresponseCrawler(): 
    def __init__(self):
        self.cookies = {
            'JSESSIONID': 'B0A1DC27977CAB5152680C6C753E0DD6.umanitobaA1',
        }

        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://umanitoba.intelliresponse.com',
            'Referer': 'https://umanitoba.intelliresponse.com/index.jsp',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0',
            'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="132", "Microsoft Edge";v="132"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }

    def getResponse(self, promt: str) -> str:
        data = {
            'interfaceID': '6',
            'sessionId': '214565d5-eea7-11ef-9225-c380bee6b00c',
            'id': '-1',
            'requestType': '',
            'source': '1',
            'question': promt,
            'NormalRequest': 'Submit',
        }
        response = requests.post('https://umanitoba.intelliresponse.com/index.jsp', cookies=self.cookies, headers=self.headers, data=data)

        # print(response.text)

        soup = BeautifulSoup(response.content, 'html.parser')

        div_id = 'irResponse'
        divs = soup.find_all('div', id=div_id)

        text = ""

        if divs:
            for div in divs:
                text += div.get_text(strip=True) + "\n" # Get the text, stripping leading/trailing whitespace

        return text

        # print(text)
