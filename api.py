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
    DATABASE_ROWS = ['Name', 'Kp_id', 'Rating', 'Poster', 'Description', 'Director', 'Actors', 'Notes', 'Screenshots']
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

    def parse_element(self, url):
        """ gets all the needed information after you enter url of the film"""
        s = requests.Session()
        r = s.get(url, cookies=self.cookies)
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
        r = s.get("https://rating.kinopoisk.ru/" + url[30:-1] + ".xml", cookies=self.cookies)
        soup = BeautifulSoup(r.text, 'html.parser')
        rating = soup.select("kp_rating")
        return [film_name[0].string, url[30:-1], rating[0].string[:-2], img_src[0]["src"][2:], description[0].string,
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


api_engine = Engine()

# print(api_engine.db_load())
# class film_list(Resource):
#
#     def get(self):
#         results = [list(row) for row in api_engine.db_load()]
#         results_dict = {'results': results}
#         return {'data': results_dict}, 200  # return data and 200 OK

    # def post(self):
    #     # parser = reqparse.RequestParser()  # initialize
    #     # parser.add_argument('userId', required=True)  # add args
    #     # parser.add_argument('name', required=True)
    #     # parser.add_argument('city', required=True)
    #     # args = parser.parse_args()  # parse arguments to dictionary
    #     #
    #     # # read our CSV
    #     # data = pd.read_csv('users.csv')
    #     #
    #     # if args['userId'] in list(data['userId']):
    #     #     return {
    #     #                'message': f"'{args['userId']}' already exists."
    #     #            }, 409
    #     # else:
    #     #     # create new dataframe containing new values
    #     #     new_data = pd.DataFrame({
    #     #         'userId': [args['userId']],
    #     #         'name': [args['name']],
    #     #         'city': [args['city']],
    #     #         'locations': [[]]
    #     #     })
    #     #     # add the newly provided values
    #     #     data = data.append(new_data, ignore_index=True)
    #     #     data.to_csv('users.csv', index=False)  # save back to CSV
    #     #     return {'data': data.to_dict()}, 200  # return data with 200 OK
    #     pass
    # def put(self):
    #     # parser = reqparse.RequestParser()  # initialize
    #     # parser.add_argument('userId', required=True)  # add args
    #     # parser.add_argument('location', required=True)
    #     # args = parser.parse_args()  # parse arguments to dictionary
    #     #
    #     # # read our CSV
    #     # data = pd.read_csv('users.csv')
    #     #
    #     # if args['userId'] in list(data['userId']):
    #     #     # evaluate strings of lists to lists !!! never put something like this in prod
    #     #     data['locations'] = data['locations'].apply(
    #     #         lambda x: ast.literal_eval(x)
    #     #     )
    #     #     # select our user
    #     #     user_data = data[data['userId'] == args['userId']]
    #     #
    #     #     # update user's locations
    #     #     user_data['locations'] = user_data['locations'].values[0] \
    #     #         .append(args['location'])
    #     #
    #     #     # save back to CSV
    #     #     data.to_csv('users.csv', index=False)
    #     #     # return data and 200 OK
    #     #     return {'data': data.to_dict()}, 200
    #     #
    #     # else:
    #     #     # otherwise the userId does not exist
    #     #     return {
    #     #                'message': f"'{args['userId']}' user not found."
    #     #            }, 404
    #     pass
    # def delete(self):
    #     # parser = reqparse.RequestParser()  # initialize
    #     # parser.add_argument('userId', required=True)  # add userId arg
    #     # args = parser.parse_args()  # parse arguments to dictionary
    #     #
    #     # # read our CSV
    #     # data = pd.read_csv('users.csv')
    #     #
    #     # if args['userId'] in list(data['userId']):
    #     #     # remove data entry matching given userId
    #     #     data = data[data['userId'] != args['userId']]
    #     #
    #     #     # save back to CSV
    #     #     data.to_csv('users.csv', index=False)
    #     #     # return data and 200 OK
    #     #     return {'data': data.to_dict()}, 200
    #     # else:
    #     #     # otherwise we return 404 because userId does not exist
    #     #     return {
    #     #                'message': f"'{args['userId']}' user not found."
    #     #            }, 404
    #     #
    #     pass
@app.route('/takeInfo', methods=['GET'])
def takeInfo():
    args = request.args
    print(args.get('query'))
    return args
@app.route('/film_list', methods=['GET'])
def film_list():
    results = [list(row) for row in api_engine.db_load()]
    results_dict = {'results': results}
    return {'data': results_dict}, 200  # return data and 200 OK
@app.route('/search', methods=['GET'])
def search():
    args = request.args
    return api_engine.search(args.get('query'))
# class Locations(Resource):
#     def get(self):
#         data = pd.read_csv('locations.csv')  # read local CSV
#         return {'data': data.to_dict()}, 200  # return data dict and 200 OK
#
#     def post(self):
#         parser = reqparse.RequestParser()  # initialize parser
#         parser.add_argument('locationId', required=True, type=int)  # add args
#         parser.add_argument('name', required=True)
#         parser.add_argument('rating', required=True)
#         args = parser.parse_args()  # parse arguments to dictionary
#
#         # read our CSV
#         data = pd.read_csv('locations.csv')
#
#         # check if location already exists
#         if args['locationId'] in list(data['locationId']):
#             # if locationId already exists, return 401 unauthorized
#             return {
#                        'message': f"'{args['locationId']}' already exists."
#                    }, 409
#         else:
#             # otherwise, we can add the new location record
#             # create new dataframe containing new values
#             new_data = pd.DataFrame({
#                 'locationId': [args['locationId']],
#                 'name': [args['name']],
#                 'rating': [args['rating']]
#             })
#             # add the newly provided values
#             data = data.append(new_data, ignore_index=True)
#             data.to_csv('locations.csv', index=False)  # save back to CSV
#             return {'data': data.to_dict()}, 200  # return data with 200 OK
#
#     def patch(self):
#         parser = reqparse.RequestParser()  # initialize parser
#         parser.add_argument('locationId', required=True, type=int)  # add args
#         parser.add_argument('name', store_missing=False)  # name/rating are optional
#         parser.add_argument('rating', store_missing=False)
#         args = parser.parse_args()  # parse arguments to dictionary
#
#         # read our CSV
#         data = pd.read_csv('locations.csv')
#
#         # check that the location exists
#         if args['locationId'] in list(data['locationId']):
#             # if it exists, we can update it, first we get user row
#             user_data = data[data['locationId'] == args['locationId']]
#
#             # if name has been provided, we update name
#             if 'name' in args:
#                 user_data['name'] = args['name']
#             # if rating has been provided, we update rating
#             if 'rating' in args:
#                 user_data['rating'] = args['rating']
#
#             # update data
#             data[data['locationId'] == args['locationId']] = user_data
#             # now save updated data
#             data.to_csv('locations.csv', index=False)
#             # return data and 200 OK
#             return {'data': data.to_dict()}, 200
#
#         else:
#             # otherwise we return 404 not found
#             return {
#                        'message': f"'{args['locationId']}' location does not exist."
#                    }, 404
#
#     def delete(self):
#         parser = reqparse.RequestParser()  # initialize parser
#         parser.add_argument('locationId', required=True, type=int)  # add locationId arg
#         args = parser.parse_args()  # parse arguments to dictionary
#
#         # read our CSV
#         data = pd.read_csv('locations.csv')
#
#         # check that the locationId exists
#         if args['locationId'] in list(data['locationId']):
#             # if it exists, we delete it
#             data = data[data['locationId'] != args['locationId']]
#             # save the data
#             data.to_csv('locations.csv', index=False)
#             # return data and 200 OK
#             return {'data': data.to_dict()}, 200
#
#         else:
#             # otherwise we return 404 not found
#             return {
#                 'message': f"'{args['locationId']}' location does not exist."
#             }


# api.add_resource(film_list, '/film_list')  # add endpoints
# api.add_resource(search, '/search')  # add endpoints


if __name__ == '__main__':
    app.run()  # run our Flask app
