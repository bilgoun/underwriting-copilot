# # bank_parser/InsightEngine.py
# import pandas as pd
# from datetime import datetime, timedelta
# from collections import Counter, defaultdict
# import logging
# import re
# from typing import Dict, List, Any, Tuple
# from .utils import strToFloat

# logger = logging.getLogger(__name__)

# class AdvancedInsightEngine:
#     def __init__(self, transactions_df):
#         self.df = transactions_df.copy()
#         if self.df.empty or 'transaction_date' not in self.df.columns:
#             raise ValueError("DataFrame must contain valid transaction data with 'transaction_date' column.")

#         self.df['transaction_date'] = pd.to_datetime(self.df['transaction_date'], errors='coerce')
#         self.df.dropna(subset=['transaction_date'], inplace=True)

#         # Ensure numeric columns
#         self.df['debit_transaction'] = pd.to_numeric(self.df['debit_transaction'], errors='coerce').fillna(0)
#         self.df['credit_transaction'] = pd.to_numeric(self.df['credit_transaction'], errors='coerce').fillna(0)

#         # Enhanced categorization
#         self.df['category'] = self.df['description'].apply(self._categorize_transaction)
#         self.df['merchant'] = self.df['description'].apply(self._extract_merchant)

#         # Add temporal features
#         self.df['month'] = self.df['transaction_date'].dt.to_period('M')
#         self.df['day_of_week'] = self.df['transaction_date'].dt.day_name()
#         self.df['hour'] = self.df['transaction_date'].dt.hour

#         logger.info(f"Initialized AdvancedInsightEngine with {len(self.df)} transactions")

#     def _categorize_transaction(self, description):
#         """Enhanced transaction categorization with Mongolian and English patterns"""
#         if not isinstance(description, str):
#             return "Uncategorized"

#         desc_lower = description.lower()

#         # Convenience stores (detailed patterns)
#         convenience_patterns = {
#             'cu': ['cu-', 'cu>', 'trf=cu', 'qpay cu'],
#             'gs25': ['gs25', 'gs 25', 'trf=gs25'],
#             'circle_k': ['circle k', 'circlek'],
#             'семь одиннадцать': ['7-eleven', '7eleven', 'seven eleven']
#         }

#         for store, patterns in convenience_patterns.items():
#             if any(pattern in desc_lower for pattern in patterns):
#                 return f"Convenience Store ({store.upper()})"

#         # Fuel/Vehicle
#         fuel_patterns = ['petrovis', 'petro', 'benzin', 'diesel', 'шатахуун', 'газ станц', 'esso', 'shell']
#         if any(pattern in desc_lower for pattern in fuel_patterns):
#             return "Fuel/Vehicle"

#         # Supermarkets/Department stores
#         supermarket_patterns = {
#             'nomin': ['nomin', 'номин'],
#             'emart': ['emart', 'e-mart'],
#             'sansar': ['sansar', 'сансар'],
#             'urguu': ['urguu', 'ургуу'],
#             'minii_delguur': ['minii delguur', 'миний дэлгүүр']
#         }

#         for store, patterns in supermarket_patterns.items():
#             if any(pattern in desc_lower for pattern in patterns):
#                 return f"Supermarket ({store.title()})"

#         # Restaurants and dining
#         restaurant_patterns = ['restaurant', 'ресторан', 'хоол', 'coffee', 'кофе', 'кафе', 'burger', 'pizza', 'kfc', 'pizza hut']
#         if any(pattern in desc_lower for pattern in restaurant_patterns):
#             return "Restaurant/Dining"

#         # Transportation
#         transport_patterns = ['taxi', 'taci', 'ubcab', 'uber', 'bolt', 'автобус', 'метро', 'тээвэр']
#         if any(pattern in desc_lower for pattern in transport_patterns):
#             return "Transportation"

#         # Fitness/Health
#         fitness_patterns = ['gym', 'fitness', 'спорт', 'биеийн тамир', 'yoga', 'йога', 'tennis', 'теннис']
#         if any(pattern in desc_lower for pattern in fitness_patterns):
#             return "Fitness/Health"

#         # Entertainment/Subscription
#         entertainment_patterns = ['netflix', 'spotify', 'amazon prime', 'youtube', 'киноны', 'тоглоом']
#         if any(pattern in desc_lower for pattern in entertainment_patterns):
#             return "Entertainment/Subscription"

#         # Education
#         education_patterns = ['сургууль', 'хичээл', 'course', 'урок', 'lesson']
#         if any(pattern in desc_lower for pattern in education_patterns):
#             return "Education"

#         # Bank fees
#         fee_patterns = ['хураамж', 'шимтгэл', 'commission', 'fee', 'апп-р хийсэн']
#         if any(pattern in desc_lower for pattern in fee_patterns):
#             return "Bank Fees"

#         # Income patterns
#         income_patterns = ['цалин', 'орлого', 'salary', 'ногдол ашиг', 'dividend']
#         if any(pattern in desc_lower for pattern in income_patterns):
#             return "Income"

#         return "Uncategorized"

#     def _extract_merchant(self, description):
#         """Extract merchant name from transaction description"""
#         if not isinstance(description, str):
#             return "Unknown"

#         desc_lower = description.lower()

#         # Common merchant extraction patterns
#         merchants = {
#             'CU': ['cu-', 'cu>', 'trf=cu'],
#             'GS25': ['gs25', 'trf=gs25'],
#             'Nomin': ['nomin', 'номин'],
#             'Petrovis': ['petrovis'],
#             'UBCab': ['ubcab'],
#             'Netflix': ['netflix'],
#             'Spotify': ['spotify']
#         }

#         for merchant, patterns in merchants.items():
#             if any(pattern in desc_lower for pattern in patterns):
#                 return merchant

#         return "Other"

#     def generate_spending_insights(self) -> List[Dict]:
#         """Generate sophisticated spending pattern insights"""
#         insights = []

