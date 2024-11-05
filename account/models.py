from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser

from payment.models import Order, SubscriptionItem
# Create your models here.
from talent_bridged.models import AbstractBaseModel
from api.models import APIKey
from django.utils import timezone  # Add this line
from datetime import timedelta  # Import timedelta
import logging
logger = logging.getLogger('django')

class MyAccountManager(BaseUserManager):
    def create_user(self, email, username, password):
        if not email:
            raise ValueError("User must have a valid email ")
        if not username:
            raise ValueError("User must have a valid username")
        if not password:
            raise ValueError("Enter a correct password")

        # Create the user
        user = self.model(
            email=self.normalize_email(email),
            username=username,
        )
        user.set_password(password)
        user.save(using=self.db)

        # Link free subscriptions to the user
        self.link_free_subscriptions(user)

        return user

    def create_superuser(self, email, username, password):
        # Create the superuser
        user = self.create_user(
            email=self.normalize_email(email),
            password=password,
            username=username,
        )

        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save(using=self._db)

        return user

    def link_free_subscriptions(self, account):
        """
        Link all free subscriptions with a unique service_name to the account
        via the AccountOrders object.
        """
        logger.info(f"Starting link_free_subscriptions for account: {account.email}")
        
        try:
            # Fetch all free SubscriptionItem objects, ensuring uniqueness by service_name
            free_subscriptions = SubscriptionItem.objects.filter(subscription_type='Free').distinct('service_name')
            logger.info(f"Fetched free subscriptions for account {account.email}: {[sub.service_name for sub in free_subscriptions]}")

            # Iterate over each free subscription and create an AccountOrders entry
            for subscription in free_subscriptions:
                logger.info(f"Processing subscription {subscription.service_name} for account {account.email}")

                # Check if the account already has a subscription for this service_name
                if not AccountOrders.objects.filter(
                        account=account, 
                        order__subscription_item__service_name=subscription.service_name,
                        is_active=True,
                    ).exists():
                    logger.info(f"Subscription {subscription.service_name} does not exist for account {account.email}. Creating a new subscription.")
                    
                    start_date = timezone.now()
                    
                    # Create the Order for the free subscription
                    order = Order.objects.create(
                        subscription_item=subscription,
                        order_type='new',
                        completed=True  # Mark it as completed since it's a free subscription
                    )
                    logger.info(f"Order created for subscription {subscription.service_name} for account {account.email}: Order ID {order.id}")

                    # Create the AccountOrders for the free subscription
                    account_order_obj = AccountOrders.objects.create(
                        account=account,
                        order=order,
                        start_date=start_date,
                        end_date=start_date + timedelta(days=30),  # Set end_date to 30 days from now
                        is_active=True,
                    )
                    logger.info(f"Account order created for subscription {subscription.service_name} for account {account.email}: AccountOrder ID {account_order_obj.id}")

                    # Create AccountOrdersHistory for tracking the subscription creation
                    AccountOrdersHistory.objects.create(
                        account_order=account_order_obj,  # Ensure this matches your model's field name
                        history_date=start_date,
                        change_type='started',
                        details="First plan after account creation",
                    )
                    logger.info(f"AccountOrdersHistory created for account {account.email}: AccountOrder ID {account_order_obj.id}")
                else:
                    logger.info(f"Subscription {subscription.service_name} already exists for account {account.email}")
        except Exception as e:
            logger.error(f"Error occurred in link_free_subscriptions for account {account.email}: {str(e)}", exc_info=True)


class Country(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=3, unique=True)  # ISO Alpha-2 code, e.g., "IN" for India

    def __str__(self):
        return self.name
        
class Address(AbstractBaseModel):
    full_name = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    address1 = models.CharField(max_length=255)
    address2 = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=255, null=True, blank=True)
    zipcode = models.CharField(max_length=255, null=True, blank=True)
    country = models.ForeignKey(Country, on_delete=models.PROTECT)

    class Meta:
        verbose_name_plural = "Address"

    def __str__(self):
        return f'Address - {str(self.id)}'

        
