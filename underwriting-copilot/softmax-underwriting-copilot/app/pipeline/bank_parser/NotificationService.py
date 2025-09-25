# # bank_parser/NotificationService.py - Enhanced with detailed logging
# import requests
# import json
# import logging
# import pandas as pd
# from datetime import datetime
# from typing import List, Dict, Any
# from django.conf import settings

# logger = logging.getLogger('financial_notifications')

# class FinancialNotificationService:
#     def __init__(self):
#         """Initialize the notification service with Gemini 2.5 Pro configuration"""
#         try:
#             self.api_key = getattr(settings, 'GEMINI_API_KEY', None)
#             self.model_name = getattr(settings, 'NOTIFICATION_SETTINGS', {}).get(
#                 'GEMINI_MODEL_NAME', 'gemini-2.5-pro-preview-05-06'
#             )
#             self.llm_available = bool(self.api_key)

#             if not self.llm_available:
#                 logger.warning("GEMINI_API_KEY not found in settings. Using fallback notifications.")
#             else:
#                 logger.info(f"Initialized FinancialNotificationService with model: {self.model_name}")

#         except Exception as e:
#             logger.error(f"Error initializing notification service: {e}")
#             self.llm_available = False

#         self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"

#     def _create_system_prompt(self) -> str:
#         """Create concise system prompt for financial notifications"""
#         return """You are FinBuddy AI for Mongolia. Create short financial notifications.

# RULES:
# - Be friendly, use specific numbers
# - Keep very short: 1-2 sentences max
# - Currency: MNT only
# - Mongolia context (CU, GS25 stores)

# FORMAT:
# Title: [3-4 words max]
# Text: [1 sentence with data]

# EXAMPLES:
# Title: CU Spending Alert
# Text: CU spending hit 150,000 MNT last month!

# Title: Netflix Subscription
# Text: Netflix: 15,000 MNT monthly - still watching?"""

#     def _create_insight_prompt(self, insight: Dict[str, Any]) -> str:
#         """Create short prompts to avoid token limits"""

#         insight_type = insight.get('insight_type', '')

#         if insight_type == "monthly_category_spending":
#             category = insight.get('category', 'purchases')
#             amount = insight.get('amount', 0)
#             return f"Monthly: {amount:,.0f} MNT on {category}. Create notification."

#         elif insight_type == "recurring_subscription":
#             merchant = insight.get('merchant', 'service')
#             amount = insight.get('amount', 0)
#             return f"Subscription: {merchant} {amount:,.0f} MNT monthly. Create notification."

#         elif insight_type == "new_signup":
#             service = insight.get('service', 'service')
#             return f"New service: {service}. Create notification."

#         elif insight_type == "impulse_spending":
#             amount = insight.get('amount', 0)
#             count = insight.get('transaction_count', 0)
#             return f"Impulse: {amount:,.0f} MNT in {count} store visits. Create notification."

#         elif insight_type == "convenience_store_breakdown":
#             total = insight.get('total_amount', 0)
#             return f"Stores: {total:,.0f} MNT total. Create notification."

#         else:
#             return f"Financial insight: {insight_type}. Create notification."

#     def _call_gemini_api(self, user_prompt: str, system_prompt: str) -> str:
#         """Call Gemini API with improved token management"""

#         if not self.api_key:
#             raise Exception("API key not available")

#         url = f"{self.base_url}?key={self.api_key}"
#         headers = {"Content-Type": "application/json"}

#         data = {
#             "contents": [{"parts": [{"text": user_prompt}]}],
#             "systemInstruction": {"parts": [{"text": system_prompt}]},
#             "generationConfig": {
#                 "temperature": 0.7,
#                 "topP": 0.8,
#                 "topK": 20,
#                 "maxOutputTokens": 3000,
#                 "stopSequences": []
#             }
#         }

#         logger.info(f"Calling Gemini API with prompt: {user_prompt[:100]}...")

#         try:
#             response = requests.post(url, headers=headers, json=data, timeout=30)
#             response.raise_for_status()

#             result = response.json()

#             if 'candidates' in result and len(result['candidates']) > 0:
#                 candidate = result['candidates'][0]

