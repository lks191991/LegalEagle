from fastapi import APIRouter, Request, Form, Cookie, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from typing import Optional
import stripe
import os
from dotenv import load_dotenv
from db_operations import DatabaseOperations
from routes.auth import verify_user_session
from template_config import templates

load_dotenv()

# Configure Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY', 'sk_test_...')  # Add your Stripe secret key to .env

router = APIRouter()

@router.get("/subscribe/{plan_id}", response_class=HTMLResponse)
def subscribe_page(request: Request, plan_id: int, user_session: Optional[str] = Cookie(None)):
    """Subscription checkout page"""
    user_data = verify_user_session(user_session)
    if not user_data:
        return RedirectResponse(url="/login", status_code=302)
    
    # Get plan details
    plans = DatabaseOperations.get_all_plans()
    plan = next((p for p in plans if p['id'] == plan_id), None)
    
    if not plan:
        return RedirectResponse(url="/subscription", status_code=302)
    
    return templates.TemplateResponse("checkout.html", {
        "request": request,
        "user": user_data,
        "plan": plan,
        "stripe_public_key": os.getenv('STRIPE_PUBLIC_KEY', 'pk_test_...')  # Add to .env
    })

@router.post("/create-checkout-session")
async def create_checkout_session(
    request: Request,
    plan_id: int = Form(...),
    user_session: Optional[str] = Cookie(None)
):
    """Create Stripe checkout session"""
    user_data = verify_user_session(user_session)
    if not user_data:
        return JSONResponse({"error": "Not authenticated"}, status_code=401)
    
    try:
        # Get plan details
        plans = DatabaseOperations.get_all_plans()
        plan = next((p for p in plans if p['id'] == plan_id), None)
        
        if not plan:
            return JSONResponse({"error": "Plan not found"}, status_code=404)
        
        # Get full user data with address
        full_user_data = DatabaseOperations.get_user_by_id(user_data['user_id'])
        if not full_user_data:
            return JSONResponse({"error": "User not found"}, status_code=404)
        
        # Debug: Print user data to see what address fields we have
        print(f"DEBUG: Full user data: {full_user_data}")
        print(f"DEBUG: Address fields - Line1: {full_user_data.get('address_line1')}, City: {full_user_data.get('city')}, State: {full_user_data.get('state')}, Postal: {full_user_data.get('postal_code')}, Country: {full_user_data.get('country')}")
        
        # Create Stripe checkout session
        base_url = str(request.base_url).rstrip('/')
        
        # Prepare customer info and billing address
        customer_data = {
            'email': full_user_data['email'],
            'name': full_user_data['name']
        }
        
        # Build billing address if available
        billing_address = {}
        if full_user_data.get('address_line1') or full_user_data.get('city'):
            if full_user_data.get('address_line1'):
                billing_address['line1'] = full_user_data['address_line1']
            if full_user_data.get('address_line2'):
                billing_address['line2'] = full_user_data['address_line2']
            if full_user_data.get('city'):
                billing_address['city'] = full_user_data['city']
            if full_user_data.get('state'):
                billing_address['state'] = full_user_data['state']
            if full_user_data.get('postal_code'):
                billing_address['postal_code'] = full_user_data['postal_code']
            # Set default country to India if not specified
            country = full_user_data.get('country', 'India')
            if country.lower() == 'india':
                billing_address['country'] = 'IN'
            elif len(country) == 2:
                billing_address['country'] = country.upper()
            else:
                # Default to India for any other case
                billing_address['country'] = 'IN'
        
        # Add billing address to customer data if available
        if billing_address:
            customer_data['address'] = billing_address
            print(f"DEBUG: Billing address prepared: {billing_address}")
        else:
            print("DEBUG: No billing address data available for user")
        
        # Create or retrieve customer first to pre-fill address
        customer = None
        try:
            # Try to find existing customer by email
            customers = stripe.Customer.list(email=customer_data['email'], limit=1)
            if customers.data:
                customer = customers.data[0]
                # Update customer with latest info if needed
                if billing_address:
                    stripe.Customer.modify(
                        customer.id,
                        name=customer_data['name'],
                        address=billing_address
                    )
            else:
                # Create new customer with address
                create_data = {
                    'email': customer_data['email'],
                    'name': customer_data['name']
                }
                if billing_address:
                    create_data['address'] = billing_address
                customer = stripe.Customer.create(**create_data)
        except Exception as e:
            print(f"Customer creation/update error: {e}")
        
        # Create checkout session
        session_data = {
            'payment_method_types': ['card'],
            'line_items': [{
                'price_data': {
                    'currency': 'inr',
                    'product_data': {
                        'name': f'LegalEagle {plan["name"]} Plan',
                        'description': f'{plan["name"]} - Professional AI-powered legal document analysis and chat assistance for your practice',
                    },
                    'unit_amount': int(plan['price'] * 100),  # Stripe uses paise for INR
                    'recurring': {
                        'interval': 'month',
                    },
                },
                'quantity': 1,
            }],
            'mode': 'subscription',
            'success_url': f'{base_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}',
            'cancel_url': f'{base_url}/payment/cancel',
            'client_reference_id': user_data['user_id'],
            'metadata': {
                'user_id': user_data['user_id'],
                'plan_id': str(plan_id),
            },
            # Enhanced UX and branding
            'locale': 'en',
            'subscription_data': {
                'description': f'LegalEagle {plan["name"]} - AI Legal Assistant',
                'metadata': {
                    'plan_name': plan['name'],
                    'user_email': full_user_data['email'],
                    'subscription_type': 'monthly'
                }
            },
            # Custom UI text
            'custom_text': {
                'submit': {
                    'message': 'Complete your subscription to LegalEagle and transform your legal practice with AI-powered document analysis and intelligent chat assistance.'
                }
            }
        }
        
        # If we have address, set billing_address_collection to auto (uses customer's saved address)
        # Otherwise require it to be filled manually
        if billing_address and customer:
            session_data['billing_address_collection'] = 'auto'
            print("DEBUG: Using auto billing address collection with customer's saved address")
        else:
            session_data['billing_address_collection'] = 'required'
            print("DEBUG: Requiring manual billing address input")
        
        # Add customer if created successfully
        if customer:
            session_data['customer'] = customer.id
            print(f"DEBUG: Using existing customer: {customer.id}")
        else:
            session_data['customer_email'] = customer_data['email']
            # Create customer during checkout if we have address
            if billing_address:
                session_data['customer_creation'] = 'always'
        
        # customer_details is not supported in checkout sessions
        # Address will be pre-filled through the customer record
        print("DEBUG: Address will be pre-filled through customer record")
        
        print(f"DEBUG: Creating checkout session with data: {session_data}")
        checkout_session = stripe.checkout.Session.create(**session_data)
        
        return JSONResponse({"checkout_url": checkout_session.url})
        
    except Exception as e:
        print(f"ERROR: Checkout session creation failed: {str(e)}")
        import traceback
        print(f"TRACEBACK: {traceback.format_exc()}")
        return JSONResponse({"error": str(e)}, status_code=500)

