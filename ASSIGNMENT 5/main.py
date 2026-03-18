from fastapi import FastAPI, Query, Response, status
from typing import Optional
from pydantic import BaseModel, Field

app = FastAPI()

# ══ MODELS ════════════════════════════════════════════════════════
class OrderRequest(BaseModel):
    customer_name:    str = Field(..., min_length=2, max_length=100)
    product_id:       int = Field(..., gt=0)
    quantity:         int = Field(..., gt=0, le=100)
    delivery_address: str = Field(..., min_length=10)

class NewProduct(BaseModel):
    name:     str  = Field(..., min_length=2, max_length=100)
    price:    int  = Field(..., gt=0)
    category: str  = Field(..., min_length=2)
    in_stock: bool = True

class CheckoutRequest(BaseModel):
    customer_name:    str = Field(..., min_length=2)
    delivery_address: str = Field(..., min_length=10)

# ══ DATA ══════════════════════════════════════════════════════════
products = [
    {'id': 1, 'name': 'Wireless Mouse', 'price': 499, 'category': 'Electronics', 'in_stock': True},
    {'id': 2, 'name': 'Notebook',        'price':  99, 'category': 'Stationery',  'in_stock': True},
    {'id': 3, 'name': 'USB Hub',         'price': 799, 'category': 'Electronics', 'in_stock': False},
    {'id': 4, 'name': 'Pen Set',         'price':  49, 'category': 'Stationery',  'in_stock': True},
]

orders        = []
order_counter = 1
cart          = []

# ══ HELPERS ═══════════════════════════════════════════════════════
def find_product(product_id: int):
    for p in products:
        if p['id'] == product_id:
            return p
    return None

# ══ DAY 6 NEW ENDPOINTS (Q4, Q5, Q6) ══════════════════════════════

# Q4: Search Orders by Customer Name
@app.get("/orders/search")
def search_orders(customer_name: str = Query(..., description="Name of the customer to search for")):
    results = [o for o in orders if customer_name.lower() in o["customer_name"].lower()]
    if not results:
        return {"message": f"No orders found for: {customer_name}"}
    return {"customer_name": customer_name, "total_found": len(results), "orders": results}

# Q5: Sort Products by Category Then Price
@app.get("/products/sort-by-category")
def sort_by_category():
    # Sorts by category (A-Z) then price (Low-High)
    sorted_data = sorted(products, key=lambda p: (p['category'], p['price']))
    return {"products": sorted_data, "total": len(sorted_data)}

# Q6: Combine Search, Sort, and Paginate
@app.get("/products/browse")
def browse_products(
    keyword: Optional[str] = Query(None),
    sort_by: str = Query('price', regex="^(price|name)$"),
    order:   str = Query('asc', regex="^(asc|desc)$"),
    page:    int = Query(1, ge=1),
    limit:   int = Query(4, ge=1)
):
    # 1. Filter by keyword
    result = products
    if keyword:
        result = [p for p in result if keyword.lower() in p['name'].lower()]
    
    # 2. Sort results
    reverse_sort = (order == 'desc')
    result = sorted(result, key=lambda p: p[sort_by], reverse=reverse_sort)
    
    # 3. Paginate sorted results
    total = len(result)
    start = (page - 1) * limit
    paged_result = result[start : start + limit]
    
    return {
        "keyword": keyword,
        "sort_by": sort_by,
        "order": order,
        "total_found": total,
        "total_pages": -(-total // limit), # Ceiling division
        "products": paged_result
    }

# ⭐ Bonus: Paginate the Orders List
@app.get("/orders/page")
def get_orders_paged(page: int = Query(1, ge=1), limit: int = Query(3, ge=1)):
    start = (page - 1) * limit
    return {
        "page": page,
        "limit": limit,
        "total": len(orders),
        "total_pages": -(-len(orders) // limit),
        "orders": orders[start : start + limit]
    }

# ══ EXISTING ENDPOINTS (Day 1 - Day 5) ════════════════════════════
@app.get('/')
def home():
    return {'message': 'Welcome to our E-commerce API'}

@app.get('/products/search')
def search_products(keyword: str = Query(...)):
    results = [p for p in products if keyword.lower() in p['name'].lower()]
    if not results:
        return {'message': f'No products found for: {keyword}'}
    return {'total_found': len(results), 'results': results}

@app.get('/products/sort')
def sort_products(sort_by: str = 'price', order: str = 'asc'):
    if sort_by not in ['price', 'name']:
        return {'error': "sort_by must be 'price' or 'name'"}
    reverse = (order == 'desc')
    sorted_products = sorted(products, key=lambda p: p[sort_by], reverse=reverse)
    return {'products': sorted_products}

@app.get('/products/page')
def get_products_paged_simple(page: int = 1, limit: int = 2):
    start = (page - 1) * limit
    return {"products": products[start : start + limit], "total_pages": -(-len(products) // limit)}

@app.get('/products/{product_id}')
def get_product(product_id: int):
    product = find_product(product_id)
    return product if product else {"error": "Product not found"}

@app.post('/orders')
def place_order(order_data: OrderRequest):
    global order_counter
    product = find_product(order_data.product_id)
    if not product or not product['in_stock']:
        return {"error": "Product unavailable"}
    order = {"order_id": order_counter, "customer_name": order_data.customer_name, "total_price": product['price'] * order_data.quantity}
    orders.append(order)
    order_counter += 1
    return order