from PIL import Image
from datetime import datetime

class MakePoster:
    def __init__(self, poster_id):
        self.poster_id = poster_id

        self.map_route = f'../app/static/map_pngs/{poster_id}.png'
        self.map_image = Image.open(self.map_route)

        self.poster = Image.new("RGB",(6000, 6000),color="#AA1452")
        self.poster.paste(self.map_image,mask=self.map_image)

        self.poster.show()



poster_id = 1


mp = MakePoster(1)