#                 # Check finish reason
#                 finish_reason = candidate.get('finishReason', '')
#                 if finish_reason == 'MAX_TOKENS':
#                     logger.warning("Response hit token limit")

#                 if 'content' in candidate:
#                     content = candidate['content']
#                     if 'parts' in content and len(content['parts']) > 0:
#                         generated_text = content['parts'][0].get('text', '')
#                         if generated_text:
#                             logger.info(f"Generated text: {generated_text}")
#                             return generated_text

#             logger.warning("Could not extract valid content from Gemini API response")
#             return ""

#         except requests.exceptions.RequestException as e:
#             logger.error(f"Request error calling Gemini API: {e}")
#             if hasattr(e, 'response') and e.response:
#                 logger.error(f"Response content: {e.response.text}")
#             raise
#         except Exception as e:
#             logger.error(f"Error processing Gemini API response: {e}")
#             raise

#     def generate_notification(self, insight: Dict[str, Any]) -> Dict[str, str]:
#         """Generate a single notification from an insight"""

#         logger.info(f"Generating notification for insight type: {insight.get('insight_type')}")

#         if not insight or not isinstance(insight, dict):
#             logger.warning("Invalid insight data, using fallback")
#             return self._generate_fallback_notification(insight or {})

#         if not self.llm_available:
#             logger.info("LLM not available, using fallback")
#             return self._generate_fallback_notification(insight)

#         try:
#             system_prompt = self._create_system_prompt()
#             insight_prompt = self._create_insight_prompt(insight)

#             logger.info(f"Calling Gemini with prompt: {insight_prompt}")

#             response_text = self._call_gemini_api(insight_prompt, system_prompt)

#             if response_text:
#                 parsed_response = self._parse_llm_response(response_text.strip())
#                 logger.info(f"Successfully generated notification: {parsed_response}")
#                 return parsed_response
#             else:
#                 logger.warning("Empty response from LLM, using fallback")
#                 return self._generate_fallback_notification(insight)

#         except Exception as e:
#             logger.error(f"Error generating notification with LLM: {e}")
#             return self._generate_fallback_notification(insight)

#     def _parse_llm_response(self, response_text: str) -> Dict[str, str]:
#         """Parse LLM response with better fallback handling"""
#         logger.info(f"Parsing LLM response: {response_text}")

#         try:
#             lines = response_text.strip().split('\n')
#             title = ""
#             text = ""

#             for line in lines:
#                 line = line.strip()
#                 if line.startswith('Title:'):
#                     title = line.replace('Title:', '').strip()
#                 elif line.startswith('Text:'):
#                     text = line.replace('Text:', '').strip()

#             # Better fallback parsing
#             if not title or not text:
#                 if '\n' in response_text:
#                     parts = response_text.split('\n', 1)
#                     title = parts[0].strip()[:50]
#                     text = parts[1].strip()[:150] if len(parts) > 1 else parts[0].strip()[:150]
#                 else:
#                     title = response_text[:30].strip()
#                     text = response_text.strip()[:150]

#             # Clean up format markers
#             title = title.replace('Title:', '').replace('[', '').replace(']', '').strip()
#             text = text.replace('Text:', '').replace('[', '').replace(']', '').strip()

#             result = {
#                 "title": title or "Financial Update",
#                 "text": text or "Check your spending insights!"
#             }

#             logger.info(f"Parsed result: {result}")
#             return result

#         except Exception as e:
#             logger.error(f"Error parsing LLM response: {e}")
#             return {
#                 "title": "Financial Update",
#                 "text": response_text[:150] if response_text else "Check your spending insights!"
#             }

#     def _generate_fallback_notification(self, insight: Dict[str, Any]) -> Dict[str, str]:
#         """Generate fallback notifications when LLM is unavailable"""

#         logger.info(f"Generating fallback notification for: {insight.get('insight_type', 'unknown')}")

#         insight_type = insight.get('insight_type', '')

