import logging
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import settings

logger = logging.getLogger("email_service")

class EmailService:
    @staticmethod
    async def send_email(to_email: str, subject: str, html_content: str):
        # Build MIME message
        message = MIMEMultipart("alternative")
        message["From"] = settings.SMTP_SENDER
        message["To"] = to_email
        message["Subject"] = subject
        
        message.attach(MIMEText(html_content, "html"))
        
        # Try sending via aiosmtplib
        try:
            if settings.SMTP_HOST:
                smtp_kwargs = {
                    "hostname": settings.SMTP_HOST,
                    "port": settings.SMTP_PORT,
                    "use_tls": settings.SMTP_USE_TLS
                }
                
                async with aiosmtplib.SMTP(**smtp_kwargs) as smtp:
                    if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                        await smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                    await smtp.send_message(message)
                logger.info(f"Email sent successfully to {to_email} with subject: '{subject}'")
                return True
        except Exception as e:
            logger.warning(f"SMTP failed to send email to {to_email}: {e}")
        
        # Fallback logger for development environment
        try:
            print("\n" + "="*80)
            print(f"[MOCK EMAIL] SENDING EMAIL TO: {to_email}")
            print(f"Subject: {subject}")
            print(f"Body:\n{html_content}")
            print("="*80 + "\n")
        except UnicodeEncodeError:
            safe_subject = subject.encode('ascii', 'replace').decode('ascii')
            safe_body = html_content.encode('ascii', 'replace').decode('ascii')
            print("\n" + "="*80)
            print(f"[MOCK EMAIL] SENDING EMAIL TO: {to_email} (fallback encoding)")
            print(f"Subject: {safe_subject}")
            print(f"Body:\n{safe_body}")
            print("="*80 + "\n")
        return False

    @classmethod
    async def sendInvitationEmail(cls, to_email: str, inviter_name: str, workspace_name: str, invite_url: str):
        subject = f"You've been invited to join {workspace_name} on EmailVerif"
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <h2>You've been invited!</h2>
                <p>Hello,</p>
                <p><strong>{inviter_name}</strong> has invited you to join their workspace <strong>{workspace_name}</strong> on EmailVerif.</p>
                <p>To accept the invitation and create your account, click the button below:</p>
                <p>
                    <a href="{invite_url}" style="display: inline-block; padding: 10px 20px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px;">Accept Invitation</a>
                </p>
                <p>Or copy and paste this link into your browser:</p>
                <p><a href="{invite_url}">{invite_url}</a></p>
                <p>This invitation will expire in 7 days.</p>
                <p>Best regards,<br>The EmailVerif Team</p>
            </body>
        </html>
        """
        return await cls.send_email(to_email, subject, html_content)

    @classmethod
    async def sendWelcomeEmail(cls, to_email: str):
        subject = "Welcome to EmailVerif!"
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                    <h2 style="color: #6366f1;">Welcome to EmailVerif! 🚀</h2>
                    <p>Thank you for signing up for our Email Verification SaaS platform. Your account is now active, and you have been credited with <strong>100 free verification credits</strong>.</p>
                    <p>With EmailVerif, you can:</p>
                    <ul>
                        <li>Perform real-time SMTP checks</li>
                        <li>Detect disposable and role accounts</li>
                        <li>Upload bulk lists (CSV) to clean your databases</li>
                        <li>Integrate verification into your apps via our Developer API</li>
                    </ul>
                    <p>If you have any questions, feel free to contact our support team.</p>
                    <br>
                    <p>Best regards,<br>The EmailVerif Team</p>
                </div>
            </body>
        </html>
        """
        return await cls.send_email(to_email, subject, html_content)

    @classmethod
    async def sendPasswordResetEmail(cls, to_email: str, reset_url: str):
        subject = "Reset Your Password - EmailVerif"
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                    <h2 style="color: #6366f1;">Password Reset Request</h2>
                    <p>We received a request to reset your password for your EmailVerif account. Click the button below to set a new password:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_url}" style="background-color: #6366f1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">Reset Password</a>
                    </div>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #6366f1;">{reset_url}</p>
                    <p><strong>Note:</strong> This link is valid for 30 minutes. If you did not make this request, you can safely ignore this email.</p>
                    <br>
                    <p>Best regards,<br>The EmailVerif Team</p>
                </div>
            </body>
        </html>
        """
        return await cls.send_email(to_email, subject, html_content)

    @classmethod
    async def sendVerificationCompletedEmail(cls, to_email: str, job_id: str, total_emails: int, valid_emails: int):
        invalid_emails = total_emails - valid_emails
        accuracy = round((valid_emails / total_emails) * 100, 2) if total_emails > 0 else 0
        subject = f"Verification Job Complete - Job #{job_id[:8]}"
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                    <h2 style="color: #6366f1;">Job Verification Completed! 🎉</h2>
                    <p>Your bulk email verification job has successfully finished processing. Here is the summary of the results:</p>
                    
                    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                        <thead>
                            <tr style="background-color: #f3f4f6; text-align: left;">
                                <th style="padding: 10px; border: 1px solid #e5e7eb;">Metric</th>
                                <th style="padding: 10px; border: 1px solid #e5e7eb;">Value</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td style="padding: 10px; border: 1px solid #e5e7eb;"><strong>Job ID</strong></td>
                                <td style="padding: 10px; border: 1px solid #e5e7eb; font-family: monospace;">{job_id}</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px; border: 1px solid #e5e7eb;"><strong>Total Verified</strong></td>
                                <td style="padding: 10px; border: 1px solid #e5e7eb;">{total_emails:,}</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px; border: 1px solid #e5e7eb;"><strong>Valid Emails</strong></td>
                                <td style="padding: 10px; border: 1px solid #e5e7eb; color: #10b981; font-weight: bold;">{valid_emails:,}</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px; border: 1px solid #e5e7eb;"><strong>Invalid/Undeliverable</strong></td>
                                <td style="padding: 10px; border: 1px solid #e5e7eb; color: #ef4444;">{invalid_emails:,}</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px; border: 1px solid #e5e7eb;"><strong>Deliverability Score</strong></td>
                                <td style="padding: 10px; border: 1px solid #e5e7eb; font-weight: bold;">{accuracy}%</td>
                            </tr>
                        </tbody>
                    </table>
                    
                    <p>You can view and download the complete cleaned results directly from your dashboard.</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="http://localhost:5173/dashboard" style="background-color: #6366f1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">Go to Dashboard</a>
                    </div>
                    <br>
                    <p>Best regards,<br>The EmailVerif Team</p>
                </div>
            </body>
        </html>
        """
        return await cls.send_email(to_email, subject, html_content)

    @classmethod
    async def sendPasswordResetEmail(cls, to_email: str, reset_link: str):
        subject = "Reset your EmailVerif password"
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; text-align: center;">
                    <h2 style="color: #1e293b; margin-top: 0;">Password Reset Request</h2>
                    <p>We received a request to reset your password for your EmailVerif account.</p>
                    <p>Click the button below to choose a new password:</p>
                    
                    <div style="margin: 30px 0;">
                        <a href="{reset_link}" style="background-color: #6366f1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">Reset Password</a>
                    </div>
                    
                    <p style="font-size: 0.9em; color: #64748b;">If you didn't request this, you can safely ignore this email. Your password will not change.</p>
                    <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;">
                    <p style="font-size: 0.8em; color: #94a3b8; word-break: break-all;">
                        If the button doesn't work, copy and paste this link into your browser:<br>
                        <a href="{reset_link}" style="color: #6366f1;">{reset_link}</a>
                    </p>
                </div>
            </body>
        </html>
        """
        return await cls.send_email(to_email, subject, html_content)
