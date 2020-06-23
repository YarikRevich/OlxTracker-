from bs4 import BeautifulSoup
import requests
import re


class Parcer:


    def __init__(self,url):
        if requests.get(url):
            self.url = url
            self.set_data()
        

    def set_data(self):
        html = requests.get(self.url)
        soup = BeautifulSoup(html.text,"html.parser")
        tbody = soup.find("p",class_="color-2")
        result = tbody.get_text()
        ads = re.findall(r"[0-9]{0,10000}",result)
        self.result = "".join(ads)
    
    

    def get_data(self):
        return self.result
       

parcer = Parcer(r"https://www.olx.ua/uk/transport/moto/")
