"""Data Seeding Module for Contoso MCP Service

Provides startup data seeding for Cosmos DB backend. This module checks if
data exists in the containers and seeds sample data if needed.

This is designed to run at MCP server startup when:
- USE_COSMOSDB=true
- SEED_ON_STARTUP=true (optional, defaults to checking if containers are empty)

The seeding uses the managed identity of the MCP service, which already has
Cosmos DB Data Contributor role, avoiding the need for local user RBAC or
firewall configuration.
"""

import os
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger("mcp.data_seeding")

# ──────────────────────────────────  RNG SETUP  ──────────────────────────
SEED = 42
random.seed(SEED)

# Try to import Faker for data generation
try:
    from faker import Faker
    fake = Faker()
    fake.seed_instance(SEED)
    FAKER_AVAILABLE = True
except ImportError:
    fake = None
    FAKER_AVAILABLE = False
    logger.warning("Faker not available - using simplified data generation")

# ─────────────────────────────  GLOBALS  ─────────────────────────────────
BASE_DATE = datetime.now()

# Container names
CONTAINERS = {
    "customers": "Customers",
    "products": "Products",
    "subscriptions": "Subscriptions",
    "invoices": "Invoices",
    "payments": "Payments",
    "promotions": "Promotions",
    "security_logs": "SecurityLogs",
    "orders": "Orders",
    "support_tickets": "SupportTickets",
    "data_usage": "DataUsage",
    "service_incidents": "ServiceIncidents",
    "knowledge_documents": "KnowledgeDocuments"
}


def get_embedding(text: str) -> List[float]:
    """Get embedding from Azure OpenAI or return dummy zeros."""
    try:
        from openai import AzureOpenAI
        
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        
        if not api_key or not endpoint:
            return [0.0] * 1536
        
        client = AzureOpenAI(
            api_key=api_key,
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
            azure_endpoint=endpoint,
        )
        model = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002")
        text = text.replace("\n", " ")
        return client.embeddings.create(input=[text], model=model).data[0].embedding
    except Exception as e:
        logger.warning(f"Failed to get embedding: {e}")
        return [0.0] * 1536


def check_container_empty(database, container_name: str) -> bool:
    """Check if a container is empty."""
    try:
        container = database.get_container_client(container_name)
        # Try to read just one item
        items = list(container.query_items(
            query="SELECT TOP 1 c.id FROM c",
            enable_cross_partition_query=True
        ))
        return len(items) == 0
    except Exception as e:
        logger.warning(f"Error checking container {container_name}: {e}")
        return True  # Assume empty if we can't check


def needs_seeding(database) -> bool:
    """Check if database needs seeding by checking if Customers container is empty."""
    force_seed = os.getenv("FORCE_SEED", "false").lower() in ("true", "1", "yes", "on")
    if force_seed:
        logger.info("FORCE_SEED is enabled - will seed data")
        return True
    
    return check_container_empty(database, CONTAINERS["customers"])