#         fallback_templates = {
#             "monthly_category_spending": {
#                 "title": "Monthly Spending Update",
#                 "text": f"You spent {insight.get('amount', 0):,.0f} MNT on {insight.get('category', 'purchases')} last month."
#             },
#             "recurring_subscription": {
#                 "title": "Recurring Subscription",
#                 "text": f"Your {insight.get('merchant', 'subscription')} charges {insight.get('amount', 0):,.0f} MNT monthly."
#             },
#             "new_signup": {
#                 "title": "New Service Detected",
#                 "text": f"Noticed you signed up for {insight.get('service', 'a new service')} recently!"
#             },
#             "impulse_spending": {
#                 "title": "Impulse Spending Alert",
#                 "text": f"Convenience stores total: {insight.get('amount', 0):,.0f} MNT last month."
#             },
#             "convenience_store_breakdown": {
#                 "title": "Convenience Store Sweep",
#                 "text": f"CU and GS25 spending: {insight.get('total_amount', 0):,.0f} MNT last month."
#             }
#         }

#         result = fallback_templates.get(insight_type, {
#             "title": "Financial Insight",
#             "text": "Check your latest spending patterns in the app!"
#         })

#         logger.info(f"Generated fallback: {result}")
#         return result

#     def generate_multiple_notifications(self, insights: List[Dict[str, Any]], max_notifications: int = 5) -> List[Dict[str, Any]]:
#         """Generate multiple notifications from a list of insights"""

#         logger.info(f"Generating notifications for {len(insights)} insights (max: {max_notifications})")

#         if not insights:
#             logger.info("No insights provided")
#             return []

#         # Prioritize insights by importance
#         prioritized_insights = self._prioritize_insights(insights)
#         logger.info(f"Prioritized insights: {[i.get('insight_type') for i in prioritized_insights]}")

#         notifications = []
#         for i, insight in enumerate(prioritized_insights[:max_notifications]):
#             try:
#                 logger.info(f"Processing insight {i+1}/{min(len(prioritized_insights), max_notifications)}: {insight.get('insight_type')}")

#                 if not insight or not isinstance(insight, dict):
#                     logger.warning(f"Invalid insight at index {i}: {insight}")
#                     continue

#                 notification = self.generate_notification(insight)
#                 notifications.append({
#                     "insight": insight,
#                     "notification": notification,
#                     "priority": insight.get('priority', 1),
#                     "timestamp": insight.get('timestamp', None)
#                 })
#                 logger.info(f"Successfully generated notification {i+1}")
#             except Exception as e:
#                 logger.error(f"Error generating notification for insight {insight.get('insight_type', 'unknown')}: {e}")
#                 continue

#         logger.info(f"Generated {len(notifications)} total notifications")
#         return notifications

#     def _prioritize_insights(self, insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
#         """Prioritize insights based on importance and relevance"""

#         priority_weights = {
#             "monthly_category_spending": 10,
#             "impulse_spending": 9,
#             "convenience_store_breakdown": 8,
#             "recurring_subscription": 7,
#             "new_signup": 6,
#             "seasonal_spending_change": 5,
#             "peak_spending_time": 3,
#             "weekend_spending_pattern": 2
#         }

#         # Add priority scores
#         for insight in insights:
#             if not insight or not isinstance(insight, dict):
#                 continue

#             insight_type = insight.get('insight_type', '')
#             base_priority = priority_weights.get(insight_type, 1)

#             # Boost priority for high amounts
#             amount = insight.get('amount', 0)
#             if amount > 500000:
#                 base_priority += 3
#             elif amount > 200000:
#                 base_priority += 2
#             elif amount > 100000:
#                 base_priority += 1

#             insight['priority'] = base_priority

#         # Filter out invalid insights and sort by priority
#         valid_insights = [i for i in insights if i and isinstance(i, dict)]
#         return sorted(valid_insights, key=lambda x: x.get('priority', 0), reverse=True)

#     def format_for_mobile_push(self, notification: Dict[str, str]) -> Dict[str, str]:
#         """Format notification for mobile push delivery"""
#         title = notification.get('title', 'FinBuddy')
#         text = notification.get('text', 'Check your financial insights!')

#         # Ensure title fits mobile notification limits
#         if len(title) > 50:
#             title = title[:47] + "..."

#         # Ensure text fits mobile notification limits
#         if len(text) > 150:
#             text = text[:147] + "..."

#         return {
#             "title": title,
#             "body": text,
#             "icon": "financial_icon",
#             "badge": "finbuddy_badge",
#             "data": {
#                 "type": "financial_insight",
#                 "timestamp": int(datetime.now().timestamp())
#             }
#         }


