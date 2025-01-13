from datetime import datetime
from firebase_admin import firestore
from firebase_init import db

class Video:
    def __init__(self, video_data):
        self.id = video_data.get('id')
        self.filename = video_data.get('filename')
        self.caption = video_data.get('caption', '')
        self.hashtags = video_data.get('hashtags', [])
        self.timestamp = video_data.get('timestamp', datetime.now())
        self.user_id = video_data.get('user_id')
        self.views = video_data.get('views', 0)
        self._author = None
        self._likes = None
        self._comments = None

    @property
    def author(self):
        if not self._author:
            from .user import User
            self._author = User.get_by_id(self.user_id)
        return self._author

    @property
    def likes(self):
        if self._likes is None:
            self._likes = self.get_likes()
        return self._likes

    @property
    def comments(self):
        if self._comments is None:
            self._comments = self.get_comments()
        return self._comments

    @staticmethod
    def from_doc(doc):
        video_data = doc.to_dict()
        video_data['id'] = doc.id
        return Video(video_data)

    def get_comments(self):
        from .comment import Comment
        comments = db.collection('comments').where('video_id', '==', self.id).stream()
        comment_list = [Comment.from_doc(comment) for comment in comments]
        return sorted(comment_list, key=lambda x: x.timestamp)

    def get_likes(self):
        from .like import Like
        likes = db.collection('likes').where('video_id', '==', self.id).stream()
        return [Like.from_doc(like) for like in likes]
    
    def increment_views(self):
        doc_ref = db.collection('videos').document(self.id)
        doc_ref.update({'views': firestore.Increment(1)})
        self.views += 1

    @staticmethod
    def get_trending_videos(limit=10):
        """Get trending videos sorted by views"""
        videos_ref = db.collection('videos')
        videos = videos_ref.order_by('views', direction=firestore.Query.DESCENDING).limit(limit).stream()
        return [Video.from_doc(video) for video in videos]

    @staticmethod
    def search_by_hashtag(hashtag, limit=20):
        """Search videos by hashtag"""
        videos_ref = db.collection('videos')
        videos = videos_ref.where('hashtags', 'array_contains', hashtag).limit(limit).stream()
        return [Video.from_doc(video) for video in videos]
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'caption': self.caption,
            'hashtags': self.hashtags,
            'timestamp': self.timestamp,
            'user_id': self.user_id,
            'views': self.views,
            'author': self.author.to_dict() if self.author else None,
            'likes_count': len(self.likes),
            'comments_count': len(self.comments)
        }