#         # Monthly category spending insights
#         insights.extend(self._monthly_category_spending())

#         # Recurring subscription insights
#         insights.extend(self._recurring_subscription_insights())

#         # New merchant/service signup insights
#         insights.extend(self._new_signup_insights())

#         # Impulse spending insights
#         insights.extend(self._impulse_spending_insights())

#         # Seasonal spending patterns
#         insights.extend(self._seasonal_spending_patterns())

#         # Convenience store sweep insights
#         insights.extend(self._convenience_store_insights())

#         return insights

#     def _monthly_category_spending(self) -> List[Dict]:
#         """Analyze monthly spending by category"""
#         insights = []

#         # Get last complete month
#         last_month = self._get_last_complete_month()
#         if not last_month:
#             return insights

#         monthly_data = self.df[self.df['month'] == last_month]
#         if monthly_data.empty:
#             return insights

#         # Category spending analysis
#         category_spending = monthly_data[monthly_data['debit_transaction'] > 0].groupby('category')['debit_transaction'].sum().sort_values(ascending=False)

#         for i, (category, amount) in enumerate(category_spending.head(3).items()):
#             if amount > 10000:  # Minimum threshold
#                 insights.append({
#                     "insight_type": "monthly_category_spending",
#                     "category": category,
#                     "amount": float(amount),
#                     "currency": "MNT",
#                     "period": last_month.strftime("%B %Y"),
#                     "rank": i + 1,
#                     "details": f"User spent {amount:,.0f} MNT on {category} last month"
#                 })

#         return insights

#     def _recurring_subscription_insights(self) -> List[Dict]:
#         """Detect recurring subscriptions and payments"""
#         insights = []

#         # Group by merchant and look for recurring patterns
#         merchant_patterns = self.df.groupby(['merchant', self.df['transaction_date'].dt.day]).size().reset_index()
#         merchant_patterns.columns = ['merchant', 'day_of_month', 'frequency']

#         # Find recurring subscriptions (same day each month, multiple months)
#         recurring = merchant_patterns[merchant_patterns['frequency'] >= 2]

#         for _, row in recurring.iterrows():
#             merchant = row['merchant']
#             day = row['day_of_month']

#             merchant_data = self.df[self.df['merchant'] == merchant]
#             avg_amount = merchant_data['debit_transaction'].mean()

#             if avg_amount > 1000:  # Minimum subscription amount
#                 insights.append({
#                     "insight_type": "recurring_subscription",
#                     "merchant": merchant,
#                     "amount": float(avg_amount),
#                     "currency": "MNT",
#                     "day_of_month": int(day),
#                     "frequency": int(row['frequency']),
#                     "details": f"User has recurring {merchant} subscription on {day}th of every month"
#                 })

#         return insights

#     def _new_signup_insights(self) -> List[Dict]:
#         """Detect new service signups"""
#         insights = []

#         # Look for first-time transactions with specific merchants
#         merchant_first_transactions = self.df.groupby('merchant')['transaction_date'].min()

#         # Services that typically indicate signups
#         signup_services = ['gym', 'fitness', 'netflix', 'spotify', 'art', 'tennis', 'yoga']

#         for merchant, first_date in merchant_first_transactions.items():
#             merchant_lower = merchant.lower()

#             # Check if it's a signup-type service
#             if any(service in merchant_lower for service in signup_services):
#                 # Check if it's recent (within last 3 months)
#                 if first_date >= datetime.now() - timedelta(days=90):
#                     insights.append({
#                         "insight_type": "new_signup",
#                         "service": merchant,
#                         "signup_date": first_date.strftime("%Y-%m-%d"),
#                         "service_type": self._classify_service_type(merchant),
#                         "details": f"User signed up to {merchant} on {first_date.strftime('%B %d')}"
#                     })

#         return insights

#     def _impulse_spending_insights(self) -> List[Dict]:
#         """Identify impulse spending patterns"""
#         insights = []

#         # Convenience store transactions (typically impulse purchases)
#         convenience_data = self.df[self.df['category'].str.contains('Convenience Store', na=False)]

#         if not convenience_data.empty:
#             last_month = self._get_last_complete_month()
#             if last_month:
#                 monthly_convenience = convenience_data[convenience_data['month'] == last_month]
#                 total_convenience = monthly_convenience['debit_transaction'].sum()

#                 if total_convenience > 50000:  # Significant convenience store spending
#                     insights.append({
#                         "insight_type": "impulse_spending",
#                         "category": "Convenience Store",
#                         "amount": float(total_convenience),
#                         "currency": "MNT",
#                         "period": last_month.strftime("%B %Y"),
#                         "transaction_count": len(monthly_convenience),
#                         "details": f"Convenience stores soaked up {total_convenience:,.0f} MNT last month, ranking #1 in impulse spending"
#                     })

#         return insights

#     def _seasonal_spending_patterns(self) -> List[Dict]:
#         """Analyze seasonal spending changes"""
#         insights = []

#         # Compare current month vs previous months
#         monthly_totals = self.df.groupby('month')['debit_transaction'].sum()

#         if len(monthly_totals) >= 2:
#             current_month = monthly_totals.index[-1]
#             current_spending = monthly_totals.iloc[-1]
#             avg_previous = monthly_totals.iloc[:-1].mean()

#             change_pct = ((current_spending - avg_previous) / avg_previous) * 100

#             if abs(change_pct) > 20:  # Significant change
#                 insights.append({
#                     "insight_type": "seasonal_spending_change",
#                     "current_month": current_month.strftime("%B %Y"),
#                     "current_spending": float(current_spending),
#                     "average_previous": float(avg_previous),
#                     "change_percentage": float(change_pct),
#                     "currency": "MNT",
#                     "details": f"Spending {'increased' if change_pct > 0 else 'decreased'} by {abs(change_pct):.1f}% this month"
#                 })

#         return insights

#     def _convenience_store_insights(self) -> List[Dict]:
#         """Specific insights for convenience store spending patterns"""
#         insights = []

