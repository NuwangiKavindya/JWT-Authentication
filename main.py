from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.concurrency import run_in_threadpool
from database import user_collection
from auth_utils import get_password_hash, create_access_token, verify_password
from s3_utils import upload_file_to_s3

app = FastAPI()

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.detail, "data": None}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"success": False, "message": "Validation error", "data": exc.errors()}
    )

@app.get("/")
async def root():
    return RedirectResponse(url="/docs")

@app.post("/register")
async def register_user(
    username: str = Form(...), 
    email: str = Form(...),
    password: str = Form(...), 
    profile_pic: UploadFile = File(...)
):
    existing_user = await user_collection.find_one({
        "$or": [{"username": username}, {"email": email}]
    })
    if existing_user:
        if existing_user.get("username") == username:
            raise HTTPException(status_code=400, detail="Username already taken")
        else:
            raise HTTPException(status_code=400, detail="Email already registered")

    image_url = await run_in_threadpool(upload_file_to_s3, profile_pic)
    if not image_url:
        raise HTTPException(status_code=500, detail="Image upload failed")

    hashed_password = get_password_hash(password)
    new_user = {
        "username": username,
        "email": email,
        "password": hashed_password,
        "profile_image": image_url
    }
    await user_collection.insert_one(new_user)
    
    return {
        "success": True,
        "message": "User registered successfully",
        "data": {
            "username": username,
            "email": email,
            "profile_image": image_url
        }
    }

@app.post("/login")
async def login(
    username: str = Form(None), 
    email: str = Form(None),
    password: str = Form(...)
):
    if not username and not email:
        raise HTTPException(status_code=400, detail="Please provide either username or email")
        
    search_query = []
    if username:
        search_query.append({"username": username})
    if email:
        search_query.append({"email": email})

    user = await user_collection.find_one({
        "$or": search_query
    })
    
    if not user or not verify_password(password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token(data={"sub": user["username"]})
    
    user_details = {
        "username": user.get("username"),
        "email": user.get("email"),
        "profile_image": user.get("profile_image")
    }
    
    return {
        "success": True,
        "message": "Login successful",
        "data": {
            "access_token": token,
            "token_type": "bearer",
            "user": user_details
        }
    }