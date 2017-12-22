from flask import render_template, redirect, url_for, request, g, current_app, abort, jsonify

from . import main
from .forms import SearchForm
from ..models import *

@main.before_request
def before_request():
    g.search_form = SearchForm()
    g.search_form2 = SearchForm()

@main.app_errorhandler(404)
def page_not_found(e):
    return render_template('error/404.html', title='404'), 404

@main.app_errorhandler(500)
def internal_server_error(e):
    db.session.rollback()
    db.session.commit()
    return render_template('error/500.html', title='500'), 500

@main.route('/')
@main.route('/index')
def index():
    page = request.args.get('page', 1, type=int)

    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['POSTS_PER_PAGE'],
        error_out=False
    )
    posts = [post for post in pagination.items if post.draft == False]

    return render_template('index.html',
                           title='首页',
                           posts=posts,
                           pagination=pagination)

def nextPost(post):
    """
    获取本篇文章的下一篇
    :param post: post
    :return: next post
    """
    post_list = Post.query.order_by(Post.timestamp.desc()).all()
    posts = [post for post in post_list if post.draft == False]
    if posts[-1] != post:
        next_post = posts[posts.index(post) + 1]
        return next_post
    return None
def prevPost(post):
    """
    获取本篇文章的上一篇
    :param post: post
    :return: prev post
    """
    post_list = Post.query.order_by(Post.timestamp.desc()).all()
    posts = [post for post in post_list if post.draft == False]
    if posts[0] != post:
        prev_post = posts[posts.index(post) - 1]
        return prev_post
    return None

@main.route('/<int:year>/<int:month>/<article_name>/')
def post(year, month, article_name):
    time = str(year) + '-' + str(month)
    posts = Post.query.filter_by(url_name=article_name).all()
    post = ''
    if len(posts) == 1:
        post = posts[0]
    elif len(posts) > 1:
        post = [i for i in posts if time in i.timestamp][0]
    elif len(posts) < 1:
        abort(404)

    post.view_num += 1
    db.session.add(post)
    tags = [tag for tag in post.tags.split(',')]
    next_post = nextPost(post)
    prev_post = prevPost(post)
    return render_template('post.html', post=post, tags=tags, title=post.title,
                           next_post=next_post, prev_post=prev_post)


@main.route('/page/<page_url>/')
def page(page_url):
    page = Page.query.filter_by(url_name=page_url).first()

    return render_template('page.html', page=page)

@main.route('/tag/<tag_name>/')
def tag(tag_name):
    tag = tag_name
    all_posts = Post.query.order_by(Post.timestamp.desc()).all()
    posts = [post for post in all_posts if post.tag_in_post(tag) and post.draft==False]

    return render_template('tag.html', tag=tag, posts=posts)

@main.route('/category/<category_name>/')
def category(category_name):
    category = Category.query.filter_by(category=category_name).first()

    posts = Post.query.filter_by(category=category, draft=False).order_by(Post.timestamp.desc()).all()
    return render_template('category.html',
                           category=category,
                           posts=posts,
                           title='分类：' + category.category)

@main.route('/archives/')
def archives():
    count = Post.query.count()
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['ACHIVES_POSTS_PER_PAGE'],
        error_out=False
    )
    posts = [post for post in pagination.items if post.draft == False]
    times = [post.timestamp for post in posts ]
    year = set([i.split('-')[0] for i in times])
    data = {}
    year_post = []
    for y in year:
        for p in posts:
            if y in p.timestamp:
                year_post.append(p)
                data[y] = year_post
        year_post = []

    return render_template('archives.html',
                           title='归档',
                           posts=posts,
                           data=data,
                           count=count,
                           pagination=pagination)

@main.route('/search/', methods=['GET', 'POST'])
def search():
    if g.search_form.validate_on_submit():
        query = g.search_form.search.data
        return redirect(url_for('main.search_result', keywords=query))

    elif g.search_form2.validate_on_submit():
        print('a')
        query = g.search_form2.search.data
        return redirect(url_for('main.search_result', keywords=query))

# /search-result?keywords=query
@main.route('/search-result/')
def search_result():
    query = request.args.get('keywords')
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.whooshee_search(query).order_by(Post.id.desc()).paginate(
        page, per_page=current_app.config['SEARCH_POSTS_PER_PAGE'],
        error_out=False
    )
    results = [post for post in pagination.items if post.draft == False]
    return render_template('results.html',
                           results=results,
                           query=query,
                           pagination=pagination,
                           title=query + '的搜索结果')

@main.route('/loveme', methods=['GET'])
def love_me():
    love_me_counts = LoveMe.query.all()[0]
    love_me_counts.loveMe += 1
    db.session.add(love_me_counts)
    db.session.commit()
    return jsonify(counts=love_me_counts.loveMe)