# class NotificationTemplateEngine:
#     """Advanced template engine for creating sophisticated notification prompts"""

#     @staticmethod
#     def create_spending_awareness_prompt(insight: Dict[str, Any]) -> str:
#         """Create prompts for spending awareness notifications"""
#         category = insight.get('category', 'purchases')
#         amount = insight.get('amount', 0)
#         period = insight.get('period', 'last month')

#         return f"""
# SPENDING AWARENESS NOTIFICATION

# Context: User spent {amount:,.0f} MNT on {category} in {period}

# Create a notification that:
# 1. Acknowledges the spending without judgment
# 2. Provides context (is this normal, high, or low?)
# 3. Offers a gentle suggestion if spending is high
# 4. Uses encouraging language

# Examples of good awareness notifications:
# - "Coffee shops captured 85,000 MNT last month - fuel for productivity! ☕"
# - "Restaurant visits totaled 240,000 MNT in March. Enjoying the local food scene!"
# - "Gym membership paying off? 45,000 MNT invested in your health this month."

# Generate: Title (3-6 words) and Text (1-2 sentences)
# """

#     @staticmethod
#     def create_savings_opportunity_prompt(insight: Dict[str, Any]) -> str:
#         """Create prompts for savings opportunity notifications"""
#         amount = insight.get('amount', 0)
#         category = insight.get('category', 'spending')

#         potential_savings = amount * 0.3  # Suggest saving 30%

#         return f"""
# SAVINGS OPPORTUNITY NOTIFICATION

# Context: User spent {amount:,.0f} MNT on {category}

# Create a notification that:
# 1. Frames the spending positively
# 2. Suggests a specific savings amount
# 3. Provides a motivating goal or reward
# 4. Uses aspirational language

# Examples of good savings notifications:
# - "CU visits: 150,000 MNT last month. Save 50,000 monthly and fund a weekend getaway!"
# - "Taxi spending hit 200,000 MNT. Try public transport 2 days/week and save for that gadget!"

# Suggested savings: {potential_savings:,.0f} MNT

# Generate: Title (3-6 words) and Text (1-2 sentences)
# """

#     @staticmethod
#     def create_behavioral_insight_prompt(insight: Dict[str, Any]) -> str:
#         """Create prompts for behavioral insights"""
#         insight_type = insight.get('insight_type', '')

#         if insight_type == "peak_spending_time":
#             hour = insight.get('peak_hour', 12)
#             return f"""
# BEHAVIORAL INSIGHT NOTIFICATION

# Context: User's peak spending time is {hour}:00

# Create a notification that:
# 1. Points out the interesting pattern
# 2. Suggests awareness of timing
# 3. Offers a practical tip
# 4. Keeps it light and informative

# Generate: Title and Text
# """

#         elif insight_type == "weekend_spending_pattern":
#             weekend_ratio = insight.get('weekend_ratio', 0.5) * 100
#             return f"""
# BEHAVIORAL INSIGHT NOTIFICATION

# Context: {weekend_ratio:.0f}% of spending happens on weekends

# Create a notification that:
# 1. Highlights the weekend pattern
# 2. Relates to lifestyle or relaxation
# 3. Suggests mindful spending if ratio is high
# 4. Celebrates work-life balance if appropriate

# Generate: Title and Text
# """

#     @staticmethod
#     def create_subscription_review_prompt(insight: Dict[str, Any]) -> str:
#         """Create prompts for subscription review notifications"""
#         merchant = insight.get('merchant', 'service')
#         amount = insight.get('amount', 0)
#         day = insight.get('day_of_month', 1)

#         return f"""
# SUBSCRIPTION REVIEW NOTIFICATION

# Context: {merchant} subscription charges {amount:,.0f} MNT on the {day}th monthly

# Create a notification that either:
# 1. Celebrates active usage (if it's clearly beneficial)
# 2. Suggests review (if it might be forgotten)
# 3. Offers optimization tips
# 4. Provides cancellation reminder for unused services

# Examples:
# - "Netflix renewed for 15,000 MNT. Enjoying the new season?"
# - "Gym membership: 45,000 MNT monthly. Getting those gains? 💪"
# - "Spotify Premium active. Cancel anytime if you're not vibing with it."

