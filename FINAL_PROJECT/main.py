from fastapi import FastAPI, HTTPException, Query, Response, status
from pydantic import BaseModel, Field
from typing import Optional, List
from math import ceil

app = FastAPI(title="CineStar Movie Booking API")

# --- DATA MODELS (Q2, Q4, Q14) ---
movies = [
    {"id": 1, "title": "Inception", "genre": "Sci-Fi", "language": "English", "duration_mins": 148, "ticket_price": 250, "seats_available": 50},
    {"id": 2, "title": "Kantara", "genre": "Action", "language": "Kannada", "duration_mins": 150, "ticket_price": 200, "seats_available": 30},
    {"id": 3, "title": "The Conjuring", "genre": "Horror", "language": "English", "duration_mins": 112, "ticket_price": 180, "seats_available": 15},
    {"id": 4, "title": "Parasite", "genre": "Drama", "language": "Korean", "duration_mins": 132, "ticket_price": 220, "seats_available": 10},
    {"id": 5, "title": "RRR", "genre": "Action", "language": "Telugu", "duration_mins": 187, "ticket_price": 300, "seats_available": 5},
    {"id": 6, "title": "Stree 2", "genre": "Comedy", "language": "Hindi", "duration_mins": 147, "ticket_price": 240, "seats_available": 25},
]

bookings = []
holds = []
booking_counter = 1
hold_counter = 1

# --- PYDANTIC MODELS (Q6, Q9, Q11, Q15) ---
class BookingRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    movie_id: int = Field(..., gt=0)
    seats: int = Field(..., gt=0, le=10)
    phone: str = Field(..., min_length=10)
    seat_type: str = "standard"  # standard, premium, recliner
    promo_code: Optional[str] = ""

class NewMovie(BaseModel):
    title: str = Field(..., min_length=2)
    genre: str = Field(..., min_length=2)
    language: str = Field(..., min_length=2)
    duration_mins: int = Field(..., gt=0)
    ticket_price: int = Field(..., gt=0)
    seats_available: int = Field(..., gt=0)

class SeatHoldRequest(BaseModel):
    customer_name: str
    movie_id: int
    seats: int

class CheckoutRequest(BaseModel):
    customer_name: str
    phone: str

# --- HELPER FUNCTIONS (Q7, Q10) ---
def find_movie(movie_id: int):
    return next((m for m in movies if m["id"] == movie_id), None)

def calculate_ticket_cost(base_price: int, seats: int, seat_type: str, promo: str = ""):
    multiplier = {"standard": 1.0, "premium": 1.5, "recliner": 2.0}
    total = base_price * seats * multiplier.get(seat_type.lower(), 1.0)
    
    discount = 0
    if promo == "SAVE10": discount = total * 0.10
    elif promo == "SAVE20": discount = total * 0.20
    
    return {"original": total, "discount": discount, "final": total - discount}

# --- ROUTES (Q1 - Q20) ---

@app.get("/")  # Q1
def home():
    return {"message": "Welcome to CineStar Booking"}

@app.get("/movies")  # Q2
def get_all_movies():
    total_seats = sum(m["seats_available"] for m in movies)
    return {"movies": movies, "total": len(movies), "total_seats_available": total_seats}

@app.get("/movies/summary")  # Q5 (Fixed route above variable)
def get_movies_summary():
    prices = [m["ticket_price"] for m in movies]
    genres = [m["genre"] for m in movies]
    return {
        "total_movies": len(movies),
        "most_expensive": max(prices) if prices else 0,
        "cheapest": min(prices) if prices else 0,
        "total_seats": sum(m["seats_available"] for m in movies),
        "genre_breakdown": {g: genres.count(g) for g in set(genres)}
    }

@app.get("/movies/search")  # Q16
def search_movies(keyword: str):
    results = [m for m in movies if keyword.lower() in m["title"].lower() or 
               keyword.lower() in m["genre"].lower() or keyword.lower() in m["language"].lower()]
    if not results:
        return {"message": f"No movies found for '{keyword}'"}
    return {"results": results, "total_found": len(results)}

@app.get("/movies/sort")  # Q17
def sort_movies(sort_by: str = "ticket_price", order: str = "asc"):
    if sort_by not in ["ticket_price", "title", "duration_mins", "seats_available"]:
        raise HTTPException(status_code=400, detail="Invalid sort field")
    
    reverse = True if order == "desc" else False
    sorted_list = sorted(movies, key=lambda x: x[sort_by], reverse=reverse)
    return {"sorted_by": sort_by, "order": order, "results": sorted_list}

@app.get("/movies/page")  # Q18
def paginate_movies(page: int = Query(1, ge=1), limit: int = Query(3, ge=1, le=10)):
    start = (page - 1) * limit
    end = start + limit
    total_pages = ceil(len(movies) / limit)
    return {
        "page": page,
        "limit": limit,
        "total": len(movies),
        "total_pages": total_pages,
        "results": movies[start:end]
    }

@app.get("/movies/filter")  # Q10
def filter_movies(
    genre: Optional[str] = None, 
    language: Optional[str] = None, 
    max_price: Optional[int] = None, 
    min_seats: Optional[int] = None
):
    filtered = movies
    if genre: filtered = [m for m in filtered if m["genre"].lower() == genre.lower()]
    if language: filtered = [m for m in filtered if m["language"].lower() == language.lower()]
    if max_price: filtered = [m for m in filtered if m["ticket_price"] <= max_price]
    if min_seats: filtered = [m for m in filtered if m["seats_available"] >= min_seats]
    return {"results": filtered, "count": len(filtered)}

