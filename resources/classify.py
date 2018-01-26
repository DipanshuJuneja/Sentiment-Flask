from flask_restful import Resource, reqparse
import pickle
from nltk.tokenize import TweetTokenizer
import numpy as np
import tweepy
import time
import threading
from flask import Response, json
from paralleldots import set_api_key, sentiment


### YOUR OWN API KEYS AND TOKEN/SECRET ####
consumer_key = "JwG59C0A3lDgUWQn3fxLx0AV7"
consumer_secret = "VaJ8lAdmpMWGIMluCGi8DmH2GxPx099IEXAahb2DiFZan7rCgZ"
access_token = "67006072-H5mlQrT0PkIx3B2zH07NSQftAFPGYMzAReqDVr4jD"
access_secret = "sSnZRzLTgIQrcuw3HG2ScD8G3OuKlDi6LMC64D3wSbRyk"
#################

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)
api = tweepy.API(auth)

stream_list = []
myStream = None 

# clf = pickle.load(open("LOGISTIC_CLASSIFIER.p","rb"))
# features = pickle.load(open("FEATURE_NAMES.p", "rb"))
clf = pickle.load(open("MULTI8NounR.p","rb"))
features = pickle.load(open("new_features8000NR.p","rb"))

tokenizer = TweetTokenizer()

class Classify(Resource):
	"""Classify the text"""
	parser = reqparse.RequestParser()
	parser.add_argument('search_text', type=str, required=True)
	parser.add_argument('num_results', type=int, required=False)
	parser.add_argument('result_type', type=str, required=False)
	parser.add_argument('since_id', type=int, required=False)

	def post(self):
		tweets_list = []  # to return, list of dicts
		search_text = Classify.parser.parse_args()['search_text']   # text to search
		num_results = Classify.parser.parse_args()['num_results']  # no. of queries
		result_type = Classify.parser.parse_args()['result_type']  # recent popular mixed
		since_id = Classify.parser.parse_args()['since_id']  # latest than this

		# User just wants to test the algo
		if num_results == 0:
			## YOUR OWN KEY ###
			set_api_key('gIX6AK1i1b1O4EG5hHJ79JCDuT4OUk7vRyagH1gfrQM')
			################
			result_parallel = sentiment(search_text)["sentiment"]
			to_return = None

			if result_parallel == "positive":
				to_return = "pos"
			elif result_parallel == "negative":
				to_return = "neg"
			else:
				to_return = "trash"
			
			
			return {'results': to_return, "message":'success'}

		# user is using SEARCH API
		if num_results and result_type:
			for tweet in api.search(q=search_text,lang="en", count=num_results, result_type=result_type):
				tweets_list.append({"classification": Classify.class_tweet(tweet.text),'user_name': tweet.user.name, 
				"user_screen_name": '@'+tweet.user.screen_name, 'tweet_content': tweet.text, 'ids': tweet.id,
				'image_src': tweet.user.profile_image_url_https, 'likes': tweet.favorite_count if tweet.favorite_count else (tweet.retweeted_status.favorite_count if hasattr(tweet,'retweeted_status')  else 0)
				, 'retweets': tweet.retweet_count if tweet.retweet_count else (tweet.retweeted_status.retweet_count if hasattr(tweet,'retweeted_status')  else 0)} )

		if since_id:
			for tweet in api.search(q=search_text,lang="en", count=100, since_id=since_id):
				tweets_list.append({"classification": Classify.class_tweet(tweet.text),'user_name': tweet.user.name, 
				"user_screen_name": '@'+tweet.user.screen_name, 'tweet_content': tweet.text, 'ids': tweet.id,
				'image_src': tweet.user.profile_image_url_https, 'likes': tweet.favorite_count if tweet.favorite_count else (tweet.retweeted_status.favorite_count if hasattr(tweet,'retweeted_status')  else 0)
				, 'retweets': tweet.retweet_count if tweet.retweet_count else (tweet.retweeted_status.retweet_count if hasattr(tweet,'retweeted_status')  else 0)} )

		return {"results": tweets_list, "message":'success'}

	# has to be called for Live streamed tweets as well
	@staticmethod
	def class_tweet(tweet_text):
		tk = tokenizer.tokenize(tweet_text)  # ["You", "me", "together"]
		to_predict = np.asarray([tk.count(feature) for feature in features]).reshape(1,-1)
		result = int(clf.predict(to_predict)[0])
		result_prob = clf.predict_proba(to_predict).max()

		#print(result_prob)
		#print(result)

		if result_prob > 0.52:
			# if Positive
			if result == 1:
				if result_prob > 0.8:
					return ["pos",1,0,0,0,0,0,'#A5D6A7']
				elif result_prob > 0.65:
					return ["pos",0,1,0,0,0,0,'#A5D6A7']
				else:
					return ["pos",0,0,1,0,0,0,'#A5D6A7']

			# if Negative
			else:
				if result_prob > 0.8:
					return ["neg",0,0,0,1,0,0,'#EF9A9A']
				elif result_prob > 0.65:
					return ["neg",0,0,0,0,1,0,'#EF9A9A']
				else:
					return ["neg",0,0,0,0,0,1,'#EF9A9A']
		else:
			return ["trash",0,0,0,0,0,0,'#BDBDBD']