# Generate: Title and Text
# """

# # Integration helper functions
# def integrate_with_bank_parser():
#     """Helper function to integrate notification service with existing bank parser"""

#     def generate_insights_and_notifications(customer_id: int, combined_df: pd.DataFrame) -> Dict[str, Any]:
#         """
#         Integration function to be called from BankStatementUploadView
#         """
#         try:
#             # Import here to avoid circular imports
#             from .InsightEngine import AdvancedInsightEngine

#             # Initialize insight engine
#             insight_engine = AdvancedInsightEngine(combined_df)

#             # Generate insights
#             insights = insight_engine.generate_all_insights()

#             # Initialize notification service
#             notification_service = FinancialNotificationService()

#             # Generate notifications
#             notifications = notification_service.generate_multiple_notifications(
#                 insights, max_notifications=5
#             )

#             # Format for response
#             formatted_notifications = []
#             for notif_data in notifications:
#                 mobile_format = notification_service.format_for_mobile_push(
#                     notif_data['notification']
#                 )

#                 formatted_notifications.append({
#                     "insight_type": notif_data['insight'].get('insight_type'),
#                     "priority": notif_data.get('priority', 1),
#                     "notification": mobile_format,
#                     "insight_details": notif_data['insight']
#                 })

#             return {
#                 "raw_insights": insights,
#                 "generated_notifications": formatted_notifications,
#                 "notification_count": len(formatted_notifications)
#             }

#         except Exception as e:
#             logger.error(f"Error in insights and notifications generation: {e}")
#             return {
#                 "raw_insights": [],
#                 "generated_notifications": [],
#                 "notification_count": 0,
#                 "error": str(e)
#             }

#     return generate_insights_and_notifications


# bank_parser/NotificationService.py - Natural Language Processing
import requests
import json
import logging
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any
from django.conf import settings

logger = logging.getLogger("financial_notifications")


