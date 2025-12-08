from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from core.models import PasswordResetToken
import uuid
import logging

logger = logging.getLogger(__name__)


class PasswordResetRequestView(APIView):
    """
    Request password reset - sends email with reset link
    No authentication required
    """
    permission_classes = []

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        
        if not email:
            return Response(
                {"error": "Email is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Check if user exists
            user = User.objects.filter(email=email).first()
            
            if user:
                # Delete any existing unused tokens for this user
                PasswordResetToken.objects.filter(
                    user=user,
                    is_used=False
                ).delete()
                
                # Create new reset token
                reset_token = PasswordResetToken.objects.create(
                    user=user,
                    token=str(uuid.uuid4())
                )
                
                # Build reset link
                frontend_url = getattr(settings, 'FRONTEND_URL', 'http://127.0.0.1:3000')
                reset_link = f"{frontend_url}/reset-password?token={reset_token.token}"
                
                # Send email
                try:
                    subject = "Password Reset Request - Software Design Sensei"
                    
                    # Plain text message
                    message = f"""
Hi {user.username},

You requested to reset your password for Software Design Sensei.

Click the link below to reset your password:
{reset_link}

This link will expire in 1 hour.

If you didn't request this, please ignore this email.

Best regards,
Software Design Sensei Team
"""
                    
                    # HTML message (optional, better looking)
                    html_message = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #3980D0;">Password Reset Request</h2>
        <p>Hi <strong>{user.username}</strong>,</p>
        <p>You requested to reset your password for Software Design Sensei.</p>
        <p>Click the button below to reset your password:</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_link}" 
               style="background-color: #3980D0; color: white; padding: 12px 30px; 
                      text-decoration: none; border-radius: 5px; display: inline-block;">
                Reset Password
            </a>
        </div>
        <p style="color: #666; font-size: 14px;">
            Or copy and paste this link into your browser:<br>
            <a href="{reset_link}" style="color: #3980D0;">{reset_link}</a>
        </p>
        <p style="color: #666; font-size: 14px;">
            This link will expire in <strong>1 hour</strong>.
        </p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
        <p style="color: #999; font-size: 12px;">
            If you didn't request this, please ignore this email. Your password will remain unchanged.
        </p>
        <p style="color: #999; font-size: 12px;">
            Best regards,<br>
            Software Design Sensei Team
        </p>
    </div>
</body>
</html>
"""
                    
                    send_mail(
                        subject=subject,
                        message=message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[email],
                        html_message=html_message,
                        fail_silently=False,
                    )
                    
                    logger.info(f"Password reset email sent to {email}")
                    
                except Exception as e:
                    logger.error(f"Failed to send password reset email to {email}: {e}")
                    return Response(
                        {"error": "Failed to send email. Please try again later."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            
            # Always return success message (don't reveal if email exists)
            return Response({
                "message": "If an account exists with this email, you will receive a password reset link shortly."
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in password reset request: {e}")
            return Response(
                {"error": "An error occurred. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PasswordResetValidateView(APIView):
    """
    Validate reset token - check if token is valid
    No authentication required
    """
    permission_classes = []

    def get(self, request):
        token = request.query_params.get('token', '').strip()
        
        if not token:
            return Response(
                {"valid": False, "error": "Token is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            reset_token = PasswordResetToken.objects.filter(token=token).first()
            
            if not reset_token:
                return Response({
                    "valid": False,
                    "error": "Invalid reset link"
                }, status=status.HTTP_200_OK)
            
            if reset_token.is_used:
                return Response({
                    "valid": False,
                    "error": "This reset link has already been used"
                }, status=status.HTTP_200_OK)
            
            if timezone.now() > reset_token.expires_at:
                return Response({
                    "valid": False,
                    "error": "This reset link has expired"
                }, status=status.HTTP_200_OK)
            
            # Token is valid
            return Response({
                "valid": True,
                "email": reset_token.user.email,
                "username": reset_token.user.username
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error validating reset token: {e}")
            return Response(
                {"valid": False, "error": "An error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PasswordResetConfirmView(APIView):
    """
    Confirm password reset - actually change the password
    No authentication required
    """
    permission_classes = []

    def post(self, request):
        token = request.data.get('token', '').strip()
        new_password = request.data.get('new_password', '')
        
        if not token or not new_password:
            return Response(
                {"error": "Token and new password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate password strength
        if len(new_password) < 8:
            return Response(
                {"error": "Password must be at least 8 characters long"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get and validate token
            reset_token = PasswordResetToken.objects.filter(token=token).first()
            
            if not reset_token:
                return Response(
                    {"error": "Invalid reset link"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if reset_token.is_used:
                return Response(
                    {"error": "This reset link has already been used"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if timezone.now() > reset_token.expires_at:
                return Response(
                    {"error": "This reset link has expired. Please request a new one."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update user password
            user = reset_token.user
            user.password = make_password(new_password)
            user.save()
            
            # Mark token as used
            reset_token.is_used = True
            reset_token.save()
            
            # Send confirmation email
            try:
                subject = "Password Changed - Software Design Sensei"
                message = f"""
Hi {user.username},

Your password for Software Design Sensei has been successfully changed.

If you didn't make this change, please contact support immediately.

Best regards,
Software Design Sensei Team
"""
                html_message = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #3980D0;">Password Changed Successfully</h2>
        <p>Hi <strong>{user.username}</strong>,</p>
        <p>Your password for Software Design Sensei has been successfully changed.</p>
        <p style="color: #666;">
            If you didn't make this change, please contact support immediately.
        </p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
        <p style="color: #999; font-size: 12px;">
            Best regards,<br>
            Software Design Sensei Team
        </p>
    </div>
</body>
</html>
"""
                
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    html_message=html_message,
                    fail_silently=True,  # Don't fail if confirmation email fails
                )
            except Exception as e:
                logger.error(f"Failed to send password change confirmation email: {e}")
            
            logger.info(f"Password successfully reset for user {user.username}")
            
            return Response({
                "message": "Password successfully reset! You can now login with your new password.",
                "username": user.username
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error resetting password: {e}")
            return Response(
                {"error": "An error occurred while resetting password. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