def generate_products() -> List[Dict[str, Any]]:
    """Generate product catalog."""
    products = [
        {
            "id": "1",
            "product_id": 1,
            "name": "Fiber Internet - Basic",
            "category": "internet",
            "description": "100 Mbps fiber internet for basic needs",
            "monthly_fee": 49.99,
            "price_monthly": 49.99,
            "speed_tier": "100Mbps",
            "data_cap_gb": 500,
            "features": ["WiFi Router", "24/7 Support"],
            "active": True
        },
        {
            "id": "2",
            "product_id": 2,
            "name": "Fiber Internet - Pro",
            "category": "internet",
            "description": "500 Mbps fiber internet for power users",
            "monthly_fee": 79.99,
            "price_monthly": 79.99,
            "speed_tier": "500Mbps",
            "data_cap_gb": 1000,
            "features": ["WiFi 6 Router", "24/7 Priority Support", "Static IP"],
            "active": True
        },
        {
            "id": "3",
            "product_id": 3,
            "name": "Fiber Internet - Ultimate",
            "category": "internet",
            "description": "1 Gbps fiber internet - no limits",
            "monthly_fee": 119.99,
            "price_monthly": 119.99,
            "speed_tier": "1Gbps",
            "data_cap_gb": -1,  # unlimited
            "features": ["WiFi 6E Router", "24/7 VIP Support", "Static IP", "Gaming Priority"],
            "active": True
        },
        {
            "id": "4",
            "product_id": 4,
            "name": "Mobile Plan - Essential",
            "category": "mobile",
            "description": "5GB data with unlimited calls/texts",
            "monthly_fee": 29.99,
            "price_monthly": 29.99,
            "data_cap_gb": 5,
            "features": ["Unlimited Calls", "Unlimited Texts", "5G Access"],
            "active": True
        },
        {
            "id": "5",
            "product_id": 5,
            "name": "Mobile Plan - Premium",
            "category": "mobile",
            "description": "Unlimited data with premium features",
            "monthly_fee": 59.99,
            "price_monthly": 59.99,
            "data_cap_gb": -1,
            "features": ["Unlimited Data", "International Roaming", "5G Priority", "Hotspot 50GB"],
            "active": True
        },
        {
            "id": "6",
            "product_id": 6,
            "name": "TV Streaming - Basic",
            "category": "tv",
            "description": "50+ channels streaming package",
            "monthly_fee": 34.99,
            "price_monthly": 34.99,
            "features": ["50+ Channels", "2 Screens", "7-Day Replay"],
            "active": True
        },
        {
            "id": "7",
            "product_id": 7,
            "name": "TV Streaming - Premium",
            "category": "tv",
            "description": "150+ channels with sports and movies",
            "monthly_fee": 64.99,
            "price_monthly": 64.99,
            "features": ["150+ Channels", "4 Screens", "30-Day Replay", "Sports Package", "Movie Channels"],
            "active": True
        },
        {
            "id": "8",
            "product_id": 8,
            "name": "Home Security - Basic",
            "category": "security",
            "description": "Basic home security monitoring",
            "monthly_fee": 19.99,
            "price_monthly": 19.99,
            "features": ["24/7 Monitoring", "2 Sensors", "Mobile App"],
            "active": True
        },
        {
            "id": "9",
            "product_id": 9,
            "name": "Bundle - Family Complete",
            "category": "bundle",
            "description": "Internet Pro + TV Premium + 2 Mobile lines",
            "monthly_fee": 199.99,
            "price_monthly": 199.99,
            "features": ["500Mbps Internet", "150+ TV Channels", "2 Unlimited Mobile Lines", "20% Discount"],
            "active": True
        },
        {
            "id": "10",
            "product_id": 10,
            "name": "Business Internet - Enterprise",
            "category": "business",
            "description": "Dedicated fiber for business",
            "monthly_fee": 299.99,
            "price_monthly": 299.99,
            "speed_tier": "10Gbps",
            "features": ["Dedicated Line", "SLA 99.99%", "24/7 Business Support", "Static IP Block"],
            "active": True
        }
    ]
    return products


def generate_promotions() -> List[Dict[str, Any]]:
    """Generate active promotions.
    
    Schema must match Pydantic model:
    - promotion_id: int (required)
    - product_id: int (required)
    - name: str
    - description: str
    - eligibility_criteria: Optional[str]
    - start_date: str
    - end_date: str
    - discount_percent: Optional[int]
    """
    today = datetime.now()
    promotions = [
        {
            "id": "1",
            "promotion_id": 1,
            "product_id": 1,  # Fiber Internet - Basic
            "name": "New Customer - 20% Off First 3 Months",
            "description": "Get 20% off your first 3 months on any internet plan",
            "eligibility_criteria": "new_customer = true",
            "discount_percent": 20,
            "start_date": (today - timedelta(days=30)).isoformat(),
            "end_date": (today + timedelta(days=60)).isoformat(),
            "active": True
        },
        {
            "id": "2",
            "promotion_id": 2,
            "product_id": 9,  # Bundle Package
            "name": "Bundle & Save - $50/month off",
            "description": "Save $50/month when you bundle 3+ services",
            "eligibility_criteria": "min_services >= 3",
            "discount_percent": 15,
            "start_date": (today - timedelta(days=15)).isoformat(),
            "end_date": (today + timedelta(days=90)).isoformat(),
            "active": True
        },
        {
            "id": "3",
            "promotion_id": 3,
            "product_id": 2,  # Fiber Internet - Pro
            "name": "Loyalty Reward - Free Upgrade",
            "description": "Gold/Platinum members: Free speed upgrade for 12 months",
            "eligibility_criteria": "loyalty_level = 'Gold' OR loyalty_level = 'Platinum'",
            "discount_percent": 100,
            "start_date": (today - timedelta(days=7)).isoformat(),
            "end_date": (today + timedelta(days=180)).isoformat(),
            "active": True
        },
        {
            "id": "4",
            "promotion_id": 4,
            "product_id": 5,  # Mobile Plan - Premium
            "name": "Refer a Friend - $100 Credit",
            "description": "Get $100 credit when you refer a friend who signs up",
            "eligibility_criteria": "referral = true",
            "discount_percent": 10,
            "start_date": today.isoformat(),
            "end_date": (today + timedelta(days=365)).isoformat(),
            "active": True
        }
    ]
    return promotions