#         # CU and GS25 specific analysis
#         cu_data = self.df[self.df['merchant'] == 'CU']
#         gs25_data = self.df[self.df['merchant'] == 'GS25']

#         last_month = self._get_last_complete_month()
#         if not last_month:
#             return insights

#         cu_monthly = cu_data[cu_data['month'] == last_month]['debit_transaction'].sum()
#         gs25_monthly = gs25_data[gs25_data['month'] == last_month]['debit_transaction'].sum()

#         total_convenience = cu_monthly + gs25_monthly

#         if total_convenience > 100000:
#             # Breakdown by store
#             store_breakdown = []
#             if cu_monthly > 0:
#                 store_breakdown.append(f"CU: {cu_monthly:,.0f} MNT")
#             if gs25_monthly > 0:
#                 store_breakdown.append(f"GS25: {gs25_monthly:,.0f} MNT")

#             insights.append({
#                 "insight_type": "convenience_store_breakdown",
#                 "total_amount": float(total_convenience),
#                 "cu_amount": float(cu_monthly),
#                 "gs25_amount": float(gs25_monthly),
#                 "currency": "MNT",
#                 "period": last_month.strftime("%B %Y"),
#                 "store_breakdown": store_breakdown,
#                 "details": f"CU and GS25 soaked up {total_convenience:,.0f} MNT last month"
#             })

#         return insights

#     def _classify_service_type(self, merchant):
#         """Classify type of service for new signups"""
#         merchant_lower = merchant.lower()

#         if any(word in merchant_lower for word in ['gym', 'fitness', 'sport']):
#             return "Gym/Fitness"
#         elif any(word in merchant_lower for word in ['art', 'урлаг']):
#             return "Art class"
#         elif any(word in merchant_lower for word in ['tennis', 'теннис']):
#             return "Tennis"
#         elif any(word in merchant_lower for word in ['volleyball', 'волейбол']):
#             return "Volleyball"
#         elif any(word in merchant_lower for word in ['netflix', 'streaming']):
#             return "Streaming service"
#         else:
#             return "Other service"

#     def _get_last_complete_month(self):
#         """Get the last complete month period"""
#         if self.df.empty:
#             return None

#         today = datetime.now()
#         last_month = today.replace(day=1) - timedelta(days=1)
#         return pd.Period(f"{last_month.year}-{last_month.month:02d}")

#     def generate_behavioral_insights(self) -> List[Dict]:
#         """Generate insights about user behavior patterns"""
#         insights = []

#         # Peak spending times
#         hourly_spending = self.df.groupby('hour')['debit_transaction'].sum()
#         peak_hour = hourly_spending.idxmax()

#         insights.append({
#             "insight_type": "peak_spending_time",
#             "peak_hour": int(peak_hour),
#             "amount": float(hourly_spending.max()),
#             "currency": "MNT",
#             "details": f"Peak spending time is {peak_hour}:00"
#         })

#         # Weekend vs weekday spending
#         weekend_spending = self.df[self.df['day_of_week'].isin(['Saturday', 'Sunday'])]['debit_transaction'].sum()
#         weekday_spending = self.df[~self.df['day_of_week'].isin(['Saturday', 'Sunday'])]['debit_transaction'].sum()

#         if weekend_spending > 0 and weekday_spending > 0:
#             weekend_ratio = weekend_spending / (weekend_spending + weekday_spending)

#             insights.append({
#                 "insight_type": "weekend_spending_pattern",
#                 "weekend_spending": float(weekend_spending),
#                 "weekday_spending": float(weekday_spending),
#                 "weekend_ratio": float(weekend_ratio),
#                 "currency": "MNT",
#                 "details": f"Weekend spending accounts for {weekend_ratio*100:.1f}% of total spending"
#             })

#         return insights

#     def generate_all_insights(self) -> List[Dict]:
#         """Generate all types of insights"""
#         all_insights = []

#         try:
#             all_insights.extend(self.generate_spending_insights())
#             all_insights.extend(self.generate_behavioral_insights())

#             logger.info(f"Generated {len(all_insights)} insights")
#             return all_insights

#         except Exception as e:
#             logger.error(f"Error generating insights: {e}")
#             return []


# bank_parser/InsightEngine.py - Natural Language Insights
import pandas as pd
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import logging
import re
from typing import Dict, List, Any, Tuple
from .utils import strToFloat

logger = logging.getLogger(__name__)


