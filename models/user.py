from flask_login import UserMixin
from firebase_admin import firestore
from firebase_init import db

DEFAULT_PROFILE_PIC = 'https://firebasestorage.googleapis.com/v0/b/tiktok-web-clone-79191.appspot.com/o/default%2Fdefault_profile.png?alt=media'

class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data.get('id')
        self.username = user_data.get('username')
        self.email = user_data.get('email')
        self.password_hash = user_data.get('password_hash')
        self.profile_pic = user_data.get('profile_pic', DEFAULT_PROFILE_PIC)
        self.bio = user_data.get('bio', '')
        
    @staticmethod
    def get_by_id(user_id):
        user_doc = db.collection('users').document(user_id).get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            user_data['id'] = user_doc.id
            return User(user_data)
        return None
    
    @staticmethod
    def get_by_email(email):
        users = db.collection('users').where('email', '==', email).limit(1).stream()
        for user in users:
            user_data = user.to_dict()
            user_data['id'] = user.id
            return User(user_data)
        return None
    
    @staticmethod
    def get_by_username(username):
        users = db.collection('users').where('username', '==', username).limit(1).stream()
        for user in users:
            user_data = user.to_dict()
            user_data['id'] = user.id
            
            user_likes = db.collection('likes').where('user_id', '==', user.id).stream()
            user_data['likes'] = len(list(user_likes))
            
            return User(user_data)
            
        return None

    def get_videos(self):
        """Get user's videos ordered by timestamp"""
        from .video import Video
        # First get all videos for the user
        videos = db.collection('videos').where('user_id', '==', self.id).stream()
        # Then sort them in memory
        video_list = [Video.from_doc(video) for video in videos]
        return sorted(video_list, key=lambda x: x.timestamp, reverse=True)
    
    def get_likes(self):
        from .like import Like
        likes = db.collection('likes').where('user_id', '==', self.id).stream()
        return [Like.from_doc(like) for like in likes]
    
    def get_comments(self):
        """Get user's comments ordered by timestamp"""
        from .comment import Comment
        # First get all comments
        comments = db.collection('comments').where('user_id', '==', self.id).stream()
        # Then sort them in memory
        comment_list = [Comment.from_doc(comment) for comment in comments]
        return sorted(comment_list, key=lambda x: x.timestamp, reverse=True)
    
    def get_followers(self):
        followers = db.collection('follows').where('following_id', '==', self.id).stream()
        return [User.get_by_id(follow.to_dict()['follower_id']) for follow in followers]
    
    def get_following(self):
        following = db.collection('follows').where('follower_id', '==', self.id).stream()
        return [User.get_by_id(follow.to_dict()['following_id']) for follow in following]
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'profile_pic': self.profile_pic,
            'bio': self.bio
        }
    
    @staticmethod
    def from_doc(doc):
        user_data = doc.to_dict()
        user_data['id'] = doc.id
        return User(user_data)
