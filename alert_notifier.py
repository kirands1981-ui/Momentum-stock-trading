"""
Alert Notifier Module - Sends real-time alerts via multiple channels
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime
from typing import Dict, List, Optional
import threading
import requests
from pathlib import Path

logger = logging.getLogger(__name__)


class EmailNotifier:
    """Sends alerts via email"""

    def __init__(self, smtp_server: str = "smtp.gmail.com", smtp_port: int = 587,
                 sender_email: str = None, sender_password: str = None):
        """Initialize email notifier"""
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.enabled = bool(sender_email and sender_password)

    def send_alert(self, recipient_email: str, alert_data: Dict, 
                  chart_path: Optional[str] = None) -> bool:
        """
        Send alert email with optional chart attachment
        
        Parameters:
            recipient_email: Email to send to
            alert_data: Alert information dict
            chart_path: Path to chart PNG (optional)
        
        Returns:
            True if sent successfully
        """
        
        if not self.enabled:
            logger.debug("Email notifier not configured, skipping email alert")
            return False

        try:
            ticker = alert_data['ticker']
            buy_type = alert_data['buy_type']
            score = alert_data['score']
            details = alert_data['details']

            # Create message
            msg = MIMEMultipart('related')
            msg['Subject'] = f"🚀 MOMENTUM ALERT: {ticker} - {buy_type}"
            msg['From'] = self.sender_email
            msg['To'] = recipient_email

            # Create HTML body
            html = self._create_html_email(alert_data)

            # Attach HTML
            msg.attach(MIMEText(html, 'html'))

            # Attach chart if provided
            if chart_path and Path(chart_path).exists():
                try:
                    with open(chart_path, 'rb') as img_file:
                        img = MIMEImage(img_file.read(), name=Path(chart_path).name)
                        img.add_header('Content-ID', '<chart>')
                        img.add_header('Content-Disposition', 'inline', filename=Path(chart_path).name)
                        msg.attach(img)
                except Exception as e:
                    logger.error(f"Error attaching chart to email: {e}")

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)

            logger.info(f"Email alert sent to {recipient_email} for {ticker}")
            return True

        except Exception as e:
            logger.error(f"Error sending email alert: {e}")
            return False

    def _create_html_email(self, alert_data: Dict) -> str:
        """Create HTML email body"""
        
        ticker = alert_data['ticker']
        buy_type = alert_data['buy_type']
        score = alert_data['score']
        details = alert_data['details']

        buy_type_color = "#00AA00" if buy_type == "INSTITUTIONAL_BUY" else "#0099FF"
        buy_type_label = "🚀 INSTITUTIONAL BUY" if buy_type == "INSTITUTIONAL_BUY" else "📊 RETAIL BUY"

        html = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; background: #0a0a0a; color: #ffffff; }}
                    .container {{ max-width: 600px; margin: 20px auto; background: #1a1a1a; 
                               border-radius: 10px; overflow: hidden; border: 2px solid #333; }}
                    .header {{ background: {buy_type_color}; padding: 20px; text-align: center; }}
                    .header h1 {{ margin: 0; font-size: 28px; color: #000; }}
                    .ticker {{ font-size: 48px; font-weight: bold; }}
                    .content {{ padding: 30px; }}
                    .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; }}
                    .info-box {{ background: #0a0a0a; padding: 15px; border-radius: 8px; 
                               border-left: 4px solid {buy_type_color}; }}
                    .label {{ color: #999; font-size: 12px; text-transform: uppercase; }}
                    .value {{ font-size: 20px; font-weight: bold; color: {buy_type_color}; }}
                    .chart {{ text-align: center; margin: 30px 0; }}
                    .chart img {{ max-width: 100%; border-radius: 8px; }}
                    .footer {{ background: #0a0a0a; padding: 20px; text-align: center; 
                              font-size: 12px; color: #666; border-top: 1px solid #333; }}
                    .link-box {{ text-align: center; margin: 20px 0; }}
                    .link {{ display: inline-block; margin: 10px; padding: 12px 24px; 
                           background: {buy_type_color}; color: #000; text-decoration: none; 
                           border-radius: 5px; font-weight: bold; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div class="ticker">{ticker}</div>
                        <h1>{buy_type_label}</h1>
                    </div>
                    
                    <div class="content">
                        <div class="info-grid">
                            <div class="info-box">
                                <div class="label">Momentum Score</div>
                                <div class="value">{score:.1f}/100</div>
                            </div>
                            <div class="info-box">
                                <div class="label">Price Change</div>
                                <div class="value">+{details['price_increase_percent']:.2f}%</div>
                            </div>
                            <div class="info-box">
                                <div class="label">Current Price</div>
                                <div class="value">${details['current_price']:.2f}</div>
                            </div>
                            <div class="info-box">
                                <div class="label">Relative Volume</div>
                                <div class="value">{details['relative_volume']:.1f}x</div>
                            </div>
                        </div>
                        
                        <div class="chart">
                            <img src="cid:chart" alt="Momentum Chart" style="max-width: 100%; border-radius: 8px;">
                        </div>
                        
                        <div class="link-box">
                            <a href="https://www.webull.com/quote/{ticker}" class="link">
                                Open on WebUll Web
                            </a>
                            <a href="webull://quote/{ticker}" class="link">
                                Open in WebUll App
                            </a>
                        </div>
                        
                        <div style="background: #0a0a0a; padding: 15px; border-radius: 8px; 
                                  border-left: 4px solid #666;">
                            <strong>Pattern Type:</strong><br>
                            {"Silent Institutional Accumulation (No PR)" if buy_type == "INSTITUTIONAL_BUY" else "PR-Driven Retail Momentum"}
                        </div>
                    </div>
                    
                    <div class="footer">
                        <p>🔔 Momentum Stock Alert System | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ET</p>
                        <p style="font-size: 10px; color: #555;">
                            This is an automated alert. Not investment advice. Always do your own research.
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        return html


class WebhookNotifier:
    """Sends alerts via webhooks (Discord, Slack, Telegram)"""

    def __init__(self, webhook_url: str = None):
        """Initialize webhook notifier"""
        self.webhook_url = webhook_url
        self.enabled = bool(webhook_url)

    def send_alert(self, alert_data: Dict) -> bool:
        """Send alert via webhook"""
        
        if not self.enabled:
            logger.debug("Webhook notifier not configured")
            return False

        try:
            ticker = alert_data['ticker']
            buy_type = alert_data['buy_type']
            score = alert_data['score']
            details = alert_data['details']

            # Prepare message
            if 'discord' in self.webhook_url.lower():
                payload = self._create_discord_payload(alert_data)
            elif 'slack' in self.webhook_url.lower():
                payload = self._create_slack_payload(alert_data)
            else:
                payload = self._create_generic_payload(alert_data)

            # Send webhook
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()

            logger.info(f"Webhook alert sent for {ticker}")
            return True

        except Exception as e:
            logger.error(f"Error sending webhook alert: {e}")
            return False

    def _create_discord_payload(self, alert_data: Dict) -> Dict:
        """Create Discord webhook payload"""
        
        ticker = alert_data['ticker']
        buy_type = alert_data['buy_type']
        score = alert_data['score']
        details = alert_data['details']

        color = 65280 if buy_type == "INSTITUTIONAL_BUY" else 28927  # Green or Blue

        embed = {
            "title": f"🚀 MOMENTUM ALERT: {ticker}",
            "color": color,
            "fields": [
                {"name": "Buy Type", "value": buy_type, "inline": True},
                {"name": "Momentum Score", "value": f"{score:.1f}/100", "inline": True},
                {"name": "Price Change", "value": f"+{details['price_increase_percent']:.2f}%", "inline": True},
                {"name": "Relative Volume", "value": f"{details['relative_volume']:.1f}x", "inline": True},
                {"name": "Current Price", "value": f"${details['current_price']:.2f}", "inline": True},
                {"name": "Previous Close", "value": f"${details['previous_close']:.2f}", "inline": True},
            ],
            "timestamp": datetime.now().isoformat()
        }

        return {"embeds": [embed]}

    def _create_slack_payload(self, alert_data: Dict) -> Dict:
        """Create Slack webhook payload"""
        
        ticker = alert_data['ticker']
        buy_type = alert_data['buy_type']
        score = alert_data['score']
        details = alert_data['details']

        color = "good" if buy_type == "INSTITUTIONAL_BUY" else "warning"

        return {
            "attachments": [
                {
                    "fallback": f"Momentum alert for {ticker}",
                    "color": color,
                    "title": f"🚀 {ticker} - {buy_type}",
                    "fields": [
                        {"title": "Momentum Score", "value": f"{score:.1f}/100", "short": True},
                        {"title": "Price Change", "value": f"+{details['price_increase_percent']:.2f}%", "short": True},
                        {"title": "Relative Volume", "value": f"{details['relative_volume']:.1f}x", "short": True},
                        {"title": "Current Price", "value": f"${details['current_price']:.2f}", "short": True},
                    ],
                    "ts": int(datetime.now().timestamp())
                }
            ]
        }

    def _create_generic_payload(self, alert_data: Dict) -> Dict:
        """Create generic webhook payload"""
        
        return {
            "timestamp": datetime.now().isoformat(),
            "alert_data": alert_data
        }


class AlertNotifier:
    """Manages all alert notifications"""

    def __init__(self, email_config: Dict = None, webhook_url: str = None):
        """Initialize alert notifier"""
        self.email_notifier = None
        self.webhook_notifier = None

        if email_config and email_config.get('enabled'):
            self.email_notifier = EmailNotifier(
                smtp_server=email_config.get('smtp_server', 'smtp.gmail.com'),
                smtp_port=email_config.get('smtp_port', 587),
                sender_email=email_config.get('sender_email'),
                sender_password=email_config.get('sender_password')
            )

        if webhook_url:
            self.webhook_notifier = WebhookNotifier(webhook_url)

    def send_alert(self, alert_data: Dict, recipient_email: str = None, 
                  chart_path: Optional[str] = None) -> Dict[str, bool]:
        """
        Send alert via all configured channels
        
        Parameters:
            alert_data: Alert information
            recipient_email: Email address (for email channel)
            chart_path: Path to chart image
        
        Returns:
            Dict with delivery status for each channel
        """
        
        results = {
            'email': False,
            'webhook': False,
            'console': False
        }

        # Send console alert (always)
        results['console'] = True
        logger.info(f"🚀 ALERT: {alert_data['ticker']} - {alert_data['buy_type']}")

        # Send email
        if self.email_notifier and recipient_email:
            results['email'] = self.email_notifier.send_alert(
                recipient_email, alert_data, chart_path
            )

        # Send webhook
        if self.webhook_notifier:
            results['webhook'] = self.webhook_notifier.send_alert(alert_data)

        return results

    def send_alert_async(self, alert_data: Dict, recipient_email: str = None,
                        chart_path: Optional[str] = None):
        """Send alert asynchronously (non-blocking)"""
        
        thread = threading.Thread(
            target=self.send_alert,
            args=(alert_data, recipient_email, chart_path),
            daemon=True
        )
        thread.start()


class SystemNotifier:
    """System-level notifications (desktop, SMS, etc)"""

    @staticmethod
    def notify_desktop(title: str, message: str) -> bool:
        """Send desktop notification (macOS/Linux/Windows)"""
        try:
            import subprocess
            import sys

            if sys.platform == 'darwin':  # macOS
                script = f'display notification "{message}" with title "{title}"'
                subprocess.run(['osascript', '-e', script], check=True)
            elif sys.platform.startswith('linux'):  # Linux
                subprocess.run(['notify-send', title, message], check=True)
            elif sys.platform == 'win32':  # Windows
                import win10toast
                notifier = win10toast.ToastNotifier()
                notifier.show_toast(title, message, duration=10)

            logger.info(f"Desktop notification sent: {title}")
            return True

        except Exception as e:
            logger.debug(f"Desktop notification failed: {e}")
            return False

    @staticmethod
    def notify_sms(phone_number: str, message: str, twilio_sid: str = None,
                  twilio_token: str = None, twilio_phone: str = None) -> bool:
        """Send SMS notification via Twilio"""
        
        if not all([twilio_sid, twilio_token, twilio_phone]):
            logger.debug("Twilio not configured for SMS")
            return False

        try:
            from twilio.rest import Client
            
            client = Client(twilio_sid, twilio_token)
            message_obj = client.messages.create(
                body=message,
                from_=twilio_phone,
                to=phone_number
            )

            logger.info(f"SMS sent to {phone_number}: {message_obj.sid}")
            return True

        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            return False
