import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import uuid

# Import Firebase initialization
from firebase_init import db, bucket

# Import models
from models import User, Video, Comment, Like

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

DEFAULT_PROFILE_PIC = 'default.jpg'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


def upload_file_to_firebase(file, folder):
    """Upload a file to Firebase Storage and return its public URL"""
    if not file:
        return None

    # Create a unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"

    # Create the full path in Firebase Storage
    blob = bucket.blob(f"{folder}/{unique_filename}")

    # Upload the file
    blob.upload_from_string(
        file.read(),
        content_type=file.content_type
    )

    # Make the file publicly accessible
    blob.make_public()

    return blob.public_url


@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)


@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 5
    videos = Video.get_trending_videos(limit=per_page * page)
    return render_template('index.html', videos=videos)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.get_by_username(username)

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index'))

        flash('Invalid username or password')
    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        bio = request.form.get('bio', '')

        if User.get_by_username(username):
            flash('Username already exists')
            return redirect(url_for('signup'))

        if User.get_by_email(email):
            flash('Email already registered')
            return redirect(url_for('signup'))

        user_data = {
            'username': username,
            'email': email,
            'password_hash': generate_password_hash(password),
            'bio': bio,
            'profile_pic': DEFAULT_PROFILE_PIC  # Use the default profile picture URL
        }

        # Create new user document
        user_ref = db.collection('users').document()
        user_ref.set(user_data)

        # Get the user object
        user = User.get_by_id(user_ref.id)
        login_user(user)
        return redirect(url_for('index'))

    return render_template('signup.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        if 'video' not in request.files:
            flash('No video file')
            return redirect(request.url)

        video = request.files['video']
        caption = request.form.get('caption', '')
        hashtags = request.form.get('hashtags', '')

        if video.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if video:
            # Upload video to Firebase Storage
            video_url = upload_file_to_firebase(video, 'videos')

            if video_url:
                # Process hashtags: remove '#' if present and split by space
                hashtags = [tag.strip('#') for tag in hashtags.split()]

                # Save video data to Firestore
                video_data = {
                    'filename': video_url,
                    'caption': caption,
                    'hashtags': hashtags,  # Store hashtags without '#'
                    'timestamp': datetime.now(),
                    'user_id': current_user.id,
                    'views': 0
                }
                db.collection('videos').document().set(video_data)
                return redirect(url_for('index'))

            flash('Error uploading video')
            return redirect(request.url)

    return render_template('upload.html')


@app.route('/profile/<username>')
def profile(username):
    user = User.get_by_username(username)
    if not user:
        return abort(404)
    videos = user.get_videos()
    user_likes = len(user.get_likes())

    return render_template('profile.html', user=user, videos=videos, likes=user_likes)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        file = request.files.get('profile_pic')
        if file and file.filename != '':

            # Upload profile picture to Firebase Storage
            profile_pic_url = upload_file_to_firebase(file, 'profiles')

            if profile_pic_url:
                # Update user profile in Firestore
                user_doc = db.collection('users').document(current_user.id)
                user_doc.update({
                    'profile_pic': profile_pic_url  # Store the full URL
                })
                current_user.profile_pic = profile_pic_url  # Update current user object

        bio = request.form.get('bio')
        if bio is not None:
            user_doc = db.collection('users').document(current_user.id)
            user_doc.update({'bio': bio})
            current_user.bio = bio  # Update current user object

        return redirect(url_for('profile', username=current_user.username))

    return render_template('edit_profile.html')


@app.route('/search')
def search():
    query = request.args.get('q', '')
    search_type = request.args.get('type', 'all')

    if not query:
        return render_template('search.html', users=[], videos=[], query=query, search_type=search_type)

    if search_type == 'users':
        users = [User.get_by_username(query)]
        if not users[0]:
            return render_template('search.html', users=[], user_videos=[], query=query, search_type=search_type)
        # get user videos
        user_videos = users[0].get_videos()
        return render_template('search.html', users=users, user_videos=user_videos, query=query, search_type=search_type)

    elif search_type == 'hashtags':
        # Remove '#' from query if present
        hashtag = query.strip('#')
        videos = Video.search_by_hashtag(hashtag)

        return render_template('search.html', users=[], videos=videos, query=query, search_type=search_type)

    else:  # 'all'
        users = [User.get_by_username(query)]
        # Remove '#' from query if present for hashtag search
        hashtag = query.strip('#')
        videos = Video.search_by_hashtag(hashtag)

        if not users[0] and not videos:
            return render_template('search.html', users=[], videos=[], query=query, search_type=search_type)

        if not users[0]:
            return render_template('search.html', users=[], user_videos=[], videos=videos, query=query, search_type=search_type)

        user_videos = users[0].get_videos()
        return render_template('search.html', users=users, user_videos=user_videos, videos=videos, query=query, search_type=search_type)


@app.route('/like/<video_id>', methods=['POST'])
@login_required
def like_video(video_id):
    if Like.check_if_liked(current_user.id, video_id):
        # Unlike the video
        likes = db.collection('likes').where('user_id', '==', current_user.id).where(
            'video_id', '==', video_id).stream()
        for like in likes:
            like.reference.delete()
        return jsonify({'action': 'unliked', 'likes': len(Like.get_video_likes(video_id))})
    else:
        # Like the video
        like_data = {
            'user_id': current_user.id,
            'video_id': video_id,
            'timestamp': datetime.now()
        }
        db.collection('likes').document().set(like_data)
        return jsonify({'action': 'liked', 'likes': len(Like.get_video_likes(video_id))})


@app.route('/add_comment/<video_id>', methods=['POST'])
@login_required
def add_comment(video_id):
    data = request.get_json()
    content = data.get('content')
    if content:
        comment_data = {
            'content': content,
            'timestamp': datetime.now(),
            'user_id': current_user.id,
            'video_id': video_id
        }
        comment_ref = db.collection('comments').document()
        comment_ref.set(comment_data)

        return jsonify({
            'id': comment_ref.id,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'user': {
                'username': current_user.username,
                'profile_pic': current_user.profile_pic
            }
        })
    return jsonify({'error': 'No content provided'}), 400


@app.route('/get_comments/<video_id>')
def get_comments(video_id):
    comments = Comment.get_recent_comments(video_id)
    comments_data = []
    for comment in comments:
        comments_data.append({
            'id': comment.id,
            'content': comment.content,
            'timestamp': comment.timestamp.isoformat(),
            'user': {
                'username': comment.user.username,
                'profile_pic': comment.user.profile_pic
            }
        })
    return jsonify(comments_data)


@app.route('/get_more_comments/<video_id>')
def get_more_comments(video_id):
    # Get the last comment ID from the request
    last_comment_id = request.args.get('last_id', 0, type=int)

    # Get the next 10 comments
    comments = db.collection('comments').where('video_id', '==', video_id).where(
        'id', '>', last_comment_id).order_by('timestamp').limit(10).stream()

    # Convert comments to JSON
    comments_data = []
    for comment in comments:
        comment_data = comment.to_dict()
        comment_data['id'] = comment.id
        comments_data.append({
            'id': comment_data['id'],
            'content': comment_data['content'],
            'timestamp': comment_data['timestamp'].isoformat(),
            'user': {
                'username': User.get_by_id(comment_data['user_id']).username,
                'profile_pic': User.get_by_id(comment_data['user_id']).profile_pic
            }
        })

    return jsonify(comments_data)


if __name__ == '__main__':
    app.run(debug=True)
