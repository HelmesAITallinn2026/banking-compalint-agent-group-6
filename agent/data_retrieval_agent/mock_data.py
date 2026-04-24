from __future__ import annotations

import hashlib
import random


def _seed(complaint_id: str) -> random.Random:
    h = int(hashlib.md5(complaint_id.encode()).hexdigest(), 16)
    return random.Random(h)


def get_customer_details(complaint_id: str, first_name: str, last_name: str) -> dict:
    rng = _seed(complaint_id)
    return {
        "customer_id": f"CUST-{complaint_id[:8].upper()}",
        "first_name": first_name,
        "last_name": last_name,
        "date_of_birth": f"{rng.randint(1960, 2000)}-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}",
        "email": f"{first_name.lower()}.{last_name.lower()}@example.com",
        "customer_since": f"{rng.randint(2010, 2024)}-{rng.randint(1,12):02d}-01",
        "risk_profile": rng.choice(["low", "medium", "high"]),
    }


def get_account_info(complaint_id: str) -> list[dict]:
    rng = _seed(complaint_id + "_accounts")
    accounts = []
    for i in range(rng.randint(1, 3)):
        accounts.append({
            "account_number": f"PL{rng.randint(10**24, 10**25-1)}",
            "account_type": rng.choice(["checking", "savings", "credit"]),
            "currency": rng.choice(["EUR", "PLN", "USD"]),
            "balance": round(rng.uniform(100, 50000), 2),
            "status": "active",
        })
    return accounts


def get_transaction_history(complaint_id: str) -> list[dict]:
    rng = _seed(complaint_id + "_transactions")
    transactions = []
    for i in range(rng.randint(5, 15)):
        transactions.append({
            "transaction_id": f"TXN-{rng.randint(100000, 999999)}",
            "date": f"2026-{rng.randint(1,4):02d}-{rng.randint(1,28):02d}",
            "amount": round(rng.uniform(-5000, 5000), 2),
            "currency": rng.choice(["EUR", "PLN"]),
            "description": rng.choice([
                "ATM Withdrawal", "Online Transfer", "Salary Deposit",
                "Card Payment - Grocery", "Card Payment - Electronics",
                "Standing Order - Rent", "Fee - Account Maintenance",
                "Fee - Card Annual", "Interest Payment", "Refund",
            ]),
            "counterparty": rng.choice(["Biedronka", "Allegro", "ZUS", "Employer LLC", "Landlord", "N/A"]),
        })
    return transactions


DECISION_RULES = """
Decision Rules for Complaint Resolution:

1. Account Issues > Unauthorized Transactions:
   - If disputed transaction found in history → POSITIVE (refund customer)
   - If no matching transaction → NEGATIVE (no evidence of unauthorized activity)

2. Account Issues > Fee Disputes:
   - If fee is standard and disclosed → NEGATIVE (fee is valid)
   - If fee exceeds disclosed amount or customer tenure > 5 years → POSITIVE (waive fee as goodwill)

3. Loan Complaints > Interest Rate Disputes:
   - If rate matches contract → NEGATIVE
   - If rate higher than contracted → POSITIVE (correct the rate)

4. Loan Complaints > Loan Denial:
   - Review based on provided documentation completeness → typically NEGATIVE (bank's right to assess risk)

5. Card Complaints > Fraud:
   - If suspicious transactions present → POSITIVE (block card, initiate refund)

6. Service Quality:
   - Always POSITIVE (acknowledge issue, commit to improvement)

7. Default rule:
   - If complaint is reasonable and customer is in good standing (tenure > 3 years, low risk) → POSITIVE
   - Otherwise → NEGATIVE with explanation
"""