class FinancialNotificationService:
    def __init__(self):
        """Initialize the notification service with Gemini 2.5 Pro configuration"""
        try:
            self.api_key = getattr(settings, "GEMINI_API_KEY", None)
            self.model_name = getattr(settings, "NOTIFICATION_SETTINGS", {}).get(
                "GEMINI_MODEL_NAME", "gemini-2.5-pro-preview-06-05"
            )
            self.llm_available = bool(self.api_key)

            if not self.llm_available:
                logger.error(
                    "GEMINI_API_KEY not found in settings. AI insights will not be available."
                )
            else:
                logger.info(
                    f"Initialized FinancialNotificationService with model: {self.model_name}"
                )

        except Exception as e:
            logger.error(f"Error initializing notification service: {e}")
            self.llm_available = False

        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"

    def _create_system_prompt(self) -> str:
        """Create system prompt for FinBuddy AI"""
        return """You are FinBuddy, a helpful financial AI companion for Softmax bank customers in Mongolia. Your job is to create engaging, friendly, and actionable push notifications based on spending insights.
        Always back your claims with actual numbers. For grocery shopping, we have agreement with Nomin Supermarket to provide 10% cashback for our customers, gently but not overtly aggresively nudge the customers to use Nomin Supermarket instead of other 
        Convenience Stores, Supermarket or other grocery shopping. All notifications must be unique in context. We also have a 5% interest monthly saving account service for all customers, if a customer spends too much money on something non-essential, you can friendly remind them about our savings account and how much they can earn and use that for something nice.
        Also, if a customer has recurring payment and has not enough balance coming to that day, you can remind them about our low-interest loan which is only few taps away on their mobile app.
        All in all, you first and foremost should always be a helpful financial AI companion without being a complete shill. Find the balance. 

RULES:
1. Be conversational and friendly, like a helpful friend
2. Use specific numbers from the insights provided
3. Keep notifications short but engaging (1-2 sentences max)
4. Always use MNT as currency
5. Context: Mongolia (CU, GS25 convenience stores, Nomin supermarkets, UBCab taxis, etc.)
6. Provide actionable suggestions when possible (save money, try alternatives, etc.)
7. Be encouraging and positive, not judgmental about spending

NOTIFICATION TYPES TO CREATE:
- Convenience store spending alerts with savings suggestions
- Subscription reminders with cancellation advice if appropriate
- New service congratulations with related offers
- Restaurant pattern observations with new recommendations
- Behavioral insights with optimization tips

RESPONSE FORMAT:
For each insight provided, generate exactly one notification in this format:
Title: [4-6 words, catchy and relevant]
Text: [1-2 sentences with specific data and actionable advice]

EXAMPLES:
Title: Convenience Store Sweep
Text: CU and GS25 soaked up 312,500 MNT last month, ranking #1 in impulse spending. Try saving 100,000 MNT monthly and treat yourself to a nice trip by year-end!

Title: Netflix Subscription Check
Text: Netflix subscription renewed for 25,000 MNT. Now that Stranger Things ended, canceling could save you money for other entertainment!

Title: Gym Membership Active
Text: Great job on your gym membership! Consider protein powder from Optimum Nutrition for 10% cashback to maximize your fitness gains.

Title: New Restaurant Discovery
Text: Based on your 4 visits to Namaste over 3 months, try the new Indian restaurant downtown for variety in your favorite cuisine!"""

    def _call_gemini_api(self, user_prompt: str, system_prompt: str) -> str:
        """Call Gemini API with natural language insights"""

        if not self.api_key:
            raise Exception("API key not available")

        url = f"{self.base_url}?key={self.api_key}"
        headers = {"Content-Type": "application/json"}

        data = {
            "contents": [{"parts": [{"text": user_prompt}]}],
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "generationConfig": {
                "temperature": 0.8,  # Slightly higher for more creative notifications
                "topP": 0.9,
                "topK": 40,
                "maxOutputTokens": 15000,  # Increased for multiple notifications
                "stopSequences": [],
            },
        }

        # Log detailed API payload information
        logger.info(f"=== GEMINI API PAYLOAD DEBUG ===")
        logger.info(f"API URL: {self.base_url}")
        logger.info(f"Model: {self.model_name}")
        logger.info(f"User prompt length: {len(user_prompt)} characters")
        logger.info(f"System prompt length: {len(system_prompt)} characters")
        logger.info(f"=== SYSTEM PROMPT ===")
        logger.info(f"{system_prompt}")
        logger.info(f"=== USER PROMPT ===")
        logger.info(f"{user_prompt}")
        logger.info(f"=== GENERATION CONFIG ===")
        logger.info(f"Temperature: {data['generationConfig']['temperature']}")
        logger.info(f"TopP: {data['generationConfig']['topP']}")
        logger.info(f"TopK: {data['generationConfig']['topK']}")
        logger.info(f"MaxOutputTokens: {data['generationConfig']['maxOutputTokens']}")
        logger.info(f"=== END PAYLOAD DEBUG ===")

        logger.info(f"Calling Gemini API with {len(user_prompt)} characters")

        try:
            response = requests.post(url, headers=headers, json=data, timeout=300)
            response.raise_for_status()

            result = response.json()

            # Log the COMPLETE API response for debugging (no truncation)
            logger.info(f"=== GEMINI API COMPLETE RESPONSE ===")
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            logger.info(f"FULL RAW RESPONSE: {response.text}")

            # Also log the parsed JSON in a more readable format
            import json

            logger.info(f"PARSED JSON RESPONSE:")
            logger.info(json.dumps(result, indent=2, ensure_ascii=False))

            # Extract and log usage metadata including thinking tokens
            if "usageMetadata" in result:
                usage = result["usageMetadata"]
                logger.info(f"=== USAGE METADATA ===")
                logger.info(f"Prompt tokens: {usage.get('promptTokenCount', 'N/A')}")
                logger.info(f"Total tokens: {usage.get('totalTokenCount', 'N/A')}")
                logger.info(
                    f"Thinking tokens: {usage.get('thoughtsTokenCount', 'N/A')}"
                )
                if "promptTokensDetails" in usage:
                    logger.info(f"Prompt token details: {usage['promptTokensDetails']}")
                logger.info(f"=== END USAGE METADATA ===")

            # Extract and log thinking/reasoning if available
            if "candidates" in result:
                for i, candidate in enumerate(result["candidates"]):
                    logger.info(f"=== CANDIDATE {i+1} ===")
                    if "content" in candidate:
                        content = candidate["content"]
                        logger.info(f"Content role: {content.get('role', 'N/A')}")
                        if "parts" in content:
                            for j, part in enumerate(content["parts"]):
                                if "text" in part:
                                    logger.info(
                                        f"Generated text part {j+1}: {part['text']}"
                                    )
                                if "thoughts" in part:
                                    logger.info(
                                        f"THINKING/REASONING part {j+1}: {part['thoughts']}"
                                    )
                    if "finishReason" in candidate:
                        logger.info(f"Finish reason: {candidate['finishReason']}")
                    if "thoughts" in candidate:
                        logger.info(
                            f"CANDIDATE THINKING/REASONING: {candidate['thoughts']}"
                        )
                    # Check for any other fields that might contain thinking content
                    for key, value in candidate.items():
                        if "think" in key.lower() or "reason" in key.lower():
                            logger.info(f"Found thinking field '{key}': {value}")
                    logger.info(f"=== END CANDIDATE {i+1} ===")

            logger.info(f"=== END COMPLETE RESPONSE ===")

            if "candidates" in result and len(result["candidates"]) > 0:
                candidate = result["candidates"][0]

                if "content" in candidate:
                    content = candidate["content"]
                    if "parts" in content and len(content["parts"]) > 0:
                        generated_text = content["parts"][0].get("text", "")
                        if generated_text:
                            logger.info(f"=== GENERATED TEXT ===")
                            logger.info(
                                f"Generated text length: {len(generated_text)} characters"
                            )
                            logger.info(f"Generated text content: {generated_text}")
                            logger.info(f"=== END GENERATED TEXT ===")
                            return generated_text

            logger.warning("Could not extract valid content from Gemini API response")
            logger.warning(f"Response structure: {result}")
            return ""

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error calling Gemini API: {e}")
            if hasattr(e, "response") and e.response:
                logger.error(f"Response content: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error processing Gemini API response: {e}")
            raise

    def generate_notifications_from_insights(
        self, insights: List[str]
    ) -> List[Dict[str, str]]:
        """Generate notifications from natural language insights"""

        logger.info(f"=== INSIGHTS PROCESSING DEBUG ===")
        logger.info(f"Received {len(insights)} insights for processing")
        for i, insight in enumerate(insights):
            logger.info(
                f"Insight {i+1}: {insight[:200]}..."
            )  # Log first 200 chars of each insight
        logger.info(f"=== END INSIGHTS DEBUG ===")

        if not insights:
            logger.info("No insights provided")
            return []

        if not self.llm_available:
            logger.error("Gemini API key not available")
            raise Exception(
                "Gemini API key not configured. Please check your settings."
            )

        try:
            # Combine insights into a single prompt
            insights_text = "\n".join(
                [f"- {insight}" for insight in insights[:5]]
            )  # Limit to 5 insights

            user_prompt = f"""Based on these user spending insights, generate 3-5 engaging push notifications:

{insights_text}

Generate notifications that are helpful, friendly, and actionable. Each notification should have a catchy title and engaging text with specific suggestions."""

            logger.info(f"=== CONSTRUCTED USER PROMPT ===")
            logger.info(f"Combined {len(insights[:5])} insights into user prompt")
            logger.info(f"User prompt: {user_prompt}")
            logger.info(f"=== END USER PROMPT ===")

            system_prompt = self._create_system_prompt()

            response_text = self._call_gemini_api(user_prompt, system_prompt)

            if response_text:
                notifications = self._parse_multiple_notifications(response_text)
                logger.info(f"=== PARSED NOTIFICATIONS ===")
                logger.info(f"Generated {len(notifications)} notifications from LLM")
                for i, notification in enumerate(notifications):
                    logger.info(
                        f"Notification {i+1}: Title='{notification.get('title')}', Text='{notification.get('text')}'"
                    )
                logger.info(f"=== END PARSED NOTIFICATIONS ===")
                return notifications
            else:
                logger.error("Empty response from Gemini API")
                raise Exception("Gemini API returned empty response. Please try again.")

        except Exception as e:
            logger.error(f"Error generating notifications: {e}")
            raise Exception(f"Failed to generate AI insights: {str(e)}")

    def _parse_multiple_notifications(self, response_text: str) -> List[Dict[str, str]]:
        """Parse multiple notifications from LLM response"""
        notifications = []

        try:
            # Split by Title: to find individual notifications
            sections = response_text.split("Title:")

            for section in sections[1:]:  # Skip first empty section
                lines = section.strip().split("\n")
                if len(lines) >= 2:
                    title = lines[0].strip()

                    # Find text line
                    text = ""
                    for line in lines[1:]:
                        if line.strip().startswith("Text:"):
                            text = line.replace("Text:", "").strip()
                            break
                        elif line.strip() and not line.strip().startswith("Title:"):
                            text = line.strip()
                            break

                    if title and text:
                        # Clean up formatting
                        title = title.replace("*", "").replace("**", "").strip()
                        text = text.replace("*", "").replace("**", "").strip()

                        notifications.append(
                            {
                                "title": title[:70],  # Limit title length (increased)
                                "text": text[:300],  # Limit text length (increased)
                            }
                        )

            # If parsing failed, try alternative method
            if not notifications:
                notifications = self._alternative_parse(response_text)

            logger.info(f"Parsed {len(notifications)} notifications")
            return notifications[:5]  # Limit to 5 notifications

        except Exception as e:
            logger.error(f"Error parsing notifications: {e}")
            return self._alternative_parse(response_text)

    def _alternative_parse(self, response_text: str) -> List[Dict[str, str]]:
        """Alternative parsing method if main parsing fails"""
        try:
            # Split into paragraphs and try to extract title/text pairs
            paragraphs = [p.strip() for p in response_text.split("\n\n") if p.strip()]

            notifications = []
            current_title = ""

            for paragraph in paragraphs:
                lines = paragraph.split("\n")
                for line in lines:
                    line = line.strip()
                    if line.startswith("Title:") or line.startswith("**Title:"):
                        current_title = (
                            line.replace("Title:", "").replace("**", "").strip()
                        )
                    elif line.startswith("Text:") or line.startswith("**Text:"):
                        text = line.replace("Text:", "").replace("**", "").strip()
                        if current_title and text:
                            notifications.append(
                                {"title": current_title[:70], "text": text[:300]}
                            )
                            current_title = ""

            return notifications[:5]

        except Exception as e:
            logger.error(f"Alternative parsing failed: {e}")
            return [
                {"title": "Financial Update", "text": "Check your spending insights!"}
            ]

    def generate_multiple_notifications(
        self, insights: List[Dict[str, Any]], max_notifications: int = 5
    ) -> List[Dict[str, Any]]:
        """Generate multiple notifications from insights (maintains compatibility)"""

        logger.info(f"Processing {len(insights)} insights for notifications")

        if not insights:
            return []

        # Extract natural language content from insights
        natural_insights = []
        for insight in insights:
            if insight.get("insight_type") == "natural_language":
                content = insight.get("content", "")
                if content:
                    natural_insights.append(content)

        # If no natural language insights, create basic ones
        if not natural_insights:
            natural_insights = [
                "User has transaction data available for financial analysis"
            ]

        # Generate notifications
        notifications = self.generate_notifications_from_insights(natural_insights)

        # Format in expected structure
        formatted = []
        for i, notification in enumerate(notifications[:max_notifications]):
            formatted.append(
                {
                    "insight": {
                        "insight_type": "natural_language",
                        "content": (
                            natural_insights[i]
                            if i < len(natural_insights)
                            else "Financial insight"
                        ),
                        "priority": len(notifications) - i,
                    },
                    "notification": notification,
                    "priority": len(notifications) - i,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        logger.info(f"Generated {len(formatted)} formatted notifications")
        return formatted

    def format_for_mobile_push(self, notification: Dict[str, str]) -> Dict[str, str]:
        """Format notification for mobile push delivery"""
        title = notification.get("title", "FinBuddy")
        text = notification.get("text", "Check your financial insights!")

        # Ensure title fits mobile notification limits
        if len(title) > 70:
            title = title[:67] + "..."

        # Ensure text fits mobile notification limits
        if len(text) > 300:
            text = text[:297] + "..."

        return {
            "title": title,
            "body": text,
            "icon": "financial_icon",
            "badge": "finbuddy_badge",
            "data": {
                "type": "financial_insight",
                "timestamp": int(datetime.now().timestamp()),
            },
        }
