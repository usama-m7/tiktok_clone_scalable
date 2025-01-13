from datetime import datetime
from firebase_admin import firestore
from firebase_init import db

class Comment:
    def __init__(self, comment_data):
        self.id = comment_data.get('id')
        self.content = comment_data.get('content')
        self.timestamp = comment_data.get('timestamp', datetime.now())
        self.user_id = comment_data.get('user_id')
        self.video_id = comment_data.get('video_id')
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
        comment_data = doc.to_dict()
        comment_data['id'] = doc.id
        return Comment(comment_data)
    
    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'timestamp': self.timestamp,
            'user_id': self.user_id,
            'video_id': self.video_id,
            'user': self.user.to_dict() if self.user else None
        }
    
    @staticmethod
    def get_recent_comments(video_id, limit=10):
        """Get recent comments for a video"""
        comments = db.collection('comments').where('video_id', '==', video_id).stream()
        comment_list = [Comment.from_doc(comment) for comment in comments]
        return sorted(comment_list, key=lambda x: x.timestamp, reverse=True)[:limit]
