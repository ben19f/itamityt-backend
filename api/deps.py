# from fastapi import Depends, HTTPException
# from jose import jwt, JWTError
# from sqlalchemy.orm import Session
# from fastapi.security import OAuth2PasswordBearer
#
# from db.session import get_db
# from models.user import User
# # from core.security import SECRET_KEY, ALGORITHM
# from core.config import settings


# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# def get_current_user(
#     token: str = Depends(oauth2_scheme),
#     db: Session = Depends(get_db)
# ):
#
#     try:
#
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         email = payload.get("sub")
#
#     except JWTError:
#
#         raise HTTPException(status_code=401, detail="Invalid token")
#
#     user = db.query(User).filter(User.email == email).first()
#
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#
#     return user


# async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
#     try:
#         payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
#         email: str = payload.get("sub")
#         if email is None:
#             raise HTTPException(status_code=401, detail="Invalid authentication")
#     except Exception:
#         raise HTTPException(status_code=401, detail="Invalid authentication")
#
#     user = await get_user_by_email(db, email)
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#     return user