class Account(AbstractBaseUser):
    email = models.EmailField(verbose_name="email", max_length=60, unique=True)
    username = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=30, null=True, verbose_name="name")
    date_joined = models.DateTimeField(verbose_name='date joined', auto_now_add=True)
    last_login = models.DateTimeField(verbose_name='last login', auto_now=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True, default='profile_photos/default_profile_photo.png')

    # Explicit intermediate model to track extra information
    orders = models.ManyToManyField(Order, through='AccountOrders')
    address = models.OneToOneField(Address, related_name='account_address', on_delete=models.CASCADE, null=True, blank=True)
    api_key = models.OneToOneField(APIKey, on_delete=models.SET_NULL, null=True, blank=True, related_name='api_account')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = MyAccountManager()

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True


class AccountOrders(AbstractBaseModel):
    SUBSCRIPTION_INTERVAL_TYPE_CHOICES = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]

    # Define corresponding days for each cycle type
    SUBSCRIPTION_CYCLE_LENGTH_CHOICES = [
        (30, 'Monthly (30 days)'),
        (365, 'Yearly (365 days)'),
    ]


    STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('initiated_expired', 'Initiated Expired'), #This Account Order will expire if its in initiated or pending status by fetch_paypal_transactions in every 19 minutes
        ('initiated_expired_refunded', 'Initiated Expired Refunded'),
        ('initiated_expired_due_to_new_active_order', 'Initiated Expired Due To New Active Order'),
        ('initiated_expired_refunded_due_to_new_active_order', 'Initiated Expired Refunded Due To New Active Order'),
        ('pending', 'Pending'),
        ('pending_expired', 'Pending Expired'),
        ('pending_expired_refunded', 'Pending Expired Refunded'),
        ('failed', 'Failed'),
        ('successful', 'Successful'),
    ]
    
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    account = models.ForeignKey('Account', on_delete=models.CASCADE)
    # Link directly to Order instead of AccountOrder
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    
    # Removed subscription_item since it’s already in the Order
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    current_end_date = models.DateTimeField(null=True, blank=True)
    pre_end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    subscription_cycle_type = models.CharField(max_length=50, choices=SUBSCRIPTION_INTERVAL_TYPE_CHOICES, default='monthly')
    subscription_cycle_length = models.IntegerField(
        choices=SUBSCRIPTION_CYCLE_LENGTH_CHOICES,
        default=30,  # Default to 'Monthly (30 days)'
        help_text="Number of days corresponding to the subscription cycle"
    )
    is_auto_renew = models.BooleanField(default=True)
    rolling_proxy_aggregator_count_usage_from_renewal = models.IntegerField(default=0)  # Get saved usage from last plan on renewal payment
    rolling_proxy_aggregator_gb_usage_from_renewal = models.FloatField(default=0) # Get saved usage from last plan on renewal payment


    def __str__(self):
        return f"{self.order} - {self.order.subscription_item.service_name}"


class AccountOrdersHistory(AbstractBaseModel):

    PLAN_STATUS_CHOICES = [
        ('started', 'Started'),
        ('stopped', 'Stopped'),
        ('pre_stopped', 'Pre Stopped'),
        ('expired', 'Expired'),
        ('renewed', 'Renewed'),
        ('degraded', 'Degraded'),
        ('upgraded', 'Upgraded'),
        ('auto_renew_cancelled', 'Auto Renew Cancelled')
    ]

    account_order = models.ForeignKey(AccountOrders, on_delete=models.CASCADE, related_name='account_order_history')
    change_type = models.CharField(max_length=50, choices=PLAN_STATUS_CHOICES)
    history_date = models.DateTimeField(auto_now_add=True)
    details = models.TextField(null=True, blank=True)  # Optional field to store any additional information about the change
    proxy_aggregator_count_usage = models.IntegerField(null=True, blank=True) # Set to None when the plan is renewed and yet not started
    proxy_aggregator_gb_usage = models.FloatField(null=True, blank=True) # Set to None when the plan is renewed and yet not started

    def __str__(self):
        return f"{self.account_order_subscription.account.email} - {self.change_type} on {self.change_date}"