@app.get("/movies/browse")  # Q20
def browse_movies(
    keyword: Optional[str] = None,
    genre: Optional[str] = None,
    sort_by: str = "ticket_price",
    order: str = "asc",
    page: int = 1,
    limit: int = 3
):
    # Filter
    data = movies
    if keyword: data = [m for m in data if keyword.lower() in m["title"].lower()]
    if genre: data = [m for m in data if m["genre"].lower() == genre.lower()]
    
    # Sort
    reverse = (order == "desc")
    data = sorted(data, key=lambda x: x.get(sort_by, "ticket_price"), reverse=reverse)
    
    # Paginate
    start = (page - 1) * limit
    return {"results": data[start:start+limit], "metadata": {"page": page, "total": len(data)}}

@app.get("/movies/{movie_id}")  # Q3 (Variable route at bottom)
def get_movie_by_id(movie_id: int):
    movie = find_movie(movie_id)
    if not movie:
        return {"error": "Movie not found"}
    return movie

@app.post("/movies", status_code=201)  # Q11
def add_movie(movie_data: NewMovie):
    if any(m["title"].lower() == movie_data.title.lower() for m in movies):
        raise HTTPException(status_code=400, detail="Movie already exists")
    new_id = movies[-1]["id"] + 1 if movies else 1
    movie_dict = {"id": new_id, **movie_data.dict()}
    movies.append(movie_dict)
    return movie_dict

@app.put("/movies/{movie_id}")  # Q12
def update_movie(movie_id: int, ticket_price: Optional[int] = None, seats_available: Optional[int] = None):
    movie = find_movie(movie_id)
    if not movie: raise HTTPException(status_code=404, detail="Movie not found")
    if ticket_price is not None: movie["ticket_price"] = ticket_price
    if seats_available is not None: movie["seats_available"] = seats_available
    return movie

@app.delete("/movies/{movie_id}")  # Q13
def delete_movie(movie_id: int):
    movie = find_movie(movie_id)
    if not movie: raise HTTPException(status_code=404, detail="Movie not found")
    if any(b["movie_id"] == movie_id for b in bookings):
        raise HTTPException(status_code=400, detail="Cannot delete movie with active bookings")
    movies.remove(movie)
    return {"message": f"Deleted {movie['title']}"}

# --- BOOKING & WORKFLOW (Q4, Q8, Q14, Q15, Q19) ---

@app.get("/bookings")  # Q4
def get_all_bookings():
    revenue = sum(b["total_cost"] for b in bookings)
    return {"bookings": bookings, "total": len(bookings), "total_revenue": revenue}

@app.get("/bookings/search")  # Q19
def search_bookings(customer_name: str):
    res = [b for b in bookings if customer_name.lower() in b["customer_name"].lower()]
    return {"results": res}

@app.post("/bookings")  # Q8
def create_booking(req: BookingRequest):
    movie = find_movie(req.movie_id)
    if not movie: raise HTTPException(status_code=404, detail="Movie not found")
    if movie["seats_available"] < req.seats:
        raise HTTPException(status_code=400, detail="Not enough seats available")
    
    costs = calculate_ticket_cost(movie["ticket_price"], req.seats, req.seat_type, req.promo_code)
    movie["seats_available"] -= req.seats
    
    global booking_counter
    new_booking = {
        "booking_id": booking_counter,
        "movie_title": movie["title"],
        **req.dict(),
        "total_cost": costs["final"]
    }
    bookings.append(new_booking)
    booking_counter += 1
    return new_booking

@app.post("/seat-hold")  # Q14
def hold_seats(req: SeatHoldRequest):
    movie = find_movie(req.movie_id)
    if not movie or movie["seats_available"] < req.seats:
        raise HTTPException(status_code=400, detail="Unavailable")
    
    global hold_counter
    movie["seats_available"] -= req.seats
    hold = {"hold_id": hold_counter, **req.dict()}
    holds.append(hold)
    hold_counter += 1
    return hold

@app.post("/seat-confirm/{hold_id}")  # Q15
def confirm_hold(hold_id: int):
    hold = next((h for h in holds if h["hold_id"] == hold_id), None)
    if not hold: raise HTTPException(status_code=404)
    
    global booking_counter
    movie = find_movie(hold["movie_id"])
    new_booking = {
        "booking_id": booking_counter,
        "customer_name": hold["customer_name"],
        "movie_title": movie["title"],
        "seats": hold["seats"],
        "total_cost": movie["ticket_price"] * hold["seats"]
    }
    bookings.append(new_booking)
    holds.remove(hold)
    booking_counter += 1
    return {"status": "Confirmed", "booking": new_booking}

@app.delete("/seat-release/{hold_id}")  # Q15
def release_hold(hold_id: int):
    hold = next((h for h in holds if h["hold_id"] == hold_id), None)
    if not hold: raise HTTPException(status_code=404)
    movie = find_movie(hold["movie_id"])
    movie["seats_available"] += hold["seats"]
    holds.remove(hold)
    return {"message": "Seats released"}