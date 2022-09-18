from flask import Flask, jsonify, request
from flask_restful import Resource, Api, reqparse
import pandas as pd
import ast
from sqlalchemy import create_engine
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
api = Api(app)


class Engine():
    cookies = {
        "domain": "i=KxuhgWWkl2Ycy/peYda/u0GVOEsLAnw209yLiz5QizXbTWu3r+195UrK7b1Zt+ha+EShQbbdpQSLQt3qwPjVpm/1hr8=; mda_exp_enabled=1; yandex_login=; yandexuid=9204112301647799500; mda2_beacon=1652595426732; _ym_uid=1628237438951307249; _ym_d=1652595427; my_perpages=%7B%2279votes%22%3A200%7D; gdpr=0; location=1; crookie=UuXwG3ldzvUiN/s6cW6JD5nYmJ00hKcdo6GgCBMGiU4mjE6ztZbSCyBqbmZ3063xJxzlftJuY474sO11Z6ACQrtmbb0=; _yasc=/4S7cOoVHore3L2iwW9+JGTzfBRJpgg2I4shvw0/iO4Jpdxr; result_type=full; spravka=dD0xNjUyNTYxNDQ2O2k9MzEuMTczLjg3Lj99ec3f4be11f335dcdebefb68e43f24777b27d02c42acdc823b4ddc7c2d3676c1c29df924175aaa6cd01d866f49ee9671d403c9b3677005b795; desktop_session_key.sig=JnkVRY8sy5xIwJgrhySSzaDL8n8; ys=udn.czozMDQ4MjMzMjpnZzrQktCw0LvQtdGA0LAg0JfQsNGF0LDRgNC%2B0LI%3D#c_chck.629755954; PHPSESSID=vrfqovhketpmvmieplum7e4gd3; _csrf=fvduUL8hXfMiNPSXAf2phC4r; _csrf_csrf_token=V7yQs6OlBuZRbT0jX5AB2sV_Iy2VoxyP-Syo9_0vkBI; yandex_gid=213; uid=91411344; user_country=ru; ya_sess_id=noauth:1652595426; sso_status=sso.passport.yandex.ru:synchronized",
        "expirationDate": "null"}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/100.0"}
    DATABASE_ROWS = ['Name', 'Kp_id', 'Rating', 'Poster', 'Description', 'Director', 'Actors']
    DB_URL = "postgresql://yvwchtpldlobqv:e29bff18ea2f2ea79d9b01dccca9e0a888294351a93293742a1e2f8263fea599@ec2-34-234-240-121.compute-1.amazonaws.com:5432/d3mk94qpk4tcin"

    def db_add(self, row_values):
        """ adds element to the database """

        engine = create_engine(self.DB_URL, echo=False)
        # try:
        #     last_index = engine.execute("SELECT * FROM kp_api ORDER BY index DESC LIMIT 1;").fetchall()[0][0]
        # except IndexError:
        #     last_index = 0
        df = pd.DataFrame([row_values], columns=self.DATABASE_ROWS)
        df.to_sql("kp_api", con=engine, if_exists='append')

    def db_load(self):
        """ loads all elements from database """

        engine = create_engine(self.DB_URL, echo=False)
        return engine.execute("SELECT * FROM kp_api").fetchall()

    def parse_element(self, id):
        """ gets all the needed information after you enter url of the film"""
        s = requests.Session()
        r = s.get(f"https://www.kinopoisk.ru/film/{id}/", cookies=self.cookies)
        soup = BeautifulSoup(r.text, 'html.parser')
        film_name = soup.select(".styles_title__65Zwx > span:nth-child(1)")
        img_src = soup.select(".film-poster")
        # rating = soup.select(".film-rating-value") for rating there is another site https://rating.kinopoisk.ru/film_id.xml
        description = soup.select(".styles_paragraph__wEGPz")
        actors = soup.select(".styles_list___ufg4")
        director_parse = soup.select("div.styles_rowDark__ucbcz:nth-child(5)")
        director = ""
        for child in director_parse[0].contents[1].children:
            director += child.string
        r = s.get("https://rating.kinopoisk.ru/" + id + ".xml", cookies=self.cookies)
        soup = BeautifulSoup(r.text, 'html.parser')
        rating = soup.select("kp_rating")
        return [film_name[0].string, id, rating[0].string[:3], img_src[0]["src"][2:], description[0].string,
                director, actors[0].contents[0].string]

    def search(self, query):
        s = requests.Session()
        r = s.get("https://www.kinopoisk.ru/index.php?kp_query=" + query.replace(' ', '+'), cookies=self.cookies)
        soup = BeautifulSoup(r.text, 'html.parser')
        search_results = soup.select(".search_results .name a")
        if search_results == []:
            return self.parse_element("https://www.kinopoisk.ru/index.php?kp_query=" + query.replace(' ', '+'))[1]
        id_list = []
        for element in search_results:
            id_list.append(element.get('data-id'))
        return id_list

    def delete(self, id):
        engine = create_engine(self.DB_URL, echo=False)
        return engine.execute(f'DELETE FROM kp_api WHERE "Kp_id"=\'{id}\'')

api_engine = Engine()
# print(api_engine.db_load())
@app.route('/take_info', methods=['GET'])
def takeInfo():
    args = request.args
    result = api_engine.parse_element(args.get('query'))
    return {'data': result}, 200
@app.route('/film_list', methods=['GET'])
def film_list():
    results = [list(row) for row in api_engine.db_load()]
    results_dict = {'results': results}
    return {'data': results_dict}, 200  # return data and 200 OK
@app.route('/search', methods=['GET'])
def search():
    args = request.args
    search_result = api_engine.search(args.get('query'))
    return {'data': search_result}, 200
@app.route('/add_film', methods=['GET'])
def add_film():
    args = request.args
    api_engine.db_add(api_engine.parse_element(args.get('query')))
    return {}, 200
@app.route('/delete_film', methods=['GET'])
def delete_film():
    args = request.args
    api_engine.delete(args.get('query'))
    return {}, 200


if __name__ == '__main__':
    app.run()  # run our Flask app
