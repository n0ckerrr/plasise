"""
IBD Global Automator - Adds products to cart on ibdglobal.com
Uses requests library for reliable HTTP-based automation.
Searches products by SKU code and adds specified quantities to cart.
"""
import os
import sys
import re
import time
from dotenv import load_dotenv
import requests
from html.parser import HTMLParser

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if not os.path.exists(env_path):
    env_path = os.path.join(os.path.dirname(__file__), '..', 'security-web', '.env')
if not os.path.exists(env_path):
    env_path = "/code/backend/.env"
load_dotenv(env_path)

IBD_USER = os.getenv("IBD_USER")
IBD_PASS = os.getenv("IBD_PASS")

LOGIN_URL = "https://www.ibdglobal.com/web/login"
SHOP_URL = "https://www.ibdglobal.com/en/shop"
CART_UPDATE_URL = "https://www.ibdglobal.com/en/shop/cart/update"
CART_URL = "https://www.ibdglobal.com/en/shop/cart"


def extract_csrf(html):
    """Extract CSRF token from HTML page."""
    match = re.search(r'name="csrf_token"\s+value="([^"]+)"', html)
    return match.group(1) if match else None


def extract_product_id(html):
    """Extract product_id from product detail page."""
    match = re.search(r'name="product_id"\s+value="(\d+)"', html)
    if not match:
        match = re.search(r'class="product_id"[^>]*value="(\d+)"', html)
    return match.group(1) if match else None


def extract_hidden_field(html, name):
    """Extract a hidden input field value by name or class."""
    match = re.search(r'name="' + re.escape(name) + r'"[^>]*value="([^"]+)"', html)
    if not match:
        match = re.search(r'class="' + re.escape(name) + r'"[^>]*value="([^"]+)"', html)
    return match.group(1) if match else None


def set_delivery_address(session, address):
    """
    Creates a new delivery address in IBD Global which is automatically
    selected for the current checkout session.
    
    Args:
        session: Active requests.Session object
        address: dict with name, phone, street, city, zip
    Returns:
        True if successful, False otherwise.
    """
    try:
        print(f"\n=== SETTING DELIVERY ADDRESS ===")
        print(f"Adding address for: {address.get('name')}")
        
        # We MUST get the CSRF token from the checkout page directly.
        # This signals Odoo that we are within the checkout wizard, so any 
        # new address with partner_id=-1 becomes the active checkout address.
        r = session.get("https://www.ibdglobal.com/shop/checkout")
        csrf_match = re.search(r'name="csrf_token"\s+value="([^"]+)"', r.text)
        
        if not csrf_match:
            print("ERROR: Could not find CSRF token on checkout page.")
            return False
            
        csrf = csrf_match.group(1)
        
        data = {
            'csrf_token': csrf,
            'name': address.get('name', 'Dropship Customer'),
            'phone': address.get('phone', ''),
            'street': address.get('street', ''),
            'city': address.get('city', ''),
            'zip': address.get('zip', ''),
            'country_id': "67",  # Spain by default
            'submitted': "1",
            'partner_id': "-1",  # Crucial: specifies "new address" for the cart
            'callback': ""
        }
        
        # Submit the address form
        r = session.post("https://www.ibdglobal.com/shop/address", data=data)
        
        # Verify if the redirect landed us further in the checkout process
        if r.status_code == 200 and "checkout" in r.url:
            print("SUCCESS: Delivery address created and selected (redirected to checkout).")
            return True
        elif "extra_info" in r.url or "payment" in r.url or "confirm_order" in r.url:
             print(f"SUCCESS: Delivery address created and selected (redirected to {r.url.split('/')[-1]}).")
             return True
        else:
            print(f"FAILED to set address. Redirected unexpectedly to: {r.url}")
            return False
            
    except Exception as e:
        print(f"ERROR setting delivery address: {e}")
        return False


