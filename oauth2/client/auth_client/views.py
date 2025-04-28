from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from .oauth2_client import OAuth2Client
import secrets

oauth_client = OAuth2Client()

def home(request):
    return render(request, 'home.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    # Generate a random state parameter for CSRF protection
    state = secrets.token_urlsafe(32)
    request.session['oauth_state'] = state
    
    # Get the authorization URL
    auth_url = oauth_client.get_authorization_url(state)
    return redirect(auth_url)

def oauth_callback(request):
    # Verify state parameter
    state = request.GET.get('state')
    if not state or state != request.session.get('oauth_state'):
        messages.error(request, 'Invalid state parameter')
        return redirect('login')
    
    # Get authorization code
    code = request.GET.get('code')
    if not code:
        messages.error(request, 'Authorization code not provided')
        return redirect('login')
    print("\n\n here is call back after if's \n\n")
    try:
        # Exchange code for tokens
        token_response = oauth_client.get_token(code)
        print(f"\n\n here is token response: {token_response} \n\n")
        # Get user info
        user_info = oauth_client.get_user_info(token_response['access_token'])
        print(f"\n\n here is user info: {user_info} \n\n")
        
        # Store tokens in session
        request.session['access_token'] = token_response['access_token']
        request.session['refresh_token'] = token_response.get('refresh_token')
        
        # Create or update user
        from django.contrib.auth.models import User
        user, created = User.objects.get_or_create(
            username=user_info['username'],
            defaults={
                'email': user_info.get('email', ''),
                'is_active': True
            }
        )
        
        # Log the user in
        login(request, user)
        messages.success(request, 'Successfully logged in!')
        return redirect('home')
        
    except Exception as e:
        messages.error(request, f'Authentication failed: {str(e)}')
        print(f"\n\n here is exception: {e} \n\n")
        return redirect('login')

def logout_view(request):
    logout(request)
    request.session.flush()
    messages.success(request, 'Successfully logged out!')
    return redirect('home')

@login_required
def profile(request):
    try:
        # Get user info from OAuth provider
        user_info = oauth_client.get_user_info(request.session['access_token'])
        return render(request, 'profile.html', {'user_info': user_info})
    except Exception as e:
        messages.error(request, f'Failed to get profile information: {str(e)}')
        return redirect('home')
