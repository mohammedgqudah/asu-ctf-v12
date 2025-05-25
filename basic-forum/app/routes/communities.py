from flask import Blueprint, flash, render_template, request, redirect, session, abort
from jinja2.exceptions import SecurityError
from jinja2.sandbox import ImmutableSandboxedEnvironment

from models.base import db
from models.user import User
from models.post import Post
from models.community import Community

from routes.utils import login_required

bp = Blueprint("communities", __name__)

@bp.get("/")
@login_required
def index():
    user = User.query.get(session['user_id'])
    if not user:
        flash('User not found.', 'danger')
        return redirect('/login')

    joined_communities = user.communities
    # communities you can still join
    communities = Community.query.filter(~Community.members.any(id=user.id)).all()


    return render_template("index.html", communities=communities, joined_communities=joined_communities)


@bp.get("/community/<int:community_id>")
@login_required
def view_community(community_id: int):
    user = User.query.get(session['user_id'])
    community: Community = Community.query.get_or_404(community_id)
    if user not in community.members:
        flash("You're not a member in that community")
        return redirect("/")

    return render_template("community.html", community=community)

@bp.post("/community/<int:community_id>")
@login_required
def add_post(community_id: int):
    user = User.query.get(session['user_id'])
    community: Community = Community.query.get_or_404(community_id)
    title = request.form.get('title')
    content = request.form.get('content')

    if not title or not content:
        flash("Missing form data")
        return redirect(request.url)

    if user not in community.members:
        flash("You're not a member in that community")
        return redirect("/")

    
    post = Post(title=title, content=content, author_id=user.id)
    community.posts.append(post)
    db.session.commit()

    return redirect(request.url)

@bp.post('/create')
@login_required
def create_community():
    name = request.form.get('name')
    welcome_template = request.form.get('welcome_template', 'Welcome, {{user.username}}')

    if not name:
        flash('Community name is required.', 'danger')
        return redirect('/')

    user = User.query.get(session['user_id'])

    # Create community with current user as owner and member
    community = Community(name=name, owner=user, welcome_template=welcome_template)
    community.members.append(user)
    db.session.add(community)
    db.session.commit()

    flash(f'You\'ve successfully created the community "{name}"', 'success')
    return redirect('/')

@bp.post('/join/<int:community_id>')
@login_required
def join_community(community_id):
    user = User.query.get(session['user_id'])
    community = Community.query.get(community_id)
    if not community:
        abort(404, description='Community not found')

    # Prevent duplicate membership
    if community in user.communities:
        flash('You are already a member of this community.', 'info')
        return redirect('/')

    try:
        sandbox_env = ImmutableSandboxedEnvironment()
        welcome_message = sandbox_env.from_string(community.welcome_template).render(user=user)
    except SecurityError:
        return "Attempted to render an insecure template. The community owner has been reported."
    except Exception:
        return "Failed to join"

    community.members.append(user)
    db.session.commit()


    flash(welcome_message, 'success')
    return redirect('/community/' + str(community.id))
