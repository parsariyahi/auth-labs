from fastapi import APIRouter, Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# from service.models.schemas import Token, UserCreate, UserResponse
# from service.database.operations import get_user_by_username, create_user
# from service.utils.security import (
#     verify_password,
#     create_access_token,
#     create_refresh_token,
#     get_current_user,
#     get_password_hash
# )
# from datetime import timedelta


router = APIRouter(prefix="/auth", tags=["authentication"])


# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# @router.post("/register", response_model=UserResponse)
# async def register(user: UserCreate):
#     db_user = get_user_by_username(user.username)
#     if db_user:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Username already registered"
#         )
    
#     hashed_password = get_password_hash(user.password)
#     user_id = create_user(
#         username=user.username,
#         hashed_password=hashed_password,
#         email=user.email,
#         full_name=user.full_name
#     )
    
#     return {
#         "id": user_id,
#         "username": user.username,
#         "email": user.email,
#         "full_name": user.full_name
#     }

# @router.post("/token", response_model=Token)
# async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
#     user = get_user_by_username(form_data.username)
#     if not user or not verify_password(form_data.password, user["hashed_password"]):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect username or password",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
    
#     access_token_expires = timedelta(minutes=30)
#     access_token = create_access_token(
#         data={"sub": user["username"]}, expires_delta=access_token_expires
#     )
    
#     refresh_token = create_refresh_token(data={"sub": user["username"]})
    
#     return {
#         "access_token": access_token,
#         "refresh_token": refresh_token,
#         "token_type": "bearer"
#     }

# @router.post("/refresh", response_model=Token)
# async def refresh_token(current_user: dict = Depends(get_current_user)):
#     access_token_expires = timedelta(minutes=30)
#     access_token = create_access_token(
#         data={"sub": current_user["username"]}, expires_delta=access_token_expires
#     )
    
#     refresh_token = create_refresh_token(data={"sub": current_user["username"]})
    
#     return {
#         "access_token": access_token,
#         "refresh_token": refresh_token,
#         "token_type": "bearer"
#     }

# @router.get("/me", response_model=UserResponse)
# async def read_users_me(current_user: dict = Depends(get_current_user)):
#     return current_user 