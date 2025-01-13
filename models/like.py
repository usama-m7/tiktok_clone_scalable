from datetime import datetime
from firebase_init import db

class Like:
    def __init__(self, like_data):
        self.id = like_data.get('id')
        self.user_id = like_data.get('user_id')
        self.video_id = like_data.get('video_id')
        self.timestamp = like_data.get('timestamp', datetime.now())
        self._user = None
        self._video = None

    @property
    def user(self):
        if not self._user:
            from .user import User
            self._user = User.get_by_id(self.user_id)
        return self._user

    @property
    def video(self):
        if not self._video:
            from .video import Video
            video_doc = db.collection('videos').document(self.video_id).get()
            self._video = Video.from_doc(video_doc)
        return self._video

    @staticmethod
    def from_doc(doc):
        like_data = doc.to_dict()
        like_data['id'] = doc.id
        return Like(like_data)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'video_id': self.video_id,
            'timestamp': self.timestamp
        }
    
    @staticmethod
    def get_user_likes(user_id):
        likes = db.collection('likes').where('user_id', '==', user_id).stream()
        return [Like.from_doc(like) for like in likes]
    
    @staticmethod
    def get_video_likes(video_id):
        likes = db.collection('likes').where('video_id', '==', video_id).stream()
        return [Like.from_doc(like) for like in likes]
    
    @staticmethod
    def check_if_liked(user_id, video_id):
        likes = (
            db.collection('likes')
            .where('user_id', '==', user_id)
            .where('video_id', '==', video_id)
            .limit(1)
            .stream()
        )
        return next(likes, None) is not None