class AdvancedInsightEngine:
    def __init__(self, transactions_df):
        self.df = transactions_df.copy()
        if self.df.empty:
            logger.warning("Empty DataFrame provided to AdvancedInsightEngine")
            return

        self.df["transaction_date"] = pd.to_datetime(
            self.df["transaction_date"], errors="coerce"
        )
        self.df.dropna(subset=["transaction_date"], inplace=True)

        if "debit_transaction" not in self.df.columns:
            self.df["debit_transaction"] = 0
        if "credit_transaction" not in self.df.columns:
            self.df["credit_transaction"] = 0
        if "description" not in self.df.columns:
            self.df["description"] = "Transaction"

        self.df["debit_transaction"] = pd.to_numeric(
            self.df["debit_transaction"], errors="coerce"
        ).fillna(0)
        self.df["credit_transaction"] = pd.to_numeric(
            self.df["credit_transaction"], errors="coerce"
        ).fillna(0)

        categorized_data = self.df["description"].apply(
            self._categorize_transaction_expanded
        )
        self.df["category"] = [item[0] for item in categorized_data]
        self.df["sub_category"] = [item[1] for item in categorized_data]
        self.df["merchant"] = [item[2] for item in categorized_data]

        self.df["month_year"] = self.df["transaction_date"].dt.to_period("M")
        self.df["day_of_week"] = self.df["transaction_date"].dt.day_name()
        self.df["hour"] = self.df["transaction_date"].dt.hour
        self.df["day_of_month"] = self.df["transaction_date"].dt.day

        logger.info(
            f"Initialized AdvancedInsightEngine with {len(self.df)} transactions"
        )
        logger.debug(
            f"Sample of categorized data after init:\n{self.df[['description', 'category', 'sub_category', 'merchant']].head()}"
        )

    def _categorize_transaction_expanded(self, description):
        if not isinstance(description, str):
            return "Other", "Unknown", "Unknown"

        desc_lower = description.lower()
        original_desc = description

        category = "Other"
        sub_category = "Unknown"
        merchant = "Unknown"

        # --- Priority 1: Fees ---
        if "ухаалаг мэдээ үйлчилгээний хураамж" in desc_lower:
            return "Financial Services", "Bank Fees", "Smart Notification Fee"
        if "апп-р хийсэн гүйлгээний хураамж" in desc_lower:
            return "Financial Services", "Bank Fees", "App Transaction Fee"
        if "данс хөтөлсөний хураамж" in desc_lower:
            return "Financial Services", "Bank Fees", "Account Maintenance Fee"
        if "картын захиалгын хураамж" in desc_lower:
            return "Financial Services", "Bank Fees", "Card Order Fee"
        if "картын шилжүүлгийн хураамж" in desc_lower:
            return "Financial Services", "Bank Fees", "Card Transfer Fee"
        if "атм-н бэлэн мөнгөний хураамж" in desc_lower:
            return "Financial Services", "Bank Fees", "ATM Fee"

        # --- Priority 2: Income ---
        if "цалин" in desc_lower or "tsalin" in desc_lower:
            return "Income", "Salary", "Employer"
        if "нөат-ын буцаан" in desc_lower:
            return "Income", "VAT Refund", "Government Tax Authority"
        if (
            "orlogo" == desc_lower.strip()
            or "орлого" == desc_lower.strip()
            or "зээл олгов" in desc_lower
        ):
            return (
                "Income",
                "Other Income/Loan Disbursement",
                "Various",
            )  # Generic if no other clues

        # --- Priority 3: Loan/Credit Related ---
        if "соно финтек" in desc_lower or "sono fintech" in desc_lower:
            merchant = "Sono Fintech"
            if (
                "зээл" in desc_lower
                or "loan" in desc_lower
                or "олгов" in desc_lower
                or "qpay уз96122869" in desc_lower
            ):
                return "Financial Services", "Loan Disbursement", merchant
            else:
                return "Bills & Utilities", "Loan Repayment", merchant
        if "netpay: зээл олгов" in desc_lower:
            return "Financial Services", "Loan Disbursement", "NetPay"
        if "pocketmn" in desc_lower:
            return "Bills & Utilities", "Loan Repayment", "Pocket.mn"
        if (
            "нөмөр кредит зээл олголт" in desc_lower
            or "nomur_credit" in desc_lower.replace(" ", "")
        ):
            return "Financial Services", "Loan Disbursement", "Nomor Credit"
        if "зээл авто төлөлт" in desc_lower:
            return "Bills & Utilities", "Loan Repayment", "Car Loan Auto Debit"
        if "зээл төлөлт" in desc_lower:
            return "Bills & Utilities", "Loan Repayment", "Loan Payment"
        if "зээл хасуулав" in desc_lower:
            return "Bills & Utilities", "Loan Repayment", "Loan Deduction"

        # --- Priority 4: Specific Merchants & Keywords ---
        # Transportation
        if "justcab" in desc_lower:
            merchant = "JustCab"
            return "Transportation", "Taxi/Ride-hailing", merchant
        if "ubcab" in desc_lower:
            merchant = "UBCab"
            return "Transportation", "Taxi/Ride-hailing", merchant
        if "taxi" == desc_lower.strip() or "taci" == desc_lower.strip():
            return "Transportation", "Taxi/Ride-hailing", "Taxi"
        if "petrovis" in desc_lower:
            return "Transportation", "Fuel", "Petrovis"

        # Food & Drink
        if "tom n tom's" in desc_lower:
            return "Food & Drink", "Cafe/Coffee Shop", "Tom N Tom's"
        if "solongos kh" in desc_lower:
            return "Food & Drink", "Restaurant", "Solongos KH"
        if "taijiin bul" in desc_lower:
            return "Food & Drink", "Restaurant/Cafe", "Taijiin Bul"
        if "moskva ikh" in desc_lower:
            return "Food & Drink", "Restaurant", "Moskva IKH"
        if "delimanjoo" in desc_lower:
            return "Food & Drink", "Food Delivery", "DelimanJoo"
        if "tlj-agro" in desc_lower:
            return "Food & Drink", "Bakery/Cafe", "Tous Les Jours (Agro)"
        if "shurkhuukhe" in desc_lower:
            return "Food & Drink", "Restaurant/Cafe", "Shurkhuukhe"
        if "tugs coffee" in desc_lower:
            return "Food & Drink", "Cafe/Coffee Shop", "TUGS Coffee"
        if "bene roaste" in desc_lower:
            return "Food & Drink", "Cafe/Restaurant", "BENE ROASTE"
        if "namaste" in desc_lower:
            return "Food & Drink", "Restaurant", "Namaste"
        if "mungun emii" in desc_lower:
            return "Food & Drink", "Restaurant", "Mungun Emgen"
        if "orange emii" in desc_lower:
            return "Food & Drink", "Restaurant/Cafe", "Orange Emgen"
        if "mint bar" in desc_lower or "mint club" in desc_lower:
            return "Food & Drink", "Bar/Club", "Mint"
        if "amar stars" in desc_lower:
            return "Food & Drink", "Restaurant/Cafe", "Amar Stars"
        if "solongos hoolnii gazar" in desc_lower:
            return "Food & Drink", "Restaurant", "Korean Restaurant"
        if "buuz" in desc_lower:
            return "Food & Drink", "Local Cuisine", "Buuz"
        if "coffee corn" in desc_lower:
            return "Food & Drink", "Cafe/Snacks", "Coffee Corner"
        if "hool" == desc_lower.strip():
            return "Food & Drink", "General", "Food"
        if "wisky" in desc_lower:
            return "Food & Drink", "Alcohol", "Whiskey Purchase/Bar"
        if "tsainii mongo" in desc_lower:
            return "Food & Drink", "Cafe/Groceries", "Tea Money"

        # Shopping/Retail
        if "era jims na" in desc_lower:
            return "Shopping/Retail", "Supermarket", "ERA JIMS"
        if (
            "nomin supermarket" in desc_lower
            or "nomin zah" in desc_lower
            or "nomin uid h" in desc_lower
            or "trf=nomin" in desc_lower
            or "qpay nomin" in desc_lower
        ):
            return "Shopping/Retail", "Supermarket", "Nomin"
        if "erhes khun" in desc_lower:
            return "Shopping/Retail", "Supermarket", "Erhes Khuns"
        if "mmart narni" in desc_lower:
            return "Shopping/Retail", "Supermarket", "MMart Narni"
        if "altjin jims" in desc_lower:
            return "Shopping/Retail", "Supermarket", "Altjin JIMS"
        if "jims khudlaa" in desc_lower:
            return "Shopping/Retail", "Supermarket", "JIMS"
        if "cu" in desc_lower and (
            "trf=" in desc_lower
            or "qpay" in desc_lower
            or desc_lower.startswith("cu-")
            or desc_lower.startswith("cu>")
        ):
            return "Shopping/Retail", "Convenience Store", "CU"
        if "gs25" in desc_lower and ("trf=" in desc_lower or "qpay" in desc_lower):
            return "Shopping/Retail", "Convenience Store", "GS25"
        if "mango" in desc_lower:
            return "Shopping/Retail", "Fashion/Clothing", "Mango"
        if "queen shoes" in desc_lower:
            return "Shopping/Retail", "Fashion/Clothing", "Queen Shoes"
        if "dainty pear" in desc_lower:
            return "Shopping/Retail", "Fashion/Clothing", "Dainty Pear"
        if "brandbox" in desc_lower:
            return "Shopping/Retail", "Fashion/General", "Brandbox"
        if "az fashion" in desc_lower:
            return "Shopping/Retail", "Fashion/Clothing", "AZ Fashion"
        if "nomilon-emn" in desc_lower:
            return "Shopping/Retail", "Fashion/Clothing", "Nomilon Fashion"
        if "monos-naran" in desc_lower:
            return "Shopping/Retail", "Pharmacy/Health Store", "Monos Naran"
        if "вэлл бий" in desc_lower or "wellbee" in desc_lower:
            return "Shopping/Retail", "Pharmacy/Health Store", "Wellbee"
        if "nomtpharm" in desc_lower:
            return "Shopping/Retail", "Pharmacy/Health Store", "Nomin Pharmacy"
        if "narnii guur" in desc_lower:
            return "Shopping/Retail", "Cosmetics/Beauty", "Sunbridge Cosmetics"
        if "store 1133" in desc_lower:
            return "Shopping/Retail", "General Retail", "Store 1133"
        if "tumen plaza" in desc_lower:
            return "Shopping/Retail", "Mall/Department Store", "Tumen Plaza"
        if "gem mall" in desc_lower:
            return "Shopping/Retail", "Mall/Department Store", "GEM Mall"
        if "peacemall g" in desc_lower:
            return "Shopping/Retail", "Mall/Department Store", "Peace Mall"
        if "mimi corner" in desc_lower:
            return "Shopping/Retail", "Fashion/Accessories", "Mimi Corner"
        if "shim delguu" in desc_lower:
            return "Shopping/Retail", "General Retail", "Shim Delguur"
        if "mini market" in desc_lower:
            return "Shopping/Retail", "General Retail", "Mini Market"
        if "online shop" in desc_lower:
            return "Shopping/Retail", "Online Shopping", "Online Shop"
        if "foodpro" in desc_lower:
            return "Shopping/Retail", "Groceries/FoodPro", "FoodPro"
        if "daily groce" in desc_lower:
            return "Shopping/Retail", "Groceries", "Daily Groceries"
        if "bumbugur" in desc_lower:
            return "Shopping/Retail", "Kids/Toys", "Bumbugur (Kids Store)"
        if "makhnii hud" in desc_lower:
            return "Shopping/Retail", "Groceries", "Meat Purchase"
        if "huvtsas" == desc_lower.strip():
            return "Shopping/Retail", "Fashion/Clothing", "Clothes"

        # Subscriptions & Services
        if "netflix" in desc_lower:
            return "Entertainment & Leisure", "Subscription", "Netflix"
        if "spotify" in desc_lower:
            return "Entertainment & Leisure", "Subscription", "Spotify"
        if "4wx4hb facebk" in desc_lower or "fb.me/ads" in desc_lower:
            return "Business Expenses", "Advertising", "Facebook Ads"
        if "4hh3yw netflix.com" in desc_lower:
            return "Entertainment & Leisure", "Subscription", "Netflix"
        if "ezpay" in desc_lower:
            return "Bills & Utilities", "Service/Bill Payment", "EZPay"
        if "monpay" in desc_lower and "qpay" in desc_lower:
            return "Bills & Utilities", "Digital Wallet Payment", "MonPay"
        if "lishpartner" in desc_lower:
            return "Services (General)", "Partner Service", "LishPartner"

        # Cash Withdrawal
        if "atm" in desc_lower and (
            ">khu" in desc_lower
            or ">ulaa" in desc_lower
            or "atm730" in desc_lower
            or "atm1079" in desc_lower
            or "atm1100" in desc_lower
            or "atm572" in desc_lower
        ):
            return "Financial Services", "ATM Withdrawal", "ATM"

        # --- Priority 5: QPAY with potential merchant ---
        if "qpay" in desc_lower:
            match1 = re.search(
                r"qpay\s+([^,]+?)(?:,\s*charge:|,?\s*desc:|,?\s*\d{4,})",
                original_desc,
                re.IGNORECASE,
            )
            match2 = re.search(
                r"qpay\s+\d+,\s*([^,]+?)(?:,\s*charge:|,?\s*desc:)",
                original_desc,
                re.IGNORECASE,
            )
            match3 = re.search(r"qpay\s+\d+,\s*([^,]+)$", original_desc, re.IGNORECASE)
            qpay_generic_code_match = re.search(
                r"qpay\s+([a-zA-Z0-9]{8,})", original_desc
            )  # For generic codes after qpay

            extracted_merchant = None
            if (
                match1
                and match1.group(1).strip().lower()
                not in ["charge", "desc", "ubcab", "justcab"]
                and len(match1.group(1).strip()) > 2
            ):
                extracted_merchant = match1.group(1).strip()
            elif (
                match2
                and match2.group(1).strip().lower()
                not in ["charge", "desc", "ubcab", "justcab"]
                and len(match2.group(1).strip()) > 2
            ):
                extracted_merchant = match2.group(1).strip()
            elif match3 and len(match3.group(1).strip()) > 2:
                extracted_merchant = match3.group(1).strip()

            if extracted_merchant:
                merc_lower = extracted_merchant.lower()
                if "nomi" in merc_lower:
                    return "Shopping/Retail", "Supermarket", "Nomin (via QPay)"
                if "cu" in merc_lower:
                    return "Shopping/Retail", "Convenience Store", "CU (via QPay)"
                if "gs25" in merc_lower:
                    return "Shopping/Retail", "Convenience Store", "GS25 (via QPay)"
                if "coffee" in merc_lower or "кофе" in merc_lower:
                    return (
                        "Food & Drink",
                        "Cafe/Coffee Shop",
                        f"{extracted_merchant} (via QPay)",
                    )
                if (
                    "restaurant" in merc_lower
                    or "хоол" in merc_lower
                    or "кафе" in merc_lower
                ):
                    return (
                        "Food & Drink",
                        "Restaurant",
                        f"{extracted_merchant} (via QPay)",
                    )
                if "такси" in merc_lower or "taxi" in merc_lower:
                    return (
                        "Transportation",
                        "Taxi/Ride-hailing",
                        f"{extracted_merchant} (via QPay)",
                    )
                if (
                    "дэлгүүр" in merc_lower
                    or "delguur" in merc_lower
                    or "market" in merc_lower
                ):
                    return (
                        "Shopping/Retail",
                        "General Retail",
                        f"{extracted_merchant} (via QPay)",
                    )
                return "Services (General)", "QPay Payment", extracted_merchant
            elif "s0027" in desc_lower:
                return "Services (General)", "Service Payment", "S0027 Service (QPay)"
            elif (
                qpay_generic_code_match
            ):  # If it's a qpay followed by a code, it's likely a generic payment.
                return (
                    "Services (General)",
                    "QPay Payment",
                    f"QPay ({qpay_generic_code_match.group(1)})",
                )
            else:
                return "Services (General)", "QPay Payment", "QPay Generic"

        # --- Priority 6: TRF with potential merchant ---
        if "trf=" in desc_lower:
            trf_match = re.search(
                r"trf=.*?-([^>]+)(?:>.*)?$", original_desc, re.IGNORECASE
            )
            if trf_match:
                extracted_merchant = trf_match.group(1).strip()
                merc_lower = extracted_merchant.lower()
                # More specific TRF merchant checks
                if "nomi" in merc_lower or "номин" in merc_lower:
                    return "Shopping/Retail", "Supermarket", "Nomin (via TRF)"
                if "cu" in merc_lower:
                    return "Shopping/Retail", "Convenience Store", "CU (via TRF)"
                if "gs25" in merc_lower:
                    return "Shopping/Retail", "Convenience Store", "GS25 (via TRF)"
                if "era jims" in merc_lower:
                    return "Shopping/Retail", "Supermarket", "ERA JIMS (via TRF)"
                if "altjin jims" in merc_lower:
                    return "Shopping/Retail", "Supermarket", "Altjin JIMS (via TRF)"
                if "mango" in merc_lower:
                    return "Shopping/Retail", "Fashion/Clothing", "Mango (via TRF)"
                if "ezpay" in merc_lower:
                    return (
                        "Bills & Utilities",
                        "Service/Bill Payment",
                        "EZPay (via TRF)",
                    )
                if "store 1133" in merc_lower:
                    return "Shopping/Retail", "General Retail", "Store 1133 (via TRF)"
                if "m-pos merch" in merc_lower:
                    return (
                        "Shopping/Retail",
                        "General Retail (POS)",
                        "M-POS Merchant (via TRF)",
                    )
                if "foodpro" in merc_lower:
                    return "Shopping/Retail", "Groceries/FoodPro", "FoodPro (via TRF)"
                # Check for P2P names within TRF if it doesn't match other merchants
                p2p_indicators_trf = [
                    "oyundelger",
                    "munkhbat",
                    "anujin",
                    "oyunaa",
                    "tulgabayar",
                    "ganzorig",
                    "solongo",
                ]
                if any(name in merc_lower for name in p2p_indicators_trf):
                    return "Transfers", "Peer-to-peer", extracted_merchant
                return "Shopping/Retail", "Card Payment", extracted_merchant
            else:
                return (
                    "Financial Services",
                    "Transfer/Card Payment",
                    "Unknown Card Payment",
                )

        # --- Transfers (more generic, lower priority) ---
        p2p_strict_indicators = [
            "uyangaa",
            "eej",
            "ane n",
            "good saihan",
            "dulguunuud",
            "ariun ikh o",
            "kha",
            "n.uyangaa",
            "n.uyangaaa",
            "bilguun",
            "bilguund",
            "ariun",
            "oyuka",
            "zaya",
            "oyunaa",
            "eej avna",
            "aaw eej avna",
        ]
        if desc_lower.strip() in p2p_strict_indicators:
            return "Transfers", "Peer-to-peer", original_desc.strip().capitalize()
        if original_desc.strip() in [
            "1",
            "99",
            "43",
        ]:  # Known P2P or generic transfer codes
            return "Transfers", "Peer-to-peer", "Individual/Generic Transfer"

        # If no other category matched, it's "Other"
        return category, sub_category, merchant

    def generate_natural_language_insights(self) -> list[str]:
        logger.info("=== ADVANCED NATURAL LANGUAGE INSIGHTS GENERATION ===")
        insights = []
        if self.df.empty:
            logger.info("DataFrame is empty, returning default insight")
            return ["User has no transaction data available."]

        # Filter out "Other" category and "Unknown" merchants for most analyses
        analyzable_df = self.df[
            (self.df["category"] != "Other")
            & (self.df["merchant"] != "Unknown")
            & (self.df["sub_category"] != "Unknown")
        ].copy()

        # Overall Spending
        total_debit = self.df["debit_transaction"].sum()  # Use original df for total
        if total_debit > 0:
            insights.append(
                f"Your total spending in the observed period is {total_debit:,.0f} MNT."
            )

        # Last Complete Month Analysis
        last_month_data = self._get_last_month_data()
        if not last_month_data.empty:
            last_month_analyzable = last_month_data[
                (last_month_data["category"] != "Other")
                & (last_month_data["merchant"] != "Unknown")
            ]
            last_month_spending = last_month_analyzable["debit_transaction"].sum()
            month_name = last_month_data["transaction_date"].iloc[0].strftime("%B")
            if last_month_spending > 0:
                insights.append(
                    f"In {month_name}, your identifiable spending was {last_month_spending:,.0f} MNT."
                )
                category_spending = (
                    last_month_analyzable[
                        last_month_analyzable["debit_transaction"] > 0
                    ]
                    .groupby("category")["debit_transaction"]
                    .sum()
                    .sort_values(ascending=False)
                )

                if not category_spending.empty:
                    top_category = category_spending.index[0]
                    top_amount = category_spending.iloc[0]
                    insights.append(
                        f"Your top spending category in {month_name} was '{top_category}' with {top_amount:,.0f} MNT."
                    )

                    # Nomin Nudge
                    if (
                        top_category in ["Shopping/Retail", "Food & Drink"]
                        and top_amount > 30000
                    ):
                        # Check if "Supermarket" or "Convenience Store" subcategories contributed significantly
                        grocery_convenience_subcats = [
                            "Supermarket",
                            "Convenience Store",
                            "Groceries",
                        ]
                        grocery_convenience_spending = last_month_analyzable[
                            last_month_analyzable["sub_category"].isin(
                                grocery_convenience_subcats
                            )
                        ]["debit_transaction"].sum()

                        nomin_spending_last_month = last_month_analyzable[
                            (
                                last_month_analyzable["merchant"].str.contains(
                                    "Nomin", case=False, na=False
                                )
                            )
                            & (
                                last_month_analyzable["sub_category"].isin(
                                    grocery_convenience_subcats
                                )
                            )
                        ]["debit_transaction"].sum()

                        if (
                            grocery_convenience_spending > 30000
                            and nomin_spending_last_month
                            < grocery_convenience_spending * 0.7
                        ):
                            non_nomin_grocery_spend = (
                                grocery_convenience_spending - nomin_spending_last_month
                            )
                            insights.append(
                                f"Shopping for groceries? You spent {non_nomin_grocery_spend:,.0f} MNT at other stores last month. Remember, Nomin Supermarket offers 10% cashback for our customers!"
                            )

                    # Savings Nudge
                    non_essential_categories = [
                        "Restaurant",
                        "Cafe/Coffee Shop",
                        "Entertainment & Leisure",
                        "Fashion/Clothing",
                        "Alcohol",
                        "Bar/Club",
                    ]
                    # Calculate spending from category index and sub_category column separately
                    category_non_essential = category_spending[
                        category_spending.index.isin(non_essential_categories)
                    ].sum()
                    subcategory_non_essential = last_month_analyzable[
                        last_month_analyzable["sub_category"].isin(
                            non_essential_categories
                        )
                    ]["debit_transaction"].sum()
                    non_essential_spending = (
                        category_non_essential + subcategory_non_essential
                    )
                    if non_essential_spending > 100000:  # Threshold
                        potential_savings = non_essential_spending * 0.10
                        potential_interest_monthly_calc = (
                            potential_savings * 0.05
                        )  # 5% on the saved amount for one month
                        insights.append(
                            f"Last month's spending on dining and leisure was {non_essential_spending:,.0f} MNT. Saving even 10% of that ({potential_savings:,.0f} MNT) in our 5% monthly interest savings account could earn you {potential_interest_monthly_calc:,.0f} MNT next month to put towards something nice!"
                        )

        # Frequent Merchants (from analyzable_df)
        if not analyzable_df.empty:
            frequent_merchants = analyzable_df[analyzable_df["debit_transaction"] > 0][
                "merchant"
            ].value_counts()
            if (
                not frequent_merchants.empty and frequent_merchants.iloc[0] > 4
            ):  # More than 4 times
                top_merchant = frequent_merchants.index[0]
                top_merchant_count = frequent_merchants.iloc[0]
                insights.append(
                    f"Looks like '{top_merchant}' is one of your go-to spots, with {top_merchant_count} visits/purchases recently!"
                )

        # Subscription Analysis
        subscription_transactions = self.df[
            self.df["sub_category"] == "Subscription"
        ]  # Use original df for subscriptions
        if not subscription_transactions.empty:
            for merchant, group in subscription_transactions.groupby("merchant"):
                if len(group) >= 2:  # At least 2 payments
                    avg_amount = group["debit_transaction"].mean()
                    # Find the most common day for this subscription
                    if not group.empty:
                        most_common_day = group["day_of_month"].mode()
                        day_str = (
                            f"around the {most_common_day.iloc[0]}th"
                            if not most_common_day.empty
                            else "regularly"
                        )
                        insights.append(
                            f"Quick reminder: Your {merchant} subscription of about {avg_amount:,.0f} MNT usually renews {day_str} of the month."
                        )

        # Convenience Store Deep Dive
        cu_transactions = self.df[self.df["merchant"] == "CU"]
        gs25_transactions = self.df[self.df["merchant"] == "GS25"]
        cu_sum = cu_transactions["debit_transaction"].sum()
        gs25_sum = gs25_transactions["debit_transaction"].sum()
        total_convenience_sum = cu_sum + gs25_sum
        num_convenience_trips = len(cu_transactions) + len(gs25_transactions)

        if (
            num_convenience_trips > 8 and total_convenience_sum > 70000
        ):  # example thresholds
            insights.append(
                f"You made {num_convenience_trips} trips to CU & GS25, spending {total_convenience_sum:,.0f} MNT. Switching some of those snack runs to Nomin could mean 10% cashback in your pocket!"
            )

        # Loan Repayments
        loan_repayments = self.df[self.df["sub_category"] == "Loan Repayment"]
        if not loan_repayments.empty:
            total_loan_repayment_amount = loan_repayments["debit_transaction"].sum()
            insights.append(
                f"You're consistently managing your finances with loan repayments totaling {total_loan_repayment_amount:,.0f} MNT this period. Well done!"
            )

        # ATM Usage
        atm_withdrawals = self.df[self.df["sub_category"] == "ATM Withdrawal"]
        if len(atm_withdrawals) > 3:
            total_atm_cash = atm_withdrawals["debit_transaction"].sum()
            insights.append(
                f"You've made {len(atm_withdrawals)} ATM withdrawals recently, totaling {total_atm_cash:,.0f} MNT. Planning your cash needs might save a few trips!"
            )

        # Large Transactions (from analyzable_df)
        if total_debit > 0 and not analyzable_df.empty:
            large_debits = analyzable_df[
                analyzable_df["debit_transaction"] > (total_debit * 0.10)
            ]  # 10% of total
            large_debits = large_debits.sort_values(
                by="debit_transaction", ascending=False
            ).head(
                2
            )  # Top 2
            if not large_debits.empty:
                for _, row in large_debits.iterrows():
                    insights.append(
                        f"A notable expense: {row['debit_transaction']:,.0f} MNT for '{row['merchant']}' ({row['category']}) on {row['transaction_date'].strftime('%b %d')}."
                    )

        if not insights:
            insights.append(
                "Your finances are looking steady! Keep up the great work managing your money."
            )

        logger.info(f"Total advanced insights generated: {len(insights)}")
        final_insights = list(set(insights))
        final_insights = final_insights[:10]  # Limit to 10

        for i, insight in enumerate(final_insights):
            logger.info(f"Final Advanced Insight {i+1}: {insight}")
        logger.info("=== END ADVANCED NATURAL LANGUAGE INSIGHTS ===")
        return final_insights

    def _get_last_month_data(self):
        """Get transaction data for the last complete month"""
        if self.df.empty:
            return pd.DataFrame()

        last_month_period = self._get_last_complete_month()
        if not last_month_period:
            return pd.DataFrame()

        return self.df[self.df["month_year"] == last_month_period]

    def _get_last_complete_month(self):
        """Get the last complete month period"""
        if self.df.empty:
            return None

        today = datetime.now()
        last_month = today.replace(day=1) - timedelta(days=1)
        return pd.Period(f"{last_month.year}-{last_month.month:02d}")

    def generate_all_insights(self) -> list[dict]:
        logger.info("=== ADVANCED INSIGHT ENGINE PROCESSING STARTED ===")

        if self.df.empty:
            logger.warning("DataFrame is empty. Returning a default message.")
            return [
                {
                    "insight_type": "natural_language",
                    "content": "No transaction data available for analysis.",
                    "priority": 1,
                    "timestamp": datetime.now().isoformat(),
                }
            ]

        logger.info(f"Processing DataFrame with {len(self.df)} transactions")
        min_date = self.df["transaction_date"].min() if not self.df.empty else "N/A"
        max_date = self.df["transaction_date"].max() if not self.df.empty else "N/A"
        logger.info(f"Date range of transactions: {min_date} to {max_date}")

        try:
            natural_insights = self.generate_natural_language_insights()
            logger.info(
                f"=== RAW ADVANCED INSIGHTS FROM ENGINE ({len(natural_insights)} generated) ==="
            )
            for i, insight in enumerate(natural_insights):
                logger.info(f"Raw Advanced Insight {i+1}: {insight}")

            formatted_insights = []
            for i, insight_content in enumerate(natural_insights):
                formatted_insights.append(
                    {
                        "insight_type": "natural_language",
                        "content": insight_content,
                        "priority": len(natural_insights) - i,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            logger.info(
                f"=== FORMATTED ADVANCED INSIGHTS ({len(formatted_insights)} generated) ==="
            )
            if not formatted_insights:
                logger.warning(
                    "No advanced insights were formatted. Returning a default message."
                )
                return [
                    {
                        "insight_type": "natural_language",
                        "content": "Transaction data analyzed, but no specific advanced insights generated based on current rules.",
                        "priority": 1,
                        "timestamp": datetime.now().isoformat(),
                    }
                ]

            for i, insight in enumerate(formatted_insights):
                logger.info(f"Formatted Advanced Insight {i+1}: {insight}")

            logger.info("=== ADVANCED INSIGHT ENGINE PROCESSING FINISHED ===")
            return formatted_insights

        except Exception as e:
            logger.error(f"Error generating all advanced insights: {e}")
            import traceback

            logger.error(f"Full traceback: {traceback.format_exc()}")
            return [
                {
                    "insight_type": "error",
                    "content": "An error occurred during advanced insight generation.",
                    "priority": 100,
                    "timestamp": datetime.now().isoformat(),
                }
            ]