def login_and_add_to_cart(products, address=None):
    """
    Login to IBD Global and add products to cart. Optionally creates a delivery address.
    
    Args:
        products: list of dicts with 'sku' and 'quantity' keys.
        address: optional dict with delivery address details.
    Returns:
        True if all products were added successfully, False otherwise.
    """
    if not IBD_USER or not IBD_PASS:
        print("ERROR: IBD_USER or IBD_PASS not set in environment.")
        return False

    session = requests.Session()
    
    try:
        # === LOGIN ===
        print(f"Navigating to {LOGIN_URL}...")
        r = session.get(LOGIN_URL)
        csrf = extract_csrf(r.text)
        
        if not csrf:
            print("ERROR: Could not find CSRF token on login page.")
            return False
        
        print("Logging in...")
        login_data = {
            'login': IBD_USER,
            'password': IBD_PASS,
            'csrf_token': csrf,
            'redirect': ''
        }
        r = session.post(LOGIN_URL, data=login_data)
        
        if "web/login" in r.url:
            print(f"ERROR: Login failed. Still on login page: {r.url}")
            return False
        
        print(f"Login successful. URL: {r.url}")
        
        # === ADD PRODUCTS TO CART ===
        added_count = 0
        for product in products:
            sku = product['sku']
            qty = product.get('quantity', 1)
            print(f"\n--- Processing: SKU={sku}, Qty={qty} ---")
            
            try:
                # Search for product by SKU
                search_url = f"{SHOP_URL}?search={sku}"
                print(f"  Searching: {search_url}")
                r = session.get(search_url)
                
                # Find product link in search results
                # Look for href containing the product slug
                product_links = re.findall(
                    r'href="(/en/shop/[^"?]+)\?search=' + re.escape(sku) + r'"',
                    r.text
                )
                
                if not product_links:
                    # Try without search param
                    product_links = re.findall(
                        r'class="o_product_link[^"]*"\s+href="(/en/shop/[^"]+)"',
                        r.text
                    )
                
                if not product_links:
                    print(f"  WARNING: No products found for SKU '{sku}'.")
                    continue
                
                # Take first unique link
                product_path = product_links[0]
                product_url = f"https://www.ibdglobal.com{product_path}"
                print(f"  Product found: {product_path}")
                
                # Load product detail page
                r = session.get(product_url)
                product_id = extract_product_id(r.text)
                csrf = extract_csrf(r.text)
                
                if not product_id:
                    print(f"  ERROR: Could not find product_id on detail page.")
                    continue
                
                if not csrf:
                    print(f"  ERROR: Could not find CSRF token on detail page.")
                    continue
                
                # Extract all hidden fields
                template_id = extract_hidden_field(r.text, 'product_template_id')
                category_id = extract_hidden_field(r.text, 'product_category_id')
                
                print(f"  product_id={product_id}, template_id={template_id}, category_id={category_id}")
                
                # POST to cart/update with all form fields
                cart_data = {
                    'product_id': product_id,
                    'add_qty': str(qty),
                    'csrf_token': csrf,
                }
                if template_id:
                    cart_data['product_template_id'] = template_id
                if category_id:
                    cart_data['product_category_id'] = category_id
                
                print(f"  POSTing to cart/update...")
                print(f"  POST data: {cart_data}")
                r = session.post(CART_UPDATE_URL, data=cart_data, allow_redirects=False)
                
                print(f"  POST response: status={r.status_code}")
                print(f"  Location header: {r.headers.get('Location', 'N/A')}")
                
                # Save POST response body
                with open(f"/tmp/ibd_post_response_{sku}.html", "w", encoding="utf-8") as f:
                    f.write(r.text[:5000])
                
                # Follow redirects manually
                if r.status_code in (301, 302, 303):
                    redirect_url = r.headers.get('Location', '')
                    if redirect_url:
                        if not redirect_url.startswith('http'):
                            redirect_url = f"https://www.ibdglobal.com{redirect_url}"
                        print(f"  Following redirect: {redirect_url}")
                        r = session.get(redirect_url)
                
                print(f"  Final URL: {r.url}")
                print(f"  Final status: {r.status_code}")
                if sku.lower() in r.text.lower() or product_id in r.text:
                    print(f"  SUCCESS: {sku} x{qty} confirmed in cart!")
                    added_count += 1
                elif "carrito está vacío" in r.text.lower() or "cart is empty" in r.text.lower():
                    print(f"  FAILED: Cart is still empty after adding {sku}.")
                else:
                    # Cart may have items but we can't find the SKU text
                    print(f"  UNCERTAIN: Cart has content but SKU not found in text. Checking...")
                    # Look for any product rows
                    if 'td_product_name' in r.text or 'o_cart_product' in r.text:
                        print(f"  SUCCESS (probable): Cart has product rows.")
                        added_count += 1
                    else:
                        print(f"  FAILED: No product rows found in cart.")
                
            except Exception as e:
                print(f"  ERROR processing {sku}: {e}")
        
        # === SUMMARY ===
        print(f"\n=== CART SUMMARY ===")
        print(f"Products requested: {len(products)}")
        print(f"Products added:     {added_count}")
        
        # === SET DELIVERY ADDRESS ===
        if address and added_count > 0:
            address_success = set_delivery_address(session, address)
            if not address_success:
                print("WARNING: Products were added, but setting the delivery address failed.")
        
        return added_count == len(products)
    
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        return False


if __name__ == "__main__":
    sample_products = [
        {'sku': 'KIT-VIDEOADVANCE-4', 'quantity': 1}
    ]
    sample_address = {
        'name': 'Test Customer',
        'phone': '600111222',
        'street': 'C/ Luna 123',
        'city': 'Madrid',
        'zip': '28001'
    }
    success = login_and_add_to_cart(sample_products, address=sample_address)
    sys.exit(0 if success else 1)
