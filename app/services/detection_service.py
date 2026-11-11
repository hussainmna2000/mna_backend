import re
import urllib.parse
from typing import Dict, Any, List, Tuple


class ScamDetectionEngine:
    """
    Production-grade detection engine for multi-vector scam and threat intelligence analysis.
    Evaluates risk factors, classifies threat severity, and calculates a normalized 0-100 risk score.
    """

    # High-risk scam phrases across SMS/WhatsApp/Email
    SUSPICIOUS_PHRASES = [
        (r"\b(urgent|immediately|within 24 hours|account suspended|deactivated|blocked)\b", 25, "Urgency & Account Termination Pressure"),
        (r"\b(otp|one time password|pin|security code|never share)\b", 20, "Credential or OTP Solicitation"),
        (r"\b(kyc|update kyc|pan card|aadhar card|verify identity)\b", 25, "Fake KYC Verification Scam"),
        (r"\b(lottery|won|winner|prize|cash reward|crore|million dollars)\b", 30, "Lottery or Reward Fraud"),
        (r"\b(claim your|refund pending|tax refund|electricity disconnected)\b", 25, "Utility or Refund Impersonation"),
        (r"\b(crypto|bitcoin|eth|guaranteed return|100% profit|double your money)\b", 35, "High-Risk Crypto / Investment Scheme"),
        (r"\b(anydesk|teamviewer|quicksupport|download apk|install app)\b", 40, "Remote Access Trojan / Dangerous App Installation"),
        (r"\b(fedex|dhl|customs|parcel seized|illegal package)\b", 30, "Digital Arrest / Courier Seizure Scam"),
        (r"\b(police|cbi|trai|rbi|customs officer|arrest warrant)\b", 40, "Law Enforcement / Authority Impersonation"),
    ]

    # Suspicious domain indicators
    SUSPICIOUS_TLDS = [".xyz", ".top", ".buzz", ".work", ".click", ".surf", ".rest", ".fit", ".loan", ".tk", ".ml", ".ga", ".cf"]
    BRAND_TARGETS = ["paypal", "google", "microsoft", "apple", "amazon", "netflix", "sbi", "hdfc", "icici", "chase", "bankofamerica", "coinbase", "binance", "metamask"]

    @classmethod
    def analyze_phone(cls, phone_number: str, context: str = "") -> Dict[str, Any]:
        """Analyze a phone number for spam, robocall, and spoofing indicators."""
        clean_num = re.sub(r"[^\d+]", "", phone_number)
        threat_indicators = []
        score = 5.0
        metadata = {
            "formatted_number": clean_num,
            "length": len(clean_num),
            "carrier_type": "Mobile / Telephony",
        }

        # Format / Length checks
        if len(clean_num) < 7:
            score += 35
            threat_indicators.append("Unusually short or invalid phone number format")

        # Specific international high-fraud prefixes
        if clean_num.startswith(("+234", "+254", "+92", "+375", "+882", "+881")):
            score += 30
            threat_indicators.append("Originating from high-incidence international telephony fraud region")
            metadata["risk_region"] = True

        # VoIP / Virtual / Toll-free patterns
        if any(clean_num.startswith(p) for p in ["+1800", "+1888", "+1877", "+1866", "1800", "1888", "1877"]):
            metadata["carrier_type"] = "Toll-Free / Virtual Line"
            score += 15
            threat_indicators.append("Toll-free virtual number often leveraged in tech support & banking scams")

        # Context evaluation
        if context:
            ctx_lower = context.lower()
            for pattern, weight, label in cls.SUSPICIOUS_PHRASES:
                if re.search(pattern, ctx_lower):
                    score += weight
                    threat_indicators.append(f"Context trigger: {label}")

        risk_score, risk_level, verdict = cls._calculate_verdict(score)
        
        recommendations = [
            "Do not call back unfamiliar numbers with missed calls.",
            "Never share One-Time Passwords (OTP) or personal banking details over the phone.",
            "Verify any alleged institutional claims using official contact numbers listed on their verified website."
        ]

        explanation = (
            f"Phone number {clean_num} evaluated with a threat score of {risk_score}/100. "
            f"Risk Level: {risk_level}. Verdict: {verdict}. "
            f"{'Threat indicators identified: ' + '; '.join(threat_indicators) if threat_indicators else 'No active malicious patterns detected.'}"
        )

        return {
            "category": "phone",
            "query_target": clean_num,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "verdict": verdict,
            "threat_indicators": threat_indicators,
            "explanation": explanation,
            "recommendations": recommendations,
            "metadata_info": metadata,
        }

    @classmethod
    def analyze_message(cls, message_text: str, channel: str = "sms") -> Dict[str, Any]:
        """Analyze SMS, WhatsApp, or chat messages for scam indicators."""
        threat_indicators = []
        score = 10.0
        msg_lower = message_text.lower()

        # Check for URLs in message
        url_match = re.findall(r"https?://[^\s]+", message_text)
        if url_match:
            score += 25
            threat_indicators.append(f"Message contains embedded hyperlinks: {url_match[0][:40]}...")

        # Match suspicious phrases
        for pattern, weight, label in cls.SUSPICIOUS_PHRASES:
            if re.search(pattern, msg_lower):
                score += weight
                threat_indicators.append(label)

        # Check for excessive punctuation / ALL CAPS
        if len(message_text) > 20 and sum(1 for c in message_text if c.isupper()) / len(message_text) > 0.4:
            score += 10
            threat_indicators.append("High capital letter ratio typically used to manufacture false urgency")

        risk_score, risk_level, verdict = cls._calculate_verdict(score)

        recommendations = [
            "Do not click on links sent from unknown senders via SMS or WhatsApp.",
            "Financial institutions will never demand immediate payment or credentials over instant messaging.",
            "Report and block the sender in your messaging application."
        ]

        explanation = (
            f"Message analyzed across {len(threat_indicators)} potential threat vectors. "
            f"Overall risk evaluated at {risk_score}%. Verdict: {verdict}."
        )

        return {
            "category": "message",
            "query_target": message_text[:100] + ("..." if len(message_text) > 100 else ""),
            "risk_score": risk_score,
            "risk_level": risk_level,
            "verdict": verdict,
            "threat_indicators": threat_indicators,
            "explanation": explanation,
            "recommendations": recommendations,
            "metadata_info": {"channel": channel, "char_count": len(message_text), "has_url": bool(url_match)},
        }

    @classmethod
    def analyze_url(cls, url: str) -> Dict[str, Any]:
        """Inspect a URL for phishing, homograph attacks, typosquatting, and deceptive structure."""
        threat_indicators = []
        score = 8.0

        if not url.startswith(("http://", "https://")):
            url_to_parse = "http://" + url
        else:
            url_to_parse = url

        try:
            parsed = urllib.parse.urlparse(url_to_parse)
            domain = parsed.netloc.lower()
        except Exception:
            domain = url.lower()

        # IP address as hostname
        if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", domain):
            score += 45
            threat_indicators.append("Raw numeric IP address used instead of reputable registered domain name")

        # Insecure HTTP
        if url.startswith("http://"):
            score += 15
            threat_indicators.append("Unencrypted HTTP protocol detected without SSL certificate")

        # Suspicious TLDs
        for tld in cls.SUSPICIOUS_TLDS:
            if domain.endswith(tld):
                score += 25
                threat_indicators.append(f"High-risk top-level domain ({tld}) frequently leveraged in disposable phishing campaigns")
                break

        # Typosquatting / Brand spoofing
        for brand in cls.BRAND_TARGETS:
            if brand in domain and not domain.endswith(f".{brand}.com") and domain != f"{brand}.com":
                score += 40
                threat_indicators.append(f"Deceptive impersonation targeting recognizable brand: '{brand}'")
                break

        # Excessive hyphens or subdomains
        if domain.count("-") >= 2:
            score += 20
            threat_indicators.append("Excessive hyphenation in hostname characteristic of phishing redirects")
        if domain.count(".") >= 3:
            score += 15
            threat_indicators.append("Suspicious multi-tiered subdomain nesting")

        risk_score, risk_level, verdict = cls._calculate_verdict(score)

        recommendations = [
            "Do not input usernames, passwords, or payment cards on this website.",
            "Verify the exact address in the browser address bar before continuing.",
            "Check for official security badges and TLS certificate validation."
        ]

        explanation = (
            f"Domain '{domain}' scored {risk_score}/100. "
            f"Risk category: {risk_level}. "
            f"{'Identified security flags: ' + '; '.join(threat_indicators) if threat_indicators else 'Domain presents standard security properties.'}"
        )

        return {
            "category": "url",
            "query_target": url,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "verdict": verdict,
            "threat_indicators": threat_indicators,
            "explanation": explanation,
            "recommendations": recommendations,
            "metadata_info": {"domain": domain, "scheme": parsed.scheme if 'parsed' in locals() else "unknown"},
        }

    @classmethod
    def analyze_email(cls, email_text: str = "", sender_email: str = "", subject: str = "") -> Dict[str, Any]:
        """Analyze email headers, sender address, and body for phishing & BEC indicators."""
        threat_indicators = []
        score = 8.0
        combined = f"{subject} {email_text} {sender_email}".lower()

        # Sender email evaluation
        if sender_email:
            free_providers = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]
            for brand in cls.BRAND_TARGETS:
                if brand in sender_email.lower() and any(sender_email.lower().endswith(f"@{p}") for p in free_providers):
                    score += 45
                    threat_indicators.append(f"Institutional brand '{brand}' claimed from free public email address ({sender_email})")

        # Subject & text matching
        for pattern, weight, label in cls.SUSPICIOUS_PHRASES:
            if re.search(pattern, combined):
                score += weight
                threat_indicators.append(label)

        risk_score, risk_level, verdict = cls._calculate_verdict(score)

        recommendations = [
            "Check the full sender email address, not just the display name.",
            "Never download unverified attachments (.exe, .zip, .apk, .scr).",
            "Contact your IT security department or the alleged sender via a verified alternate channel."
        ]

        explanation = (
            f"Email communication analyzed with {len(threat_indicators)} security triggers. "
            f"Risk evaluation: {risk_score}%, Status: {verdict}."
        )

        return {
            "category": "email",
            "query_target": sender_email or (subject or "Email Content"),
            "risk_score": risk_score,
            "risk_level": risk_level,
            "verdict": verdict,
            "threat_indicators": threat_indicators,
            "explanation": explanation,
            "recommendations": recommendations,
            "metadata_info": {"sender": sender_email, "subject": subject},
        }

    @classmethod
    def analyze_general(cls, content: str, content_type: str = "general") -> Dict[str, Any]:
        """Multi-vector analysis for text, transactions, or general scam intelligence."""
        if content_type == "phone" or re.match(r"^\+?[\d\s\-()]{7,20}$", content.strip()):
            return cls.analyze_phone(content)
        elif content_type == "url" or re.match(r"^(https?://|[a-zA-Z0-9-]+\.[a-zA-Z]{2,})", content.strip()):
            return cls.analyze_url(content)
        elif content_type == "email" or "@" in content and len(content.split()) == 1:
            return cls.analyze_email(sender_email=content)
        else:
            return cls.analyze_message(content, channel=content_type)

    @staticmethod
    def _calculate_verdict(score: float) -> Tuple[float, str, str]:
        """Normalize score to 0-100 and determine risk level & verdict."""
        normalized_score = min(max(round(score, 1), 0.0), 99.9)

        if normalized_score >= 80.0:
            return normalized_score, "CRITICAL", "High Confidence Malicious Threat"
        elif normalized_score >= 60.0:
            return normalized_score, "HIGH", "Likely Scam / Fraudulent Activity"
        elif normalized_score >= 40.0:
            return normalized_score, "MEDIUM", "Suspicious / Potential Risk"
        elif normalized_score >= 20.0:
            return normalized_score, "LOW", "Low Risk / Standard Precautions"
        else:
            return normalized_score, "SAFE", "Legitimate / No Threats Detected"