class MyStreamListener(tweepy.StreamListener):
	def on_status(self, status):
		stream_list.append({"classification": Classify.class_tweet(status.text),'user_name': status.user.name, 
			"user_screen_name": status.user.screen_name, 'tweet_content': status.text, 'ids': status.id,
			'image_src': status.user.profile_image_url_https, 'likes': status.favorite_count if status.favorite_count else (status.retweeted_status.favorite_count if hasattr(status,'retweeted_status')  else 0)
			, 'retweets': status.retweet_count if status.retweet_count else (status.retweeted_status.retweet_count if hasattr(status,'retweeted_status')  else 0)})
		print("Current length of stream ",len(stream_list))
		#yield json.dumps({"results": [row]})

class LiveStream(Resource):
	"""docstring for LiveStream"""
	parser = reqparse.RequestParser()
	parser.add_argument('search_text', type=str, required=True)
	#parser.add_argument('disconnect', type=int, required=True)

	def post(self):
		global myStream
		if myStream is not None:
			return {"results": "Stream in use"}

		search_text = LiveStream.parser.parse_args()['search_text'] 
	#	disconnect = LiveStream.parser.parse_args()['disconnect'] 
		myStreamListener = MyStreamListener()

		try:
			myStream = tweepy.Stream(auth = api.auth, listener=myStreamListener)
			myStream.filter(track=[search_text], async=True)
		except:
			print("ERROR WHILE STARTING")
			return {"results": "Error in starting stream"}

		start = time.time()
		t = threading.Thread(target=stream_disconnect, name="stream_start", args=(start,17))
		t.start()
		print("STREAM STARTED")
		time.sleep(15)
		def generate():
			#for row in stream_list:
			#	yield json.dumps({"results": [row]})
			yield json.dumps({"results": [row for row in stream_list]})
		return Response(generate(), mimetype='application/json')

def stream_disconnect(start_time,last_for):
	while True:
		if (time.time() - start_time) >= last_for:
			global myStream, stream_list
			myStream.disconnect()
			myStream = None 
			stream_list = []
			print("Stream disconnected")
			break
	return

# class ReturnTweets(Resource):
# 	"""docstring for ReturnTweets"""
# 	parser = reqparse.RequestParser()
# 	parser.add_argument('received', type=int, required=True)

# 	def post(self):
# 		received = ReturnTweets.parser.parse_args()['received']
# 		print("current length of stream_list ", len(stream_list))
# 		return {"results":stream_list[received:],"connected":connected}
