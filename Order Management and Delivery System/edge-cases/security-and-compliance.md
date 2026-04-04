# Edge Cases — Security and Compliance

## EC-SEC-001: JWT Token Expiry During Active Session

**Scenario:** Customer's access token expires mid-checkout while payment is processing.

**Expected Behaviour:**
- Access token TTL: 1 hour; refresh token TTL: 30 days
- API Gateway rejects expired token with `401 Unauthorized`
- Client SDK transparently refreshes token using refresh token
- If refresh token also expired → redirect to login; cart persists across sessions
- Payment processing (server-side) does not depend on client token; server-to-gateway call completes independently

---

## EC-SEC-002: Privilege Escalation Attempt

**Scenario:** Customer modifies JWT claims to include admin role.

**Expected Behaviour:**
- JWTs signed by Cognito with RS256; API Gateway validates signature against Cognito JWKS
- Modified tokens fail signature validation → `401 Unauthorized`
- Cognito groups are authoritative; custom claims in client-issued tokens are ignored
- API Gateway authorizer checks `cognito:groups` claim from Cognito-issued token only

---

## EC-SEC-003: Cross-Account Order Access

**Scenario:** Customer A crafts a request to access Customer B's order details.

**Expected Behaviour:**
- API handler enforces ownership: `WHERE order.customer_id = token.customer_id`
- Non-matching customer_id → `404 Not Found` (not `403`) to prevent order ID enumeration
- Admin and finance roles bypass ownership check (for support purposes)
- Access logged in audit trail for all order detail views

---

## EC-SEC-004: PCI-DSS Scope — Raw Card Data

**Scenario:** Developer accidentally logs raw card number in application logs.

**Prevention:**
- No raw card data ever enters the system; tokenisation happens at the payment gateway
- Cards are tokenised via gateway-hosted form/SDK on the client side
- System only stores gateway tokens (`tok_xxx`), never PANs or CVVs
- CloudWatch log filter rules block patterns matching card number formats (16 digits)
- Automated PCI scans in CI/CD pipeline flag any code handling card-like data

---

## EC-SEC-005: POD Photo Contains Sensitive Information

**Scenario:** Delivery photo inadvertently captures sensitive information (license plates, personal documents visible).

**Mitigation:**
- POD photos accessible only to: order owner, admin, finance (via signed S3 URLs with 1-hour expiry)
- No public access to S3 POD bucket (bucket policy enforces private-only)
- S3 server-side encryption (AES-256)
- Data retention: photos purged after 5 years per retention policy
- Future enhancement: client-side blur detection before upload

---

## EC-SEC-006: Brute Force Login Attempts

**Scenario:** Attacker attempts credential stuffing against customer login endpoint.

**Expected Behaviour:**
- Cognito built-in lockout: 5 failed attempts → account temporarily locked (30 min)
- WAF rate limit: 20 login attempts per 5 min per IP
- After lockout, customer receives email notification of suspicious activity
- CAPTCHA challenge enabled after 3 failed attempts (Cognito Advanced Security)
- IP addresses with > 100 failed attempts per hour added to WAF block list (auto)
