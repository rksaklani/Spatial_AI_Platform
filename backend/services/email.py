import structlog

logger = structlog.get_logger(__name__)


class EmailService:
    """Service to handle sending emails depending on environment configurations."""
    
    @staticmethod
    async def send_welcome_email(email: str, name: str) -> bool:
        """Sends a welcome email to the newly registered user."""
        try:
            # TODO: Integrate Amazon SES/SendGrid in the future.
            # For Phase 2 we are mocking it via strict json structured logging
            logger.info(
                "email_sent",
                subject="Welcome to Ultimate Spatial AI Platform",
                recipient=email,
                name=name,
                template="welcome"
            )
            return True
            
        except Exception as e:
            logger.error("failed_to_send_email", recipient=email, exc_info=e)
            return False
