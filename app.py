from flask import Flask
from flask_restful import Api
import resources.classify as Class

app = Flask(__name__)
api = Api(app)

api.add_resource(Class.Classify, '/classify')
api.add_resource(Class.LiveStream, '/live')
api.add_resource(Class.ReturnTweets, '/returnTweets')

if __name__ == '__main__':
	app.run(port=5000, debug=True)

 # host='0.0.0.0'