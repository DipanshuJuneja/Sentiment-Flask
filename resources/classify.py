from flask_restful import Resource, reqparse
import pickle
from nltk.tokenize import TweetTokenizer
import numpy as np
import tweepy


consumer_key = "JwG59C0A3lDgUWQn3fxLx0AV7"
consumer_secret = "VaJ8lAdmpMWGIMluCGi8DmH2GxPx099IEXAahb2DiFZan7rCgZ"
access_token = "67006072-H5mlQrT0PkIx3B2zH07NSQftAFPGYMzAReqDVr4jD"
access_secret = "sSnZRzLTgIQrcuw3HG2ScD8G3OuKlDi6LMC64D3wSbRyk"

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)
api = tweepy.API(auth)

# clf = pickle.load(open("LOGISTIC_CLASSIFIER.p","rb"))
# features = pickle.load(open("FEATURE_NAMES.p", "rb"))
clf = pickle.load(open("multinomial_classifier3.p","rb"))
features = pickle.load(open("new_features2.p","rb"))

tokenizer = TweetTokenizer()

class Classify(Resource):
	"""Classify the text"""
	parser = reqparse.RequestParser()
	parser.add_argument('search_text', type=str, required=True)
	parser.add_argument('num_results', type=int, required=True)

	def post(self):
		tweets_list = []  # to return, list of dicts
		search_text = Classify.parser.parse_args()['search_text']   # text to search
		num_results = Classify.parser.parse_args()['num_results']  # no. of queries

		# User just wants to test the algo
		if num_results == 0:
			return {'results': self.class_tweet(search_text)[0], "message":'success'}


		for tweet in api.search(q=search_text,lang="en", count=num_results):
			tweets_list.append({"classification": Classify.class_tweet(tweet.text),'user_name': tweet.user.name, 
		    "user_screen_name": tweet.user.screen_name, 'tweet_content': tweet.text, 'ids': tweet.id,
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
		print(result_prob)

		if result_prob > 0.53:
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