def generate_knowledge_base() -> List[Dict[str, Any]]:
    """Generate knowledge base documents."""
    documents = [
        {
            "id": "KB001",
            "title": "How to Reset Your Router",
            "doc_type": "troubleshooting",
            "category": "troubleshooting",
            "content": """To reset your router:
1. Locate the reset button on the back of your router
2. Use a paperclip to press and hold the button for 10 seconds
3. Wait for the router to restart (lights will blink)
4. Your router will return to factory settings
5. Reconnect using the default WiFi name and password on the router label

If issues persist, contact support at 1-800-CONTOSO.""",
            "tags": ["router", "reset", "wifi", "troubleshooting"],
            "last_updated": datetime.now().isoformat()
        },
        {
            "id": "KB002",
            "title": "Understanding Your Bill",
            "doc_type": "billing",
            "category": "billing",
            "content": """Your monthly bill includes:
- Monthly service charges for each active subscription
- Any one-time charges (equipment, installation)
- Taxes and regulatory fees
- Credits or adjustments

Payment is due by the date shown on your bill. Enable autopay to never miss a payment and get a $5 monthly discount.

View your bill online at myaccount.contoso.com or in the Contoso mobile app.""",
            "tags": ["billing", "payment", "charges", "autopay"],
            "last_updated": datetime.now().isoformat()
        },
        {
            "id": "KB003",
            "title": "Upgrading Your Internet Speed",
            "doc_type": "services",
            "category": "services",
            "content": """To upgrade your internet speed:
1. Log in to your account at myaccount.contoso.com
2. Go to Services > Internet
3. Click 'Upgrade Plan'
4. Select your new speed tier
5. Review the price change and confirm

Speed upgrades typically take effect within 24 hours. You may need to restart your router for the change to apply.

Call us at 1-800-CONTOSO for special upgrade offers.""",
            "tags": ["internet", "upgrade", "speed", "plans"],
            "last_updated": datetime.now().isoformat()
        },
        {
            "id": "KB004",
            "title": "Account Security Best Practices",
            "doc_type": "security",
            "category": "security",
            "content": """Protect your account:
- Use a strong, unique password
- Enable two-factor authentication
- Never share your login credentials
- Monitor your account for suspicious activity
- Update your password every 90 days

If you suspect unauthorized access, call our security line immediately at 1-800-CONTOSO-SEC.

We will NEVER ask for your password via email or phone.""",
            "tags": ["security", "password", "2fa", "account"],
            "last_updated": datetime.now().isoformat()
        },
        {
            "id": "KB005",
            "title": "International Roaming Guide",
            "doc_type": "mobile",
            "category": "mobile",
            "content": """Before traveling internationally:
1. Check if your plan includes international roaming
2. Add a travel pass if needed ($10/day unlimited in 100+ countries)
3. Download offline content before you go
4. Use WiFi when available to save data

Premium mobile plans include free roaming in 50+ countries.

Visit contoso.com/travel for country-specific information and rates.""",
            "tags": ["mobile", "roaming", "international", "travel"],
            "last_updated": datetime.now().isoformat()
        }
    ]
    
    # Add embeddings to documents
    for doc in documents:
        text_for_embedding = f"{doc['title']} {doc['content']}"
        doc["content_vector"] = get_embedding(text_for_embedding)
    
    return documents


