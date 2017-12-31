from flask import Flask
from flask_restful import Api
from resources.classify import Classify, LiveStream

app = Flask(__name__)
api = Api(app)

api.add_resource(Classify, '/classify')
api.add_resource(LiveStream, '/live')



if __name__ == '__main__':
	app.run(port=5000, debug=True)

 # host='0.0.0.0'