@router.get("/payment/success", response_class=HTMLResponse)
def payment_success(request: Request, session_id: str, user_session: Optional[str] = Cookie(None)):
    """Payment success page"""
    user_data = verify_user_session(user_session)
    if not user_data:
        return RedirectResponse(url="/login", status_code=302)
    
    try:
        # Retrieve the checkout session
        session = stripe.checkout.Session.retrieve(session_id)
        
        # Save subscription to database
        from datetime import datetime, timedelta
        start_date = datetime.now().strftime('%Y-%m-%d')
        end_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        
        DatabaseOperations.create_user_subscription(
            user_id=int(user_data['user_id']),
            plan_id=int(session.metadata['plan_id']),
            start_date=start_date,
            end_date=end_date,
            stripe_session_id=session_id
        )
        
        # Create user plan with limits
        DatabaseOperations.create_user_plan(
            user_id=int(user_data['user_id']),
            plan_id=int(session.metadata['plan_id']),
            plan_type='paid'
        )
        
        # Create transaction record
        plan_id = int(session.metadata['plan_id'])
        plans = DatabaseOperations.get_all_plans()
        plan = next((p for p in plans if p['id'] == plan_id), None)
        if plan:
            DatabaseOperations.create_transaction(
                user_id=int(user_data['user_id']),
                plan_id=plan_id,
                amount=float(plan['price']),
                status='completed',
                stripe_session_id=session_id
            )
        
        return templates.TemplateResponse("payment_success.html", {
            "request": request,
            "user": user_data,
            "session": session,
            "plan": plan
        })
        
    except Exception as e:
        return templates.TemplateResponse("payment_error.html", {
            "request": request,
            "user": user_data,
            "error": str(e)
        })

@router.get("/payment/cancel", response_class=HTMLResponse)
def payment_cancel(request: Request, user_session: Optional[str] = Cookie(None)):
    """Payment cancelled page"""
    user_data = verify_user_session(user_session)
    if not user_data:
        return RedirectResponse(url="/login", status_code=302)
    
    return templates.TemplateResponse("payment_cancel.html", {
        "request": request,
        "user": user_data
    })

@router.post("/stripe-webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    endpoint_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        return JSONResponse({"error": "Invalid payload"}, status_code=400)
    except stripe.error.SignatureVerificationError:
        return JSONResponse({"error": "Invalid signature"}, status_code=400)
    
    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Handle successful payment
        if session.metadata and session.metadata.get('user_id'):
            user_id = int(session.metadata['user_id'])
            plan_id = int(session.metadata['plan_id'])
            
            # Create subscription
            from datetime import datetime, timedelta
            start_date = datetime.now().strftime('%Y-%m-%d')
            end_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            
            DatabaseOperations.create_user_subscription(
                user_id=user_id,
                plan_id=plan_id,
                start_date=start_date,
                end_date=end_date
            )
        
    elif event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        
        # Handle recurring payment - extend subscription
        if invoice.subscription:
            # Find and update subscription end date
            pass
        
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        
        # Handle subscription cancellation
        if subscription.metadata and subscription.metadata.get('user_id'):
            user_id = int(subscription.metadata['user_id'])
            # Find and cancel user's subscription
            pass
    
    return JSONResponse({"status": "success"})