def generate_customers_and_related(num_customers: int = 50) -> Dict[str, List[Dict[str, Any]]]:
    """Generate customers with subscriptions, invoices, orders, etc."""
    customers = []
    subscriptions = []
    invoices = []
    payments = []
    orders = []
    support_tickets = []
    data_usage = []
    security_logs = []
    service_incidents = []
    
    loyalty_levels = ["Bronze", "Silver", "Gold", "Platinum"]
    statuses = ["active", "suspended", "cancelled"]
    service_statuses = ["normal", "slow", "offline"]  # Must match SQLite backend expectations
    
    products = generate_products()
    product_ids = [p["id"] for p in products]
    
    for i in range(1, num_customers + 1):
        customer_id = i
        
        # Generate customer
        if FAKER_AVAILABLE:
            first_name = fake.first_name()
            last_name = fake.last_name()
            email = f"{first_name.lower()}.{last_name.lower()}@{fake.domain_name()}"
            phone = fake.phone_number()
            address = fake.address().replace("\n", ", ")
        else:
            first_name = f"Customer{i}"
            last_name = f"User{i}"
            email = f"customer{i}@example.com"
            phone = f"+1-555-{i:04d}"
            address = f"{i} Main Street, City {i}, ST {10000 + i}"
        
        customer = {
            "id": str(customer_id),
            "customer_id": customer_id,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone,
            "address": address,
            "loyalty_level": random.choice(loyalty_levels),
            "account_status": "active" if random.random() > 0.1 else "locked",
            "created_date": (BASE_DATE - timedelta(days=random.randint(30, 730))).isoformat(),
            "preferences": {
                "email_notifications": random.choice([True, False]),
                "sms_notifications": random.choice([True, False]),
                "paperless_billing": random.choice([True, False])
            }
        }
        customers.append(customer)
        
        # Generate 1-3 subscriptions per customer
        num_subs = random.randint(1, 3)
        for j in range(num_subs):
            sub_id = len(subscriptions) + 1
            product = random.choice(products)
            start_date = BASE_DATE - timedelta(days=random.randint(30, 365))
            # Calculate end_date: active subs have future end dates, others have past dates
            is_active = random.random() > 0.2
            if is_active:
                end_date = BASE_DATE + timedelta(days=random.randint(30, 365))
            else:
                end_date = start_date + timedelta(days=random.randint(30, 180))
            
            subscription = {
                "id": str(sub_id),
                "subscription_id": sub_id,
                "customer_id": customer_id,
                "product_id": product["product_id"],  # Use integer product_id
                "product_name": product["name"],
                "product_description": product.get("description"),
                "category": product.get("category"),
                "monthly_fee": product.get("monthly_fee"),
                "status": "active" if is_active else random.choice(statuses),
                "service_status": random.choice(service_statuses) if random.random() > 0.3 else "normal",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),  # Required by Pydantic model
                "monthly_rate": product["price_monthly"],
                "autopay_enabled": random.choice([0, 1]),
                "roaming_enabled": random.choice([0, 1]) if "mobile" in product.get("category", "") else 0,
                "speed_tier": product.get("speed_tier"),
                "data_cap_gb": product.get("data_cap_gb")
            }
            subscriptions.append(subscription)
            
            # Generate invoices for this subscription
            num_invoices = random.randint(1, 6)
            for k in range(num_invoices):
                inv_id = len(invoices) + 1
                invoice_date = start_date + timedelta(days=30 * k)
                amount = product["price_monthly"] * (1 + random.uniform(-0.1, 0.2))  # Some variation
                
                invoice = {
                    "id": str(inv_id),
                    "invoice_id": inv_id,
                    "subscription_id": sub_id,
                    "customer_id": customer_id,
                    "amount": round(amount, 2),
                    "invoice_date": invoice_date.isoformat(),
                    "due_date": (invoice_date + timedelta(days=30)).isoformat(),
                    "status": random.choice(["paid", "paid", "paid", "unpaid", "overdue"]),
                    "description": f"Monthly service - {product['name']}"
                }
                invoices.append(invoice)
                
                # Generate payment if invoice is paid
                if invoice["status"] == "paid":
                    pay_id = len(payments) + 1
                    payment = {
                        "id": str(pay_id),
                        "payment_id": pay_id,
                        "invoice_id": inv_id,
                        "customer_id": customer_id,
                        "amount": invoice["amount"],
                        "payment_date": (invoice_date + timedelta(days=random.randint(1, 25))).isoformat(),
                        "method": random.choice(["credit_card", "debit_card", "bank_transfer", "autopay"]),
                        "status": "successful"  # Must match backend query expectation
                    }
                    payments.append(payment)
            
            # Generate data usage for internet/mobile subscriptions
            if product.get("data_cap_gb"):
                for day_offset in range(min(30, random.randint(7, 30))):
                    usage = {
                        "id": f"USAGE-{sub_id}-{day_offset}",
                        "subscription_id": sub_id,
                        "customer_id": customer_id,
                        "usage_date": (BASE_DATE - timedelta(days=day_offset)).isoformat()[:10],
                        "data_used_mb": random.randint(100, 5000),  # in MB as per Pydantic model
                        "voice_minutes": random.randint(0, 300) if "mobile" in product.get("category", "") else 0,
                        "sms_count": random.randint(0, 100) if "mobile" in product.get("category", "") else 0,
                    }
                    data_usage.append(usage)
            
            # Generate service incidents for some subscriptions (20% chance)
            if random.random() > 0.8:
                for incident_num in range(random.randint(1, 3)):
                    incident_id = len(service_incidents) + 1
                    incident = {
                        "id": str(incident_id),
                        "incident_id": incident_id,
                        "subscription_id": sub_id,
                        "customer_id": customer_id,
                        "incident_date": (BASE_DATE - timedelta(days=random.randint(1, 90))).isoformat(),
                        "description": random.choice([
                            "Temporary service degradation",
                            "Scheduled maintenance impact",
                            "Network connectivity issue",
                            "Equipment malfunction",
                            "Speed reduction during peak hours"
                        ]),
                        "resolution_status": random.choice(["investigating", "resolved"])  # Match SQLite
                    }
                    service_incidents.append(incident)
        
        # Generate orders
        if random.random() > 0.7:
            order_id = len(orders) + 1
            order_product = random.choice(products)
            order = {
                "id": str(order_id),
                "order_id": order_id,
                "customer_id": customer_id,
                "order_date": (BASE_DATE - timedelta(days=random.randint(1, 180))).isoformat(),
                "product_name": order_product["name"],
                "product_id": order_product["product_id"],
                "amount": round(random.uniform(50, 500), 2),
                "order_status": random.choice(["delivered", "completed", "pending", "returned"]),  # Match SQLite
            }
            orders.append(order)
        
        # Generate support tickets
        if random.random() > 0.6:
            ticket_id = len(support_tickets) + 1
            # Get a subscription_id for this customer
            customer_subs = [s for s in subscriptions if s["customer_id"] == customer_id]
            sub_id = customer_subs[0]["subscription_id"] if customer_subs else 1
            
            status = random.choice(["open", "pending", "closed"])  # Match SQLite values
            opened_at = (BASE_DATE - timedelta(days=random.randint(1, 60))).isoformat()
            closed_at = None
            if status == "closed":
                closed_at = (BASE_DATE - timedelta(days=random.randint(0, 5))).isoformat()
            
            ticket = {
                "id": str(ticket_id),
                "ticket_id": ticket_id,
                "customer_id": customer_id,
                "subscription_id": sub_id,
                "category": random.choice(["billing", "technical", "account", "call_drop", "sms_issue"]),  # Match SQLite
                "subject": random.choice([
                    "Slow internet speeds",
                    "Billing question",
                    "Service outage",
                    "Equipment issue",
                    "Plan upgrade request",
                    "Account access problem"
                ]),
                "description": "Customer reported an issue requiring assistance.",
                "status": status,
                "priority": random.choice(["low", "normal", "high", "urgent"]),  # Match SQLite ("normal" not "medium")
                "opened_at": opened_at,
                "closed_at": closed_at,
                "cs_agent": f"Agent{random.randint(1, 10)}"
            }
            support_tickets.append(ticket)
        
        # Generate security logs for some customers
        if random.random() > 0.8 or customer["account_status"] == "locked":
            for log_offset in range(random.randint(1, 5)):
                log_id = len(security_logs) + 1
                # Include 'account_locked' for locked accounts (needed for unlock_account tool)
                if customer["account_status"] == "locked" and log_offset == 0:
                    event_type = "account_locked"
                else:
                    event_type = random.choice(["login_attempt", "login_success", "login_failed", "password_changed"])
                log = {
                    "id": str(log_id),
                    "log_id": log_id,
                    "customer_id": customer_id,
                    "event_type": event_type,
                    "event_timestamp": (BASE_DATE - timedelta(hours=random.randint(1, 720))).isoformat(),
                    "description": f"{event_type.replace('_', ' ').title()} event for customer {customer_id}",
                    "ip_address": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                    "details": {}
                }
                security_logs.append(log)
    
    return {
        "customers": customers,
        "subscriptions": subscriptions,
        "invoices": invoices,
        "payments": payments,
        "orders": orders,
        "support_tickets": support_tickets,
        "data_usage": data_usage,
        "security_logs": security_logs,
        "service_incidents": service_incidents
    }


def seed_container(database, container_name: str, items: List[Dict[str, Any]], upsert: bool = True) -> int:
    """Seed items into a container. Returns count of items seeded."""
    container = database.get_container_client(container_name)
    count = 0
    
    for item in items:
        try:
            if upsert:
                container.upsert_item(item)
            else:
                container.create_item(item)
            count += 1
        except Exception as e:
            logger.warning(f"Error seeding item to {container_name}: {e}")
    
    logger.info(f"Seeded {count} items to {container_name}")
    return count


def seed_database(database) -> Dict[str, int]:
    """Seed all containers with sample data. Returns counts per container."""
    logger.info("Starting database seeding...")
    counts = {}
    
    # Seed products
    products = generate_products()
    counts["products"] = seed_container(database, CONTAINERS["products"], products)
    
    # Seed promotions
    promotions = generate_promotions()
    counts["promotions"] = seed_container(database, CONTAINERS["promotions"], promotions)
    
    # Seed knowledge base
    knowledge = generate_knowledge_base()
    counts["knowledge_documents"] = seed_container(database, CONTAINERS["knowledge_documents"], knowledge)
    
    # Seed customers and related data
    num_customers = int(os.getenv("SEED_CUSTOMER_COUNT", "250"))
    customer_data = generate_customers_and_related(num_customers)
    
    counts["customers"] = seed_container(database, CONTAINERS["customers"], customer_data["customers"])
    counts["subscriptions"] = seed_container(database, CONTAINERS["subscriptions"], customer_data["subscriptions"])
    counts["invoices"] = seed_container(database, CONTAINERS["invoices"], customer_data["invoices"])
    counts["payments"] = seed_container(database, CONTAINERS["payments"], customer_data["payments"])
    counts["orders"] = seed_container(database, CONTAINERS["orders"], customer_data["orders"])
    counts["support_tickets"] = seed_container(database, CONTAINERS["support_tickets"], customer_data["support_tickets"])
    counts["data_usage"] = seed_container(database, CONTAINERS["data_usage"], customer_data["data_usage"])
    counts["security_logs"] = seed_container(database, CONTAINERS["security_logs"], customer_data["security_logs"])
    counts["service_incidents"] = seed_container(database, CONTAINERS["service_incidents"], customer_data["service_incidents"])
    
    logger.info("Database seeding complete!")
    return counts


def run_seeding_if_needed():
    """Main entry point - check if seeding is needed and run it."""
    # Only run if using Cosmos DB backend
    use_cosmos = os.getenv("USE_COSMOSDB", "false").lower() in ("true", "1", "yes", "on")
    if not use_cosmos:
        logger.info("Using SQLite backend - skipping Cosmos DB seeding")
        return None
    
    # Check if seeding is enabled
    seed_enabled = os.getenv("SEED_ON_STARTUP", "true").lower() in ("true", "1", "yes", "on")
    if not seed_enabled:
        logger.info("SEED_ON_STARTUP is disabled - skipping seeding")
        return None
    
    # Import Cosmos client (done here to avoid import issues when not using Cosmos)
    try:
        from azure.cosmos import CosmosClient
        from azure.identity import DefaultAzureCredential
    except ImportError:
        logger.error("Azure Cosmos SDK not installed - cannot seed")
        return None
    
    endpoint = os.getenv("COSMOSDB_ENDPOINT")
    database_name = os.getenv("COSMOS_DATABASE_NAME", "contoso")
    
    if not endpoint:
        logger.error("COSMOSDB_ENDPOINT not set - cannot seed")
        return None
    
    try:
        # Connect using managed identity
        credential = DefaultAzureCredential()
        client = CosmosClient(endpoint, credential=credential)
        database = client.get_database_client(database_name)
        
        # Check if seeding is needed
        if needs_seeding(database):
            logger.info("Database is empty - seeding with sample data...")
            counts = seed_database(database)
            logger.info(f"Seeding complete: {counts}")
            return counts
        else:
            logger.info("Database already has data - skipping seeding")
            return None
            
    except Exception as e:
        logger.error(f"Error during seeding: {e}")
        return None


if __name__ == "__main__":
    # Allow running as standalone script for testing
    logging.basicConfig(level=logging.INFO)
    result = run_seeding_if_needed()
    if result:
        print(f"Seeded data: {result}")
    else:
        print("No seeding performed